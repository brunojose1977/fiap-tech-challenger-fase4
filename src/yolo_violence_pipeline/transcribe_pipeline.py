"""Pipeline aws-transcribe-audio-from-video-conversations."""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

from yolo_violence_pipeline.openai_risk import analyze_transcript_risk
from yolo_violence_pipeline.risk_pdf import build_risk_assessment_pdf
from yolo_violence_pipeline.s3_io import download_file, s3_client, upload_file
from yolo_violence_pipeline.transcribe_config import TranscribePipelineConfig

logger = logging.getLogger(__name__)

MEDIA_EXTENSIONS = {
    ".mp3",
    ".mp4",
    ".wav",
    ".flac",
    ".ogg",
    ".amr",
    ".webm",
    ".m4a",
    ".mov",
    ".mkv",
    ".mpeg",
    ".mpg",
}

TRANSCRIBE_FORMAT_BY_EXT = {
    ".mp3": "mp3",
    ".mp4": "mp4",
    ".wav": "wav",
    ".flac": "flac",
    ".ogg": "ogg",
    ".amr": "amr",
    ".webm": "webm",
    ".m4a": "mp4",
    ".mov": "mp4",
    ".mkv": "mp4",
    ".mpeg": "mp4",
    ".mpg": "mp4",
}


def _sanitize_job_name(key: str) -> str:
    base = re.sub(r"[^0-9A-Za-z._-]", "-", Path(key).name)[:180]
    return f"transcribe-{base}-{uuid.uuid4().hex[:8]}"


def _object_basename(key: str) -> str:
    return Path(key).name


def _transcribed_text_key(cfg: TranscribePipelineConfig, basename: str) -> str:
    return f"{cfg.transcribed_text_prefix}{basename}.txt"


def _risk_pdf_key(cfg: TranscribePipelineConfig, basename: str) -> str:
    return f"{cfg.risk_pdf_prefix}{basename}.pdf"


def list_media_keys(client, bucket: str) -> list[str]:
    """Lista chaves de vídeo/áudio no bucket de entrada."""
    keys: list[str] = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue
            if Path(key).suffix.lower() in MEDIA_EXTENSIONS:
                keys.append(key)
    return sorted(keys)


def _object_exists(client, bucket: str, key: str) -> bool:
    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
            return False
        raise


def _extract_transcript_text(transcript_payload: dict[str, Any]) -> str:
    transcripts = transcript_payload.get("results", {}).get("transcripts", [])
    if transcripts:
        return transcripts[0].get("transcript", "").strip()
    return json.dumps(transcript_payload, ensure_ascii=False, indent=2)


def _wait_transcription_job(transcribe_client, job_name: str, poll_seconds: int = 15) -> str:
    while True:
        resp = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        status = resp["TranscriptionJob"]["TranscriptionJobStatus"]
        if status == "COMPLETED":
            return resp["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
        if status == "FAILED":
            reason = resp["TranscriptionJob"].get("FailureReason", "unknown")
            msg = f"TranscriptionJob {job_name} falhou: {reason}"
            raise RuntimeError(msg)
        logger.info("Aguardando Transcribe (%s): %s", job_name, status)
        time.sleep(poll_seconds)


def _download_transcript_json(transcript_uri: str) -> dict[str, Any]:
    parsed = urlparse(transcript_uri)
    if parsed.scheme == "s3":
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        s3 = boto3.client("s3")
        local = Path("/tmp") / f"transcript-{uuid.uuid4().hex}.json"
        download_file(s3, bucket, key, local)
        return json.loads(local.read_text(encoding="utf-8"))

    import urllib.request

    with urllib.request.urlopen(transcript_uri, timeout=120) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def transcribe_s3_object(
    *,
    cfg: TranscribePipelineConfig,
    s3,
    transcribe_client,
    input_key: str,
) -> str:
    """Executa Amazon Transcribe para um objeto e retorna o texto."""
    media_format = TRANSCRIBE_FORMAT_BY_EXT.get(Path(input_key).suffix.lower())
    if not media_format:
        msg = f"Formato não suportado para Transcribe: {input_key}"
        raise ValueError(msg)

    job_name = _sanitize_job_name(input_key)
    media_uri = f"s3://{cfg.s3_input_bucket}/{input_key}"
    raw_output_key = f"_transcribe-jobs/{job_name}.json"

    logger.info("Iniciando Transcribe job %s para %s", job_name, media_uri)
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        LanguageCode=cfg.transcribe_language_code,
        MediaFormat=media_format,
        Media={"MediaFileUri": media_uri},
        OutputBucketName=cfg.s3_output_bucket,
        OutputKey=raw_output_key,
    )

    transcript_uri = _wait_transcription_job(transcribe_client, job_name)
    payload = _download_transcript_json(transcript_uri)
    return _extract_transcript_text(payload)


def process_media_object(
    *,
    cfg: TranscribePipelineConfig,
    input_key: str,
) -> dict[str, Any]:
    """Transcreve, analisa com ChatGPT e grava TXT + PDF no bucket de saída."""
    s3 = s3_client(cfg.aws_region)
    transcribe_client = boto3.client("transcribe", region_name=cfg.aws_region)
    basename = _object_basename(input_key)
    text_key = _transcribed_text_key(cfg, basename)
    pdf_key = _risk_pdf_key(cfg, basename)

    if cfg.skip_existing and _object_exists(s3, cfg.s3_output_bucket, text_key):
        if _object_exists(s3, cfg.s3_output_bucket, pdf_key):
            logger.info("Saídas já existem para %s; pulando.", basename)
            return {"source_key": input_key, "skipped": True}

    work = Path(cfg.work_dir)
    work.mkdir(parents=True, exist_ok=True)

    transcript_text = transcribe_s3_object(
        cfg=cfg,
        s3=s3,
        transcribe_client=transcribe_client,
        input_key=input_key,
    )

    local_txt = work / text_key.replace("/", "_")
    local_txt.write_text(transcript_text, encoding="utf-8")
    upload_file(s3, local_txt, cfg.s3_output_bucket, text_key)

    analysis = analyze_transcript_risk(
        api_key=cfg.openai_api_key,
        model=cfg.openai_model,
        source_filename=basename,
        transcript_text=transcript_text,
    )

    local_pdf = work / pdf_key.replace("/", "_")
    build_risk_assessment_pdf(
        output_path=local_pdf,
        source_filename=basename,
        model_name=cfg.openai_model,
        transcript_excerpt=transcript_text,
        analysis=analysis,
    )
    upload_file(s3, local_pdf, cfg.s3_output_bucket, pdf_key)

    return {
        "source_key": input_key,
        "transcribed_text_key": text_key,
        "risk_pdf_key": pdf_key,
        "risk_level": analysis.get("nivel_risco"),
        "skipped": False,
    }


def run_transcribe_pipeline(cfg: TranscribePipelineConfig) -> dict[str, Any]:
    """Processa todos os vídeos/áudios do bucket de entrada."""
    s3 = s3_client(cfg.aws_region)
    keys = list_media_keys(s3, cfg.s3_input_bucket)
    if not keys:
        logger.warning(
            "Nenhum arquivo de mídia encontrado em s3://%s/", cfg.s3_input_bucket
        )
        return {"processed": [], "count": 0}

    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for key in keys:
        try:
            results.append(process_media_object(cfg=cfg, input_key=key))
        except Exception as exc:  # noqa: BLE001 — registrar e continuar demais arquivos
            logger.exception("Falha ao processar %s", key)
            errors.append({"source_key": key, "error": str(exc)})

    return {"processed": results, "errors": errors, "count": len(results)}

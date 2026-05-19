"""Configuração do pipeline Amazon Transcribe + análise de risco (OpenAI)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from yolo_violence_pipeline.config import _require


@dataclass(frozen=True)
class TranscribePipelineConfig:
    """Parâmetros do fluxo aws-transcribe-audio-from-video-conversations."""

    aws_region: str
    s3_input_bucket: str
    s3_output_bucket: str
    work_dir: str
    transcribe_language_code: str
    openai_model: str
    openai_api_key: str
    transcribed_text_prefix: str
    risk_pdf_prefix: str
    skip_existing: bool

    @classmethod
    def from_environ(cls) -> TranscribePipelineConfig:
        return cls(
            aws_region=_require("AWS_REGION"),
            s3_input_bucket=_require("TRANSCRIBE_S3_INPUT_BUCKET"),
            s3_output_bucket=_require("TRANSCRIBE_S3_OUTPUT_BUCKET"),
            work_dir=os.environ.get("WORK_DIR", "/tmp/transcribe-work").strip(),
            transcribe_language_code=os.environ.get("TRANSCRIBE_LANGUAGE_CODE", "pt-BR").strip(),
            openai_model=os.environ.get("OPENAI_MODEL", "gpt-5.4").strip(),
            openai_api_key=_require("OPENAI_API_KEY"),
            transcribed_text_prefix=os.environ.get(
                "TRANSCRIBED_TEXT_PREFIX", "transcribed-text-"
            ).strip(),
            risk_pdf_prefix=os.environ.get(
                "RISK_PDF_PREFIX", "ChatGPT-5.4-avaliacao-conteudo-"
            ).strip(),
            skip_existing=os.environ.get("SKIP_EXISTING_OUTPUTS", "true").lower()
            in ("1", "true", "yes"),
        )

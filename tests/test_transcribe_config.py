"""Testes do fluxo Amazon Transcribe + OpenAI."""

from __future__ import annotations

import pytest

from yolo_violence_pipeline.transcribe_config import TranscribePipelineConfig
from yolo_violence_pipeline.transcribe_pipeline import (
    _risk_pdf_key,
    _transcribed_text_key,
)


def test_transcribe_from_environ_missing_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("TRANSCRIBE_S3_INPUT_BUCKET", "in")
    monkeypatch.setenv("TRANSCRIBE_S3_OUTPUT_BUCKET", "out")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        TranscribePipelineConfig.from_environ()


def test_transcribe_from_environ_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv(
        "TRANSCRIBE_S3_INPUT_BUCKET",
        "transcribe-violence-input-fiap-posttech-iadevs-tcfase04",
    )
    monkeypatch.setenv(
        "TRANSCRIBE_S3_OUTPUT_BUCKET",
        "transcribe-violence-output-fiap-posttech-iadevs-tcfase0",
    )
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    cfg = TranscribePipelineConfig.from_environ()
    assert cfg.openai_model == "gpt-5.4"
    assert cfg.transcribed_text_prefix == "transcribed-text-"


def test_output_key_prefixes() -> None:
    cfg = TranscribePipelineConfig(
        aws_region="us-east-1",
        s3_input_bucket="in",
        s3_output_bucket="out",
        work_dir="/tmp",
        transcribe_language_code="pt-BR",
        openai_model="gpt-5.4",
        openai_api_key="x",
        transcribed_text_prefix="transcribed-text-",
        risk_pdf_prefix="ChatGPT-5.4-avaliacao-conteudo-",
        skip_existing=True,
    )
    assert _transcribed_text_key(cfg, "video.mp4") == "transcribed-text-video.mp4.txt"
    assert _risk_pdf_key(cfg, "video.mp4") == "ChatGPT-5.4-avaliacao-conteudo-video.mp4.pdf"

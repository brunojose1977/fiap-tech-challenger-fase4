"""Testes de configuração."""

from __future__ import annotations

import pytest

from yolo_violence_pipeline.config import PipelineConfig


def test_from_environ_missing_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("S3_INPUT_BUCKET", raising=False)
    with pytest.raises(ValueError, match="AWS_REGION"):
        PipelineConfig.from_environ()


def test_from_environ_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("S3_INPUT_BUCKET", "in")
    monkeypatch.setenv("S3_PREDICT_BUCKET", "pred")
    monkeypatch.setenv("S3_OUTPUT_BUCKET", "out")
    monkeypatch.setenv("S3_INPUT_KEY", "video.mp4")
    cfg = PipelineConfig.from_environ()
    assert cfg.aws_region == "us-east-1"
    assert cfg.s3_input_key == "video.mp4"
    assert cfg.model_name == "yolov8n-pose.pt"

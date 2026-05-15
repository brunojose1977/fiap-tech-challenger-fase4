"""Configuração via variáveis de ambiente (12-factor)."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _require(name: str) -> str:
    v = os.environ.get(name, "").strip()
    if not v:
        msg = f"Variável de ambiente obrigatória ausente: {name}"
        raise ValueError(msg)
    return v


@dataclass(frozen=True)
class PipelineConfig:
    """Parâmetros do pipeline alinhados ao notebook Colab."""

    aws_region: str
    s3_input_bucket: str
    s3_predict_bucket: str
    s3_output_bucket: str
    s3_input_key: str
    model_name: str
    work_dir: str
    predict_conf: float
    predict_iou: float
    predict_imgsz: int
    violence_confidence_threshold: float

    @classmethod
    def from_environ(cls) -> PipelineConfig:
        return cls(
            aws_region=_require("AWS_REGION"),
            s3_input_bucket=_require("S3_INPUT_BUCKET"),
            s3_predict_bucket=_require("S3_PREDICT_BUCKET"),
            s3_output_bucket=_require("S3_OUTPUT_BUCKET"),
            s3_input_key=_require("S3_INPUT_KEY"),
            model_name=os.environ.get("MODEL_NAME", "yolov8n-pose.pt").strip(),
            work_dir=os.environ.get("WORK_DIR", "/tmp/work").strip(),
            predict_conf=float(os.environ.get("PREDICT_CONF", "0.25")),
            predict_iou=float(os.environ.get("PREDICT_IOU", "0.7")),
            predict_imgsz=int(os.environ.get("PREDICT_IMGSZ", "640")),
            violence_confidence_threshold=float(
                os.environ.get("VIOLENCE_CONFIDENCE_THRESHOLD", "0.7")
            ),
        )

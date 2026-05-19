"""Garante que o fluxo Transcribe não carrega pipeline YOLO (cv2)."""

from __future__ import annotations

import sys


def test_transcribe_cli_does_not_import_pipeline() -> None:
    """transcribe_cli não deve puxar yolo_violence_pipeline.pipeline."""
    for mod in ("yolo_violence_pipeline.pipeline", "cv2"):
        sys.modules.pop(mod, None)

    import yolo_violence_pipeline.transcribe_cli  # noqa: F401

    assert "yolo_violence_pipeline.pipeline" not in sys.modules

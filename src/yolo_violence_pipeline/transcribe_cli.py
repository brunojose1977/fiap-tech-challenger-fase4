"""CLI exclusivo do fluxo Transcribe + ChatGPT (sem importar pipeline YOLO/cv2)."""

from __future__ import annotations

import argparse
import json
import logging
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="aws-transcribe-audio-from-video-conversations: S3 + Transcribe + ChatGPT."
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    from yolo_violence_pipeline.transcribe_config import TranscribePipelineConfig
    from yolo_violence_pipeline.transcribe_pipeline import run_transcribe_pipeline

    cfg = TranscribePipelineConfig.from_environ()
    result = run_transcribe_pipeline(cfg)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result.get("errors"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

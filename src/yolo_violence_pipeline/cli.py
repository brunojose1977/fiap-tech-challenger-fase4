"""Interface de linha de comando."""

from __future__ import annotations

import argparse
import json
import logging
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pipeline YOLOv8 pose e fluxo Amazon Transcribe + análise de risco."
    )
    parser.add_argument(
        "command",
        choices=["process", "transcribe-analyze"],
        help=(
            "process: YOLOv8 + S3; "
            "transcribe-analyze: aws-transcribe-audio-from-video-conversations"
        ),
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

    if args.command == "process":
        from yolo_violence_pipeline.config import PipelineConfig
        from yolo_violence_pipeline.pipeline import run_pipeline

        cfg = PipelineConfig.from_environ()
        result = run_pipeline(cfg)
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "transcribe-analyze":
        # Delega ao CLI isolado (não importa pipeline.py / cv2 / ultralytics).
        from yolo_violence_pipeline import transcribe_cli

        return transcribe_cli.main(["--log-level", args.log_level])

    return 1


if __name__ == "__main__":
    sys.exit(main())

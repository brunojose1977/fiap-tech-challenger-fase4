"""Interface de linha de comando."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from yolo_violence_pipeline.config import PipelineConfig
from yolo_violence_pipeline.pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Processa vídeo do S3 com YOLOv8 pose e envia resultados aos buckets."
    )
    parser.add_argument(
        "command",
        choices=["process"],
        help="process: executa o pipeline completo",
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
        cfg = PipelineConfig.from_environ()
        result = run_pipeline(cfg)
        print(json.dumps(result, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())

"""Operações S3 usando a cadeia padrão de credenciais da AWS."""

from __future__ import annotations

import logging
from pathlib import Path

import boto3

logger = logging.getLogger(__name__)


def s3_client(region: str):
    return boto3.client("s3", region_name=region)


def download_file(client, bucket: str, key: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Baixando s3://%s/%s -> %s", bucket, key, dest)
    client.download_file(bucket, key, str(dest))


def upload_file(client, path: Path, bucket: str, key: str) -> None:
    logger.info("Enviando %s -> s3://%s/%s", path, bucket, key)
    client.upload_file(str(path), bucket, key)

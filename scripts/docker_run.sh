#!/usr/bin/env bash
# Build local e execução com variáveis do arquivo .env (Linux/macOS).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Crie .env a partir de .env.example"
  exit 1
fi

docker build -t yolo-violence:local .
docker run --rm --env-file .env yolo-violence:local

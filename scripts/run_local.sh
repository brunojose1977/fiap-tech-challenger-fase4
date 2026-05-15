#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Crie .env a partir de .env.example"
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

pip install -e ".[dev,runtime]"
yolo-violence process --log-level INFO

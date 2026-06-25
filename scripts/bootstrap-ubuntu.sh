#!/usr/bin/env bash
set -euo pipefail

echo "== OneEpis Ubuntu Bootstrap =="

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_command node
require_command npm
require_command python3.12
require_command docker

if ! docker compose version >/dev/null 2>&1; then
  echo "Missing required Docker Compose plugin: docker compose" >&2
  exit 1
fi

node --version
npm --version
python3.12 --version
docker --version
docker compose version

npm run check:toolchain

cp -n .env.example .env || true

docker compose -f infra/docker-compose.dev.yml up -d

python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e "apps/api[dev]"

npm ci

.venv/bin/python -m alembic -c apps/api/alembic.ini upgrade head

npm run check:api
npm run check:web
npm run check:contract

echo "OK: OneEpis listo."

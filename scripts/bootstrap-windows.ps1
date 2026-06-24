$ErrorActionPreference = "Stop"

Write-Host "== OneEpis Windows Bootstrap =="

function Require-Command {
  param([string]$Name)
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Missing required command: $Name"
  }
}

Require-Command node
Require-Command npm
Require-Command docker

$pythonCommand = Get-Command py -ErrorAction SilentlyContinue
if ($pythonCommand) {
  $python = "py"
  $pythonArgs = @("-3.12")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  $python = "python"
  $pythonArgs = @()
} else {
  throw "Missing required command: py or python"
}

docker compose version | Out-Null

node --version
npm --version
& $python @pythonArgs --version
docker --version
docker compose version

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
}

docker compose -f infra/docker-compose.dev.yml up -d

& $python @pythonArgs -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e "apps/api[dev]"

npm ci

.\.venv\Scripts\python.exe -m alembic -c apps/api/alembic.ini upgrade head

npm run check:api
npm run check:web
npm run check:contract
npm run check:architecture

Write-Host "OK: OneEpis listo."

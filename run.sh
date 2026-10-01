#!/usr/bin/env bash
# Start BroadcastBot locally.
#
#   ./run.sh          # normal run
#   ./run.sh --check  # run the self-checks only, don't start the bot
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Creating virtualenv with Python 3.10 ..."
  uv venv --python 3.10 .venv
  uv pip install --python .venv/bin/python -r requirements.txt
fi

if [[ "$(uname -s)" == "Darwin" ]] && ! grep -q . .env 2>/dev/null; then
  echo "No .env found. Copy .env.example to .env and fill in your credentials."
  exit 1
fi

if grep -q "AAExampleTokenReplaceMe" .env 2>/dev/null; then
  echo "⚠️  .env still contains the placeholder BOT_TOKEN."
  echo "    Edit $ROOT/.env with your real BOT_TOKEN / API_ID / API_HASH / AUTH_USERS."
  echo "    The bot cannot connect to Telegram until you do."
  exit 1
fi

if [[ "${1:-}" == "--check" ]]; then
  .venv/bin/python selfcheck.py
  .venv/bin/python selfcheck_handlers.py
  exit 0
fi

echo "Starting BroadcastBot ..."
exec .venv/bin/python main.py

#!/usr/bin/env bash
# Stop the local MongoDB instance started by start-mongo.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -x "$ROOT/.mongo/bin/mongod" ]]; then
  echo "mongod not found; nothing to stop."
  exit 0
fi

if ! nc -z 127.0.0.1 27017 >/dev/null 2>&1; then
  echo "MongoDB is not running."
  exit 0
fi

"$ROOT/.mongo/bin/mongod" --dbpath "$ROOT/.mongo-data" --shutdown
echo "MongoDB stopped."

#!/usr/bin/env bash
# Start a local MongoDB instance for BroadcastBot (no Homebrew/Xcode needed).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONGO_HOME="$ROOT/.mongo"
DBPATH="$ROOT/.mongo-data"
LOGPATH="$ROOT/.mongo-logs"

mkdir -p "$DBPATH" "$LOGPATH"

if [[ ! -x "$MONGO_HOME/bin/mongod" ]]; then
  echo "mongod not found at $MONGO_HOME/bin/mongod"
  echo "Download it with:"
  echo "  curl -sL -o /tmp/mongo.tgz https://fastdl.mongodb.org/osx/mongodb-macos-arm64-8.0.12.tgz"
  echo "  mkdir -p $MONGO_HOME && tar -xzf /tmp/mongo.tgz -C $MONGO_HOME --strip-components=1"
  echo "  # optional, for a mongo shell:"
  echo "  curl -sL -o /tmp/mongosh.tgz https://downloads.mongodb.com/compass/mongosh-2.3.1-darwin-arm64.zip"
  exit 1
fi

if nc -z 127.0.0.1 27017 >/dev/null 2>&1; then
  echo "MongoDB is already running on 127.0.0.1:27017"
  exit 0
fi

"$MONGO_HOME/bin/mongod" \
  --dbpath "$DBPATH" \
  --logpath "$LOGPATH/mongod.log" \
  --port 27017 \
  --bind_ip 127.0.0.1 \
  --fork

echo "MongoDB started (dbpath: $DBPATH, log: $LOGPATH/mongod.log)"

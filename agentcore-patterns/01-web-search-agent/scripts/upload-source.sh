#!/usr/bin/env bash
# Usage: ./scripts/upload-source.sh <source-bucket-name>
set -euo pipefail

BUCKET="${1:?Usage: $0 <source-bucket-name>}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENT_DIR="$SCRIPT_DIR/../agent"
TMP_DIR="$SCRIPT_DIR/../tmp"
TMP_ZIP="$TMP_DIR/source.zip"

mkdir -p "$TMP_DIR"

echo "Packaging agent source..."
(cd "$AGENT_DIR" && zip -r "$TMP_ZIP" . -x "*.pyc" -x "__pycache__/*" -x ".pytest_cache/*")

echo "Uploading to s3://$BUCKET/source.zip ..."
aws s3 cp "$TMP_ZIP" "s3://$BUCKET/source.zip"

echo "Done. Pipeline will trigger automatically."

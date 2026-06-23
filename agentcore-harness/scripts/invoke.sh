#!/usr/bin/env bash
# Usage: ./scripts/invoke.sh <harness-arn> "<prompt>"
set -euo pipefail

HARNESS_ARN="${1:?Usage: $0 <harness-arn> '<prompt>'}"
PROMPT="${2:?Usage: $0 <harness-arn> '<prompt>'}"
SESSION_ID=$(python -c "import uuid; print(uuid.uuid4())" 2>/dev/null || cat /proc/sys/kernel/random/uuid)

echo "Harness: $HARNESS_ARN"
echo "Prompt:  $PROMPT"
echo ""

PAYLOAD=$(python -c "import json,sys; print(json.dumps({'prompt': sys.argv[1]}))" "$PROMPT")

aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-arn "$HARNESS_ARN" \
  --runtime-session-id "$SESSION_ID" \
  --qualifier DEFAULT \
  --payload "$PAYLOAD" \
  --output json \
| python -c "
import sys, json
data = json.load(sys.stdin)
chunks = data.get('response', [])
raw = ''.join(c if isinstance(c, str) else c.decode('utf-8') for c in chunks)
try:
    print(json.dumps(json.loads(raw), indent=2))
except Exception:
    print(raw)
"

#!/usr/bin/env bash
# Usage: ./scripts/invoke.sh <agent-runtime-arn> "<prompt>"
set -euo pipefail

AGENT_ARN="${1:?Usage: $0 <agent-runtime-arn> '<prompt>'}"
PROMPT="${2:?Usage: $0 <agent-runtime-arn> '<prompt>'}"
SESSION_ID=$(uuidgen 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())")

echo "Invoking runtime: $AGENT_ARN"
echo "Prompt: $PROMPT"
echo ""

RESPONSE=$(aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-arn "$AGENT_ARN" \
  --runtime-session-id "$SESSION_ID" \
  --qualifier DEFAULT \
  --payload "$(echo '{}' | python3 -c "import sys,json; d=json.load(sys.stdin); d['prompt']='$PROMPT'; print(json.dumps(d))")" \
  --output json)

echo "$RESPONSE" | python3 -c "
import sys, json, base64
data = json.load(sys.stdin)
raw = data.get('response', '')
if isinstance(raw, list):
    raw = ''.join(raw)
try:
    print(json.dumps(json.loads(raw), indent=2))
except Exception:
    print(raw)
"

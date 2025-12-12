#!/usr/bin/env bash
# Post a test message to a Viber Channel via Channels Post API.
# Requires environment variables:
#   VIBER_TOKEN            - Channel token (NOT bot/PA token)
#   VIBER_CHANNEL_ID       - Your channel id
# Optional:
#   VIBER_SENDER_NAME      - Display name (default: GrainTrade)
#   VIBER_CHANNEL_POST_URL - Endpoint (default: https://chatapi.viber.com/pa/post)
#
# Usage:
#   export VIBER_TOKEN=...; export VIBER_CHANNEL_ID=...;
#   ./scripts/send_viber_channel_test.sh "Hello from GrainTrade!"

set -euo pipefail

# Env
TOKEN=${VIBER_TOKEN:-}
CHANNEL_ID=${VIBER_CHANNEL_ID:-}
SENDER_NAME=${VIBER_SENDER_NAME:-GrainTrade}
POST_URL=${VIBER_CHANNEL_POST_URL:-https://chatapi.viber.com/pa/post}

if [[ -z "$TOKEN" ]]; then
  echo "[ERROR] VIBER_TOKEN is not set" >&2
  exit 1
fi
if [[ -z "$CHANNEL_ID" ]]; then
  echo "[ERROR] VIBER_CHANNEL_ID is not set" >&2
  exit 1
fi

# Message text
TEXT=${*:-"Test message from GrainTrade ($(date -Iseconds))"}

# Build JSON payload
# Prefer jq if available for safe JSON escaping
if command -v jq >/dev/null 2>&1; then
  PAYLOAD=$(jq -n \
    --arg t "$TEXT" \
    --arg n "$SENDER_NAME" \
    --arg c "$CHANNEL_ID" \
    '{type:"text", text:$t, sender:{name:$n}, channel_id:$c}')
else
  # Fallback: basic quote escaping (handles simple cases)
  ESCAPED_TEXT=${TEXT//"/\"}
  ESCAPED_NAME=${SENDER_NAME//"/\"}
  PAYLOAD='{"
  PAYLOAD+="type":"text","text":"'"$ESCAPED_TEXT"'"","sender":{"name":"'"$ESCAPED_NAME"'""},"channel_id":"'"$CHANNEL_ID"'""}'
fi

TMP_BODY=$(mktemp)
HTTP_CODE=$(curl -sS -o "$TMP_BODY" -w "%{http_code}" \
  -X POST "$POST_URL" \
  -H "X-Viber-Auth-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD") || {
  echo "[ERROR] curl failed" >&2
  rm -f "$TMP_BODY"
  exit 2
}

echo "HTTP $HTTP_CODE"
if command -v jq >/dev/null 2>&1; then
  jq . "$TMP_BODY" || cat "$TMP_BODY"
else
  cat "$TMP_BODY"
fi

# Viber returns {"status":0, ...} on success
if grep -q '"status"\s*:\s*0' "$TMP_BODY"; then
  echo "[OK] Message posted to channel $CHANNEL_ID"
  rm -f "$TMP_BODY"
  exit 0
else
  echo "[WARN] Non-zero Viber status. See response above." >&2
  rm -f "$TMP_BODY"
  exit 3
fi

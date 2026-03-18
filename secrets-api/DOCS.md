# Crabby Secrets API

A localhost HTTP service that provides secure access to all API credentials.
Keys are stored in ~/.secrets/keys.json as the single source of truth.

## Base URL

    http://127.0.0.1:5002

Always localhost-only. Never exposed externally.

## Authentication

All endpoints except /v1/health require a Bearer token in the Authorization header:

    Authorization: Bearer <token>

The token is stored at ~/.secrets/api-token.txt.

Shell helper:
    TOKEN=$(cat ~/.secrets/api-token.txt)
    curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:5002/v1/keys

---

## Endpoints

### GET /v1/health
Public. No auth required.
Returns: {"status": "ok", "keys_available": 4}

### GET /v1/keys
List all key names and metadata. Values are never included in this response.
Returns: {"keys": [{"name": "...", "service": "...", "description": "...", "added": "..."}, ...]}

### GET /v1/keys/<name>
Get full details including value for one key.
Returns: {"name": "...", "value": "...", "service": "...", "description": "...", "added": "..."}
Errors: 401 no auth, 403 wrong token, 404 key not found

### GET /v1/keys/<name>/value
Returns the raw key value as text/plain. Handy in shell scripts:
    KEY=$(curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:5002/v1/keys/openrouter_api_key/value)

---

## Key Store Format (~/.secrets/keys.json)

Both formats work. No server restart needed after editing the file.

Rich format (recommended):
    {
      "my_api_key": {
        "value": "the-actual-key",
        "service": "service-name",
        "description": "What this key is for",
        "added": "YYYY-MM-DD"
      }
    }

Flat format (also works):
    {"my_api_key": "the-actual-key"}

---

## Current Keys

Name                    Service      Description
openrouter_api_key      openrouter   LLM access (Claude, DeepSeek, Gemini etc.)
brave_search_api_key    brave        Web search tool
google_places_api_key   google       goplaces skill
telegram_bot_token      telegram     @CrabbyOpen_bot

---

## Adding a New Key

1. Edit ~/.secrets/keys.json and add a new entry
2. No restart needed - keys are read from disk on every request
3. Verify: curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:5002/v1/keys

---

## Running Tests

    cd ~/secrets-api
    venv/bin/python -m pytest test_secrets_api.py -v

Tests cover: API server endpoints, auth, error handling, flat-key compatibility,
and a live validation call for every real API key.

---

## Service Management

    sudo systemctl status crabby-secrets      # check status
    sudo systemctl restart crabby-secrets     # restart after config changes
    sudo journalctl -u crabby-secrets -f      # live logs

---

## Docker Migration Note

When OpenClaw moves to Docker, this server stays on the host.
The container calls http://host-gateway:5002/v1/keys/<name> to fetch credentials
instead of reading config files directly. ~/.secrets/keys.json never enters
the container - that is the security boundary.

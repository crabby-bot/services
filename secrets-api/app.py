"""
Crabby Secrets API
==================
A simple localhost key-value store for API credentials.

Adding a new key
----------------
Edit ~/.secrets/keys.json and add an entry in either format:

  Simple:   "my_key": "the-value"
  Rich:     "my_key": {"value": "the-value", "service": "acme", "description": "...", "added": "YYYY-MM-DD"}

No server restart needed — keys are read from disk on every request.

Endpoints
---------
  GET /v1/health              Public. Returns server status and key count.
  GET /v1/keys                Auth required. Lists all key names (no values).
  GET /v1/keys/<name>         Auth required. Returns value + metadata for one key.
  GET /v1/keys/<name>/value   Auth required. Returns the raw value as plain text.

Auth
----
  All non-health endpoints require:  Authorization: Bearer <token>
  Token is stored in ~/.secrets/api-token.txt
"""

import json
import os
from flask import Flask, jsonify, request, abort, make_response

app = Flask(__name__)

KEYS_FILE  = os.environ.get('KEYS_FILE',  '/home/crabby/.secrets/keys.json')
TOKEN_FILE = os.environ.get('TOKEN_FILE', '/home/crabby/.secrets/api-token.txt')


# ── helpers ───────────────────────────────────────────────────────────────────

def _load_keys():
    with open(KEYS_FILE) as f:
        return json.load(f)

def _normalise(name, entry):
    """Accept both 'key: value' and 'key: {value, service, ...}' formats."""
    if isinstance(entry, str):
        return {'name': name, 'value': entry, 'service': None, 'description': None, 'added': None}
    return {
        'name':        name,
        'value':       entry.get('value'),
        'service':     entry.get('service'),
        'description': entry.get('description'),
        'added':       entry.get('added'),
    }

def _api_token():
    with open(TOKEN_FILE) as f:
        return f.read().strip()

def _require_auth():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        abort(401, description='Missing Bearer token')
    if auth[7:] != _api_token():
        abort(403, description='Invalid token')


# ── error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(401)
def unauthorized(e):
    return jsonify(error='unauthorized', message=str(e.description)), 401

@app.errorhandler(403)
def forbidden(e):
    return jsonify(error='forbidden', message=str(e.description)), 403

@app.errorhandler(404)
def not_found(e):
    return jsonify(error='not_found', message=str(e.description)), 404


# ── routes ────────────────────────────────────────────────────────────────────

@app.route('/v1/health')
def health():
    """Public health check. No auth required."""
    keys = _load_keys()
    return jsonify(status='ok', keys_available=len(keys))


@app.route('/v1/keys')
def list_keys():
    """List all key names with metadata (no values)."""
    _require_auth()
    keys = _load_keys()
    result = []
    for name, entry in keys.items():
        meta = _normalise(name, entry)
        result.append({k: v for k, v in meta.items() if k != 'value'})
    return jsonify(keys=result)


@app.route('/v1/keys/<name>')
def get_key(name):
    """Return value + metadata for a single key."""
    _require_auth()
    keys = _load_keys()
    if name not in keys:
        abort(404, description=f'Key "{name}" not found')
    return jsonify(_normalise(name, keys[name]))


@app.route('/v1/keys/<name>/value')
def get_key_value(name):
    """Return the raw key value as plain text (handy for shell scripts)."""
    _require_auth()
    keys = _load_keys()
    if name not in keys:
        abort(404, description=f'Key "{name}" not found')
    value = _normalise(name, keys[name])['value']
    resp = make_response(value, 200)
    resp.mimetype = 'text/plain'
    return resp


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5002)

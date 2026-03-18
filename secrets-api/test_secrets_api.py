"""
Unit tests for the Crabby Secrets API.
Runs against the live server on 127.0.0.1:5002.
Also tests each real API key is valid and functional.

Usage:
    cd ~/secrets-api && venv/bin/python -m pytest test_secrets_api.py -v
"""

import pytest
import requests
import json

BASE = 'http://127.0.0.1:5002'
TOKEN_FILE = '/home/crabby/.secrets/api-token.txt'
KEYS_FILE  = '/home/crabby/.secrets/keys.json'

def _token():
    with open(TOKEN_FILE) as f:
        return f.read().strip()

def _auth():
    return {'Authorization': f'Bearer {_token()}'}

def _keys():
    with open(KEYS_FILE) as f:
        return json.load(f)

def _val(name):
    entry = _keys()[name]
    return entry['value'] if isinstance(entry, dict) else entry


# ── Secrets API server tests ──────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_ok(self):
        r = requests.get(f'{BASE}/v1/health')
        assert r.status_code == 200
        assert r.json()['status'] == 'ok'

    def test_health_shows_key_count(self):
        r = requests.get(f'{BASE}/v1/health')
        assert r.json()['keys_available'] == len(_keys())

    def test_health_needs_no_auth(self):
        r = requests.get(f'{BASE}/v1/health')
        assert r.status_code == 200


class TestAuth:
    def test_list_keys_requires_auth(self):
        r = requests.get(f'{BASE}/v1/keys')
        assert r.status_code == 401

    def test_get_key_requires_auth(self):
        r = requests.get(f'{BASE}/v1/keys/openrouter_api_key')
        assert r.status_code == 401

    def test_wrong_token_rejected(self):
        r = requests.get(f'{BASE}/v1/keys', headers={'Authorization': 'Bearer wrong'})
        assert r.status_code == 403


class TestListKeys:
    def test_returns_all_key_names(self):
        r = requests.get(f'{BASE}/v1/keys', headers=_auth())
        assert r.status_code == 200
        names = [k['name'] for k in r.json()['keys']]
        assert set(names) == set(_keys().keys())

    def test_does_not_return_values(self):
        r = requests.get(f'{BASE}/v1/keys', headers=_auth())
        for entry in r.json()['keys']:
            assert 'value' not in entry

    def test_returns_metadata(self):
        r = requests.get(f'{BASE}/v1/keys', headers=_auth())
        for entry in r.json()['keys']:
            assert 'name' in entry
            assert 'service' in entry
            assert 'description' in entry


class TestGetKey:
    def test_returns_value_and_metadata(self):
        r = requests.get(f'{BASE}/v1/keys/openrouter_api_key', headers=_auth())
        assert r.status_code == 200
        data = r.json()
        assert data['name'] == 'openrouter_api_key'
        assert data['value'] == _val('openrouter_api_key')
        assert data['service'] == 'openrouter'

    def test_missing_key_returns_404(self):
        r = requests.get(f'{BASE}/v1/keys/does_not_exist', headers=_auth())
        assert r.status_code == 404

    def test_all_keys_retrievable(self):
        for name in _keys():
            r = requests.get(f'{BASE}/v1/keys/{name}', headers=_auth())
            assert r.status_code == 200, f'Failed for key: {name}'

class TestRawValue:
    def test_value_endpoint_returns_plain_text(self):
        r = requests.get(f'{BASE}/v1/keys/openrouter_api_key/value', headers=_auth())
        assert r.status_code == 200
        assert r.headers['Content-Type'].startswith('text/plain')
        assert r.text == _val('openrouter_api_key')

    def test_new_flat_key_works(self, tmp_path):
        """Verify a plain 'key: value' entry (no metadata) still works."""
        keys = _keys()
        keys['_test_flat_key'] = 'flat-value-123'
        with open(KEYS_FILE, 'w') as f:
            json.dump(keys, f, indent=2)
        try:
            r = requests.get(f'{BASE}/v1/keys/_test_flat_key/value', headers=_auth())
            assert r.status_code == 200
            assert r.text == 'flat-value-123'
        finally:
            keys.pop('_test_flat_key')
            with open(KEYS_FILE, 'w') as f:
                json.dump(keys, f, indent=2)


# ── Real API key validation tests ─────────────────────────────────────────────

class TestOpenRouterKey:
    def test_key_is_valid(self):
        key = _val('openrouter_api_key')
        r = requests.get(
            'https://openrouter.ai/api/v1/models',
            headers={'Authorization': f'Bearer {key}'},
            timeout=10
        )
        assert r.status_code == 200, f'OpenRouter rejected key: {r.text[:200]}'

    def test_key_fetched_via_api(self):
        key_via_api = requests.get(
            f'{BASE}/v1/keys/openrouter_api_key/value', headers=_auth()
        ).text
        r = requests.get(
            'https://openrouter.ai/api/v1/models',
            headers={'Authorization': f'Bearer {key_via_api}'},
            timeout=10
        )
        assert r.status_code == 200


class TestBraveSearchKey:
    def test_key_is_valid(self):
        key = _val('brave_search_api_key')
        r = requests.get(
            'https://api.search.brave.com/res/v1/web/search',
            headers={'Accept': 'application/json', 'X-Subscription-Token': key},
            params={'q': 'opencrabby test', 'count': 1},
            timeout=10
        )
        assert r.status_code == 200, f'Brave rejected key: {r.text[:200]}'

    def test_key_fetched_via_api(self):
        key = requests.get(
            f'{BASE}/v1/keys/brave_search_api_key/value', headers=_auth()
        ).text
        r = requests.get(
            'https://api.search.brave.com/res/v1/web/search',
            headers={'Accept': 'application/json', 'X-Subscription-Token': key},
            params={'q': 'test', 'count': 1},
            timeout=10
        )
        assert r.status_code == 200


class TestGooglePlacesKey:
    def test_key_is_valid(self):
        key = _val('google_places_api_key')
        r = requests.get(
            'https://maps.googleapis.com/maps/api/place/nearbysearch/json',
            params={'location': '53.3498,-6.2603', 'radius': 500, 'key': key},
            timeout=10
        )
        data = r.json()
        assert r.status_code == 200
        assert data.get('status') not in ('REQUEST_DENIED', 'INVALID_REQUEST'),             f'Google Places rejected key: {data.get("status")}'

    def test_key_fetched_via_api(self):
        key = requests.get(
            f'{BASE}/v1/keys/google_places_api_key/value', headers=_auth()
        ).text
        r = requests.get(
            'https://maps.googleapis.com/maps/api/place/nearbysearch/json',
            params={'location': '53.3498,-6.2603', 'radius': 500, 'key': key},
            timeout=10
        )
        assert r.json().get('status') not in ('REQUEST_DENIED', 'INVALID_REQUEST')


class TestTelegramToken:
    def test_token_is_valid(self):
        token = _val('telegram_bot_token')
        r = requests.get(
            f'https://api.telegram.org/bot{token}/getMe',
            timeout=10
        )
        data = r.json()
        assert data['ok'] is True, f'Telegram rejected token: {data}'
        assert data['result']['username'] == 'CrabbyOpen_bot'

    def test_token_fetched_via_api(self):
        token = requests.get(
            f'{BASE}/v1/keys/telegram_bot_token/value', headers=_auth()
        ).text
        r = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=10)
        assert r.json()['ok'] is True



class TestOpenAIKey:
    def test_key_is_valid(self):
        key = _val('openai_api_key')
        r = requests.get(
            'https://api.openai.com/v1/models',
            headers={'Authorization': f'Bearer {key}'},
            timeout=10
        )
        assert r.status_code == 200, f'OpenAI rejected key: {r.text[:200]}'

    def test_key_fetched_via_api(self):
        key = requests.get(
            f'{BASE}/v1/keys/openai_api_key/value', headers=_auth()
        ).text
        r = requests.get(
            'https://api.openai.com/v1/models',
            headers={'Authorization': f'Bearer {key}'},
            timeout=10
        )
        assert r.status_code == 200, f'OpenAI rejected key fetched via secrets API: {r.text[:200]}'

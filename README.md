# Crabby Services

Flask services running on the Crabby server.

| Service | Port | Description |
|---|---|---|
| web | 5000 | Main website (opencrabby.com) |
| admin | 5001 | Admin dashboard |
| secrets-api | 5002 | API key management |

## Setup
Each service has its own venv. From the service directory:
```bash
python3 -m venv venv --upgrade-deps
venv/bin/pip install -r requirements.txt
sudo systemctl restart crabby-<service>
```

## Secrets
Keys live at `~/.secrets/keys.json` — never in this repo.
See `secrets-api/DOCS.md` for the API reference.

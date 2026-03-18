# Crabby Secrets API

Localhost HTTP service serving API credentials to Crabby.

## Setup
```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

## Keys store
Keys live at `~/.secrets/keys.json` — never committed to this repo.
Bearer token at `~/.secrets/api-token.txt` — never committed.

## Run
```bash
sudo systemctl start crabby-secrets
```

See DOCS.md for full API reference.

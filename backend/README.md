# Cadence — Backend

FastAPI backend for the Cadence DCA savings bot. Non-custodial: never holds
funds, only places market **buy** orders on the user's exchange. No
withdrawal code path exists, by design.

## Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in values
```

Generate the encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Put the result in `ENCRYPTION_KEY`. Get Supabase URL / keys / JWT secret
from the Supabase dashboard (Settings > API).

## Database

Run `migrations/001_init.sql` in the Supabase SQL editor. It creates the
tables and enables Row Level Security (per-user isolation).

## Run

```bash
uvicorn app.main:app --reload
```

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

All `/api/*` routes require a Supabase user JWT:
`Authorization: Bearer <token>`.

## Architecture

| Path | Role |
|------|------|
| `app/main.py` | App + CORS + scheduler lifespan |
| `app/core/config.py` | Settings from env |
| `app/core/security.py` | Fernet encrypt/decrypt for API keys |
| `app/core/deps.py` | Supabase JWT auth dependency |
| `app/db/supabase.py` | Service-role client |
| `app/services/exchange_service.py` | ccxt — verify keys, market buy |
| `app/services/dca_engine.py` | Run due strategies, record trades |
| `app/services/scheduler.py` | APScheduler 1-min poll |
| `app/api/routes/` | exchanges, strategies, trades |

## Endpoints

- `POST /api/exchanges` — connect exchange (validates keys, stores encrypted)
- `GET /api/exchanges` — list connections (hint only)
- `DELETE /api/exchanges/{id}`
- `POST /api/strategies` — create DCA strategy
- `GET /api/strategies` — list
- `PATCH /api/strategies/{id}` — update / pause (emergency stop)
- `DELETE /api/strategies/{id}`
- `GET /api/trades` — history

## Security notes

- API keys encrypted app-side before DB write — never plaintext.
- RLS enabled on every table; backend also filters by `user_id`.
- Keys should be created **without withdrawal permission** on the exchange.
- The scheduler is a simple in-process poller (MVP). For multi-instance
  deploys, move to a single worker or a queue (Celery) to avoid double
  execution.

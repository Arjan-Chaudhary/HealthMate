# HealthMate AI
One FastAPI service that also serves the web app (no build step). Users can optionally register (explicit consent); profile and history (chats, diet, exercise, risk results) are stored in SQLite per account. Passwords are scrypt-hashed. "Delete my data" deletes the account and all its rows. Logged-out use stores nothing.

IMPORTANT: set DB_PATH to a persistent disk (e.g. /data/healthmate.db) or the database is wiped on each redeploy. For multi-instance or free hosts, swap SQLite for Postgres.

## Run locally
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # optional; without it the assistant returns source passages directly
uvicorn main:app --reload

## Deploy (Render / Railway / Fly)
Push this folder to GitHub -> New Web Service -> Environment: Docker. Add env var ANTHROPIC_API_KEY (optional MODEL). HTTPS is provided by the host. Health check path: /healthz

## Safety design
Numbers (calories, plans, risk scores, trend flags) come from deterministic code; the LLM only phrases answers from retrieved WHO passages. Emergency phrases (EN/HI) short-circuit to 112/108. Users with listed conditions, pregnancy or under 18 get no diet/exercise plan. Educational screening only, not diagnosis. Have a clinician review the knowledge base and outputs before real use.

## Free hosting (no cost)
render.yaml now targets Render's free plan: no API key and no disk needed. The assistant answers from the bilingual WHO knowledge base (extractive); add ANTHROPIC_API_KEY later for LLM phrasing. Free plan: app sleeps when idle and accounts reset on restart.
Run checks: python tests.py

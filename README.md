# SentinelAI

SentinelAI is an AI-powered endpoint security investigation and decision-support platform for Windows endpoints. It monitors endpoint telemetry, detects suspicious behavior, correlates related events into incidents, enriches investigations with security knowledge, and gives analysts natural-language reasoning and mitigation guidance.

SentinelAI is not an antivirus and is not an EDR replacement. It is built as an analyst assistant for explanation, triage, and decision support.

## Completed Modules

- Backend foundation: FastAPI app, settings, logging, health checks, SQLAlchemy session management, Alembic migrations.
- Authentication: JWT registration, login, current-user endpoint, password hashing, protected analyst APIs.
- Endpoint ingestion: endpoint inventory and raw security event ingestion.
- Detection and correlation: detection rules, alert creation, incident correlation, severity/status workflows.
- Incident management: incident list/detail, timeline, notes, assignment, status and resolution updates.
- AI reasoning: retrieval-grounded incident analysis with MITRE knowledge and optional OpenAI-compatible LLM support.
- Threat intelligence: MITRE mapping plus optional NVD CVE enrichment.
- Frontend dashboard: React/TypeScript app with protected routes, auth flow, overview analytics, incident queue/detail, endpoint inventory, RAG and threat-intel panels.
- Deployment foundation: Dockerfiles, Nginx SPA hosting, PostgreSQL-backed Docker Compose environment.

## Architecture

```text
SentinelAI
├── backend
│   ├── app/api              # FastAPI route modules
│   ├── app/core             # config and logging
│   ├── app/db               # engine, sessions, declarative base
│   ├── app/models           # SQLAlchemy persistence models
│   ├── app/repositories     # database access layer
│   ├── app/schemas          # Pydantic request/response contracts
│   ├── app/services         # business logic, detection, reasoning, threat intel
│   └── alembic              # database migrations
└── frontend
    └── src
        ├── app              # router and shell
        ├── auth             # session provider
        ├── lib              # typed API client
        └── pages            # dashboard and analyst workflows
```

## Run With Docker

Create a secure JWT secret before running in production.

```bash
cd "C:\Users\Duniya Vasa\OneDrive\Desktop\Sentinal AI"
docker compose up --build
```

Services:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1
- API docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432

Optional environment values can be passed to Compose:

```bash
$env:JWT_SECRET_KEY="replace-with-a-long-random-secret"
$env:LLM_BASE_URL="https://api.openai.com/v1"
$env:LLM_API_KEY="your-api-key"
$env:LLM_MODEL="gpt-4o-mini"
$env:NVD_API_KEY="optional-nvd-key"
docker compose up --build
```

## Local Backend Development

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements\base.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Run backend tests:

```bash
.\.venv\Scripts\python -m pytest app\tests -q
```

## Local Frontend Development

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

Build for production:

```bash
npm run build
```

## Production Notes

- Replace `JWT_SECRET_KEY` before exposing the backend.
- Keep event ingestion separated from analyst JWT authentication when adding a real endpoint agent; agent authentication should use scoped machine credentials or signed ingestion tokens.
- Use PostgreSQL for persistent deployments. SQLite-style shortcuts are intentionally avoided in the production path.
- Chroma retrieval can be enabled with `RAG_RETRIEVER=chroma`; the default memory retriever keeps development lightweight.
- The LLM integration is optional. Without LLM settings, SentinelAI returns deterministic retrieval-grounded guidance.

## Recommended Next Modules

- Endpoint agent prototype for Windows event collection.
- RBAC roles for admin/analyst separation.
- Background jobs for scheduled CVE and threat-intelligence refresh.
- Audit logging for authentication and incident workflow actions.
- Frontend code splitting for chart-heavy dashboard bundles.

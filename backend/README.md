# SentinelAI Backend Foundation

This module contains the foundational backend structure for SentinelAI.

## Included in Module 1

- FastAPI application factory
- API router aggregation
- Health and readiness endpoints
- Centralized environment configuration
- Logging bootstrap
- SQLAlchemy engine and session factory
- Initial API tests

## Local setup

1. Create a virtual environment.
2. Install dependencies from `backend/requirements/base.txt`.
3. Copy `backend/.env.example` to `backend/.env`.
4. Run the API with Uvicorn:

```bash
uvicorn app.main:app --app-dir backend --reload
```

## Database migrations

Run migrations from the `backend` directory:

```bash
alembic upgrade head
```

Create a new revision after future model changes:

```bash
alembic revision --autogenerate -m "describe change"
```

## Why this module exists

The goal of this first module is to establish a clean, extensible foundation so that later modules such as authentication, ingestion, incident correlation, and AI reasoning can be added without restructuring the application.

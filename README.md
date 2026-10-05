# cairn-api

The Cairn backend: accounts, sync coordination, share links and print orders. Python
[FastAPI](https://fastapi.tiangolo.com) on Fly.io, with Postgres on Neon and encrypted blobs in
Cloudflare R2.

**Journal content never passes through this service.** The phone encrypts it and uploads it straight
to storage using pre-signed URLs. Postgres holds accounts and sync bookkeeping only. See
[ARCHITECTURE.md](https://github.com/Cairn-Outdoors-Journal/cairn-product-hub/blob/main/ARCHITECTURE.md)
in the product hub.

## Setup

```sh
brew install uv
uv sync
```

uv installs the right Python (3.14) and all dependencies into `.venv/`.

## Commands

| Task | Command |
|---|---|
| Run locally | `uv run uvicorn cairn_api.main:app --reload` (docs at http://127.0.0.1:8000/docs) |
| Test | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Type-check | `uv run mypy` |
| Apply migrations | `CAIRN_DATABASE_URL=... uv run cairn-migrate` |
| Export the API contract | `uv run python scripts/export_openapi.py` |

Database tests run when `CAIRN_TEST_DATABASE_URL` is set; **they reset the `public` schema**, so
point them at a throwaway database:

```sh
docker run -d --rm --name cairn-testdb -e POSTGRES_PASSWORD=postgres -p 55432:5432 postgres:17
CAIRN_TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:55432/postgres uv run pytest
docker stop cairn-testdb
```

## Configuration

Environment variables, prefixed `CAIRN_` (see `src/cairn_api/config.py`):

| Variable | Meaning |
|---|---|
| `CAIRN_ENVIRONMENT` | `local`, `test`, `staging` or `prod` |
| `CAIRN_DATABASE_URL` | Postgres connection URL. In staging and prod it comes from cairn-infra as a Fly secret. |

## Migrations

Plain SQL files in `migrations/`, named `NNNN_description.sql`. Each runs once, in its own
transaction, and is recorded in `schema_migrations`; an advisory lock prevents concurrent runs.
Migrations only move forward: to change something, add a new file. On Fly.io they run as the
release command before new machines start.

## Pipelines

- **CI** ([ci.yml](.github/workflows/ci.yml)), on every pull request and on `main`:
  - lint, format check, type-check;
  - tests against a temporary Postgres;
  - OpenAPI export;
  - container image build.
- **Release** ([release.yml](.github/workflows/release.yml)): pushing a `v*` tag creates a GitHub
  release with `openapi.json` attached. cairn-app pins one of these.
- **Deploys** to Fly.io (staging on merge, prod on tag) will be added once cairn-infra has created
  the Fly apps and the deploy token exists.

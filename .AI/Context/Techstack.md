# Tech Stack — Pinned Versions

Versions are exact. Do not bump without updating this file and re-running the full test suite. Locked because the 24h build budget cannot absorb dependency churn.

---

## Backend (Python 3.12)

| Package | Version | Purpose | Notes |
|---|---|---|---|
| `python` | 3.12.x | runtime | not 3.13 — some deps lag |
| `fastapi` | 0.115.0 | HTTP framework | requires `pydantic>=2.7` |
| `uvicorn[standard]` | 0.30.6 | ASGI server | run `uvicorn SRC.Backend.main:app --workers 4` in prod-like; `--reload` in dev |
| `sqlalchemy` | 2.0.35 | ORM | **async** API only — `AsyncSession`, `select()`, `update()` |
| `asyncpg` | 0.29.0 | Postgres driver | DSN: `postgresql+asyncpg://...` |
| `alembic` | 1.13.3 | migrations | configure `env.py` for async (template provided in SQLAlchemy docs) |
| `pydantic` | 2.9.x | schemas | v2 syntax — `model_config = ConfigDict(...)`, `Field(...)`, no `Config` class |
| `pydantic-settings` | 2.5.x | env var config | `BaseSettings` lives here, not in `pydantic` core anymore |
| `python-jose[cryptography]` | 3.3.0 | JWT | `jose.jwt.encode/decode` |
| `passlib[bcrypt]` | 1.7.4 | password hash | pin `bcrypt==4.0.1` to avoid a known passlib/bcrypt 4.1+ warning |
| `bcrypt` | 4.0.1 | hash impl | see above |
| `aiosmtplib` | 3.0.x | async SMTP | works against mailhog out of box |
| `email-validator` | 2.2.x | EmailStr validation | required by Pydantic `EmailStr` |
| `python-multipart` | 0.0.9 | form parsing | required by FastAPI for any `Form()` field |
| `httpx` | 0.27.x | test client + outbound HTTP | also used by FastAPI `TestClient` |

### Backend dev/test
| Package | Version | Purpose |
|---|---|---|
| `pytest` | 8.3.x | test runner |
| `pytest-asyncio` | 0.24.x | async test support — set `asyncio_mode = "auto"` in `pyproject.toml` |
| `pytest-cov` | 5.0.x | coverage |
| `freezegun` | 1.5.x | time mocking (OTP expiry tests) |
| `factory-boy` | 3.3.x | test fixtures |

---

## Database

| Component | Version | Notes |
|---|---|---|
| PostgreSQL | 15.x | image `postgres:15-alpine` in docker-compose; **not 16+** — partial-index syntax is identical, but we standardize on 15 |

No extensions required. No Redis. No queue broker.

---

## Frontend (Node 20)

| Package | Version | Purpose | Notes |
|---|---|---|---|
| `node` | 20.x LTS | runtime | not 22 |
| `react` | 18.3.1 | UI lib | hooks-only, no class components |
| `react-dom` | 18.3.1 | renderer | |
| `react-router-dom` | 6.26.x | routing | v6 API — `createBrowserRouter` or `<Routes>`/`<Route>` |
| `vite` | 5.4.x | build tool | `npm create vite@latest -- --template react-ts` |
| `typescript` | 5.5.x | types | `strict: true` in tsconfig |
| `tailwindcss` | 3.4.x | styling | configure with `@tailwind base/components/utilities` |
| `postcss` | 8.4.x | required by tailwind | |
| `autoprefixer` | 10.4.x | required by tailwind | |
| `axios` | 1.7.x | HTTP client | single instance with interceptors |
| `react-hook-form` | 7.53.x | form state | uncontrolled inputs |
| `@hookform/resolvers` | 3.9.x | RHF + Zod glue | `zodResolver(schema)` |
| `zod` | 3.23.x | runtime schema validation | mirror Pydantic schemas |
| `react-day-picker` | 9.1.x | calendar | replaces Odoo's date picker UX |
| `date-fns` | 3.6.x | date math | required by react-day-picker; do not use moment |
| `lucide-react` | 0.451.x | icon set | matches Odoo aesthetic |
| `recharts` | 2.12.x | bar charts (P1 reports) | only loaded on reports page |
| `clsx` | 2.1.x | conditional classnames | |

### Frontend dev/test
| Package | Version | Purpose |
|---|---|---|
| `@playwright/test` | 1.47.x | E2E | run `npx playwright install` after `npm install` |
| `@vitejs/plugin-react` | 4.3.x | Vite React plugin | |
| `eslint` | 9.x | linter | flat config |
| `eslint-plugin-react-hooks` | 5.x | hook rules | |
| `prettier` | 3.3.x | formatter | |

---

## API Test Layer (Node 20, separate from frontend)

Located at `SRC/Backend/tests/api/` with its own `package.json`.

| Package | Version | Purpose |
|---|---|---|
| `jest` | 29.x | test runner |
| `supertest` | 7.x | HTTP assertions |
| `@types/jest` | 29.x | types |
| `@types/supertest` | 6.x | types |
| `ts-jest` | 29.x | TypeScript transform for jest |
| `jsonwebtoken` | 9.x | mint test JWTs that match backend's HS256 secret |

---

## Infrastructure

| Component | Version | Notes |
|---|---|---|
| Docker | latest | required for compose |
| docker-compose | v2 (plugin) | `docker compose` (no hyphen) |
| `mailhog` | image `mailhog/mailhog:latest` | SMTP capture, web UI on :8025 |

---

## Version Pinning Rationale

- **FastAPI 0.115 + Pydantic 2.9** — last verified-compatible pairing as of cutoff. Pydantic 2.10+ introduces strict mode changes.
- **SQLAlchemy 2.0.35** — async API stable, `mapped_column()` available, type stubs solid.
- **bcrypt 4.0.1 (not 4.1+)** — passlib 1.7.4 emits deprecation warning with bcrypt 4.1, breaks some test assertions on stderr.
- **React Router 6 (not 7)** — v7 changed module structure mid-2024; v6 is the documented hackathon-default.
- **Tailwind 3.4 (not 4 alpha)** — v4 reorganized config; not stable enough for 24h commit.
- **Playwright 1.47** — page object model docs match this version.

---

## Out-of-Scope Dependencies (do not add)

- Redux / Zustand / MobX — Context + hooks suffice
- React Query / SWR — manual hooks suffice
- Material UI / Chakra / Mantine — Tailwind primitives only
- Celery / RQ / Dramatiq — no background queue; cron jobs run via OS scheduler
- Sentry / Datadog — out of scope
- Stripe / Razorpay live SDK — payment is mocked

---

## Dependency Install Commands

```bash
# Backend
cd SRC/Backend
python -m venv .venv && source .venv/bin/activate
pip install fastapi==0.115.0 'uvicorn[standard]'==0.30.6 sqlalchemy==2.0.35 \
            asyncpg==0.29.0 alembic==1.13.3 pydantic==2.9.2 pydantic-settings==2.5.2 \
            'python-jose[cryptography]'==3.3.0 'passlib[bcrypt]'==1.7.4 bcrypt==4.0.1 \
            aiosmtplib==3.0.2 email-validator==2.2.0 python-multipart==0.0.9 httpx==0.27.2
pip install pytest==8.3.3 pytest-asyncio==0.24.0 pytest-cov==5.0.0 freezegun==1.5.1 factory-boy==3.3.1

# Frontend
cd SRC/Frontend
npm create vite@latest . -- --template react-ts
npm install react-router-dom@6.26 axios@1.7 react-hook-form@7.53 @hookform/resolvers@3.9 \
            zod@3.23 react-day-picker@9.1 date-fns@3.6 lucide-react@0.451 recharts@2.12 clsx@2.1
npm install -D tailwindcss@3.4 postcss@8.4 autoprefixer@10.4 @playwright/test@1.47

# API tests
cd SRC/Backend/tests/api
npm init -y
npm install -D jest@29 supertest@7 @types/jest@29 @types/supertest@6 ts-jest@29 typescript@5.5 jsonwebtoken@9
```

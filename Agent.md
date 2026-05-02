# Agent.md — Coding Agent Entry Point

You are building **OverClocked Appointment App** — a hackathon-grade MVP appointment booking system modeled on Odoo Appointments. Read this file first, every session, before any code.

---

## 1. Project at a Glance

- **Hackathon:** VIT Pune, 24 hours, team of 4 devs
- **Benchmark:** Odoo Appointments (`https://www.odoo.com/app/appointments`)
- **Stack:** FastAPI + PostgreSQL 15 + SQLAlchemy 2 (async) + React 18 + Vite + TS + Tailwind
- **Three roles:** Customer, Organiser, Admin
- **Non-negotiable invariant:** zero double-bookings via `SELECT … FOR UPDATE SKIP LOCKED`

---

## 2. Mandatory Read Order (before writing any code)

Read top-to-bottom. Each file extends the previous one.

1. **`Documentation/appointment_db_design.docx`** — authoritative DB schema. 18 tables, every column, every index, the concurrency lock. **The source of truth for the database layer. Read it cover to cover.**
2. **`.AI/MVP/PRD.md`** — full product spec. 13 sections covering features, APIs, services, frontend pages, sequence diagrams, test specs, build order, and Definition of Done.
3. **`.AI/Context/Architecture.md`** — system design conventions: folder layout, request lifecycle, exception map, transaction discipline, state machine, time/timezone rules.
4. **`.AI/Context/Techstack.md`** — exact pinned versions. Do not deviate. Install commands at bottom.
5. **`.AI/Context/gotchas.md`** — 30 known pitfalls covering Pydantic v2, SQLAlchemy async, JWT/jose, Postgres ENUMs, Alembic autogen, DST, CORS, Playwright auth state, and more. Skim once; revisit when a layer bites you.
6. **`.AI/Skills/Backend-skills/`** — backend code conventions (folder layout, error patterns, async style).
7. **`.AI/Skills/frontend-design/`** — frontend conventions (component composition, Tailwind patterns).
8. **`.AI/Skills/playwright/`** — Playwright config and helpers. Read **before** writing E2E tests.
9. **`.AI/Skills/owl_odoo_components_handbook/`** — UI patterns to replicate. **NOT a framework to adopt** — extract interaction design only (booking page layout, preset chooser, tabs, resource chips, calendar grid).
10. **`Documentation/screenshots/`** + **`Documentation/flow.png`** — visual references for both organiser and customer journeys.
11. **`Documentation/problem-statement.pdf`** — original brief.

---

## 3. The Five Architectural Anchors (memorize)

Every implementation choice cascades from these. They are restated from `.AI/MVP/PRD.md` §2.

1. **Pre-materialized slot rows** in `generated_slots`. Slots are physical rows, not computed on-the-fly.
2. **`SELECT … FOR UPDATE SKIP LOCKED`** is the sole concurrency primitive for booking writes.
3. **JWT-only stateless auth** with `roles[]` claim baked into the token. 8h TTL.
4. **Service-layer state machine** (`appointment_service.transition`) is the only mutator of `appointments.status`.
5. **Backend owns availability**; frontend never computes slot times or capacity.

---

## 4. The One SQL Pattern You Must Get Right

```sql
SELECT * FROM generated_slots
  WHERE id = :slot_id AND is_blocked = FALSE AND booked_count < max_capacity
  FOR UPDATE SKIP LOCKED;
```

- Lives inside a single `async with session.begin():` block in `booking_service.create`.
- Empty rowset → raise `SlotUnavailableError` (HTTP 409). Do not retry, do not wait.
- Capacity bump (`UPDATE generated_slots SET booked_count = booked_count + :n`) and `INSERT INTO appointments` happen in the same transaction.
- A unit test (`test_unit_booking_calls_for_update_skip_locked`) asserts this exact string is present in source.

---

## 5. Build Order (parallel tracks, 22h)

Refer to `.AI/MVP/PRD.md` §12 for the hour-by-hour table. High-level:

- **Dev1** — Backend Core (auth, models, migrations, RBAC)
- **Dev2** — Slots/Booking (slot generation service, booking transaction, status machine, API tests)
- **Dev3** — Frontend Customer (auth pages, home, booking flow, confirmation, my-appointments)
- **Dev4** — Frontend Organiser/Admin + E2E tests (preset chooser, config tabs, share link, admin users, Playwright)

Hard dependency: Dev3/Dev4 cannot integrate APIs until Dev1's auth and Dev2's booking endpoints land at hour 9.

---

## 6. Hard Rules (will be enforced by tests and code review)

- All booking writes use the **verbatim** lock SQL above. CI greps for it.
- All status transitions go through `appointment_service.transition()`. Direct `UPDATE appointments SET status = ...` is forbidden.
- All datetimes stored UTC. Convert at the API boundary.
- All endpoints prefixed `/api/v1`.
- Pydantic v2 syntax (`model_config = ConfigDict(...)`, no inner `Config` class).
- SQLAlchemy 2.0 async syntax (`AsyncSession`, `select()`, `mapped_column()`).
- `expire_on_commit=False` on the session maker. Always.
- `bcrypt==4.0.1` (not 4.1+). See `gotchas.md` G-10.
- Tests are first-class. No feature is "done" without its tests green across all three layers.
- **No P2 features.** Out of scope: flexible slots, SMS, real payment gateway, i18n, mobile app, closing days. Do not build them. Do not stub them. Do not add config flags for them.

---

## 7. Folder Conventions

```
SRC/Backend/                        # Python 3.12 / FastAPI
  main.py                           # app factory, includes routers, mounts CORS
  config.py                         # pydantic-settings Settings
  db/                               # session, base, models/ (one file per domain)
  schemas/                          # Pydantic DTOs (one file per resource)
  routes/                           # APIRouter modules (one file per resource)
  services/                         # business logic — pure functions on a session
  core/                             # security, deps, errors, time helpers
  jobs/                             # cron entry points
  scripts/seed_test_data.py         # fixtures
  alembic/                          # migrations
  tests/unit/                       # pytest
  tests/api/                        # supertest+jest (own package.json)

SRC/Frontend/                       # React 18 / Vite / TS / Tailwind
  src/main.tsx                      # root + Router
  src/api/                          # axios client + per-resource hooks
  src/auth/                         # AuthContext, useAuth
  src/pages/{public,booking,customer,organiser,admin}/
  src/components/{booking,forms,layout,ui}/
  src/lib/                          # zod-schemas, time, format
  tests/e2e/                        # Playwright specs + page-objects/
```

Files are organized by **resource**, not by **layer**. Single-resource PR touches model + schema + route + service + tests for that resource.

---

## 8. Run Commands (committed to memory)

```bash
# First-time setup
docker compose up -d postgres mailhog
alembic upgrade head
python SRC/Backend/scripts/seed_test_data.py

# Backend dev
uvicorn SRC.Backend.main:app --reload --port 8000

# Frontend dev
cd SRC/Frontend && npm run dev   # serves on :5173

# Full stack
docker compose up -d              # postgres + backend + frontend + mailhog

# Test layers (all must pass for DoD)
pytest SRC/Backend/tests/unit/ -v
cd SRC/Backend/tests/api && npx jest --runInBand
cd SRC/Frontend && npx playwright test tests/e2e/

# Migrations workflow
alembic revision --autogenerate -m "add_foo_column"
# review the generated file MANUALLY (gotchas.md G-5, G-6)
alembic upgrade head
```

---

## 9. Definition of Done (verbatim from PRD §13)

- [ ] `alembic upgrade head` runs cleanly on a fresh Postgres 15; all 18 tables + indexes present.
- [ ] `python SRC/Backend/scripts/seed_test_data.py` populates the system; demo accounts log in.
- [ ] `pytest SRC/Backend/tests/unit/ -v` — **all 28 unit tests green**, zero skipped.
- [ ] `npx jest SRC/Backend/tests/api/ --runInBand` — **all 27 API tests green**, including concurrent-double-book.
- [ ] `npx playwright test SRC/Frontend/tests/e2e/` — **all 9 E2E tests green** against `docker compose up` stack.
- [ ] Demo walkthrough succeeds end-to-end (signup → OTP → book → confirmation; reschedule; cancel; organiser create+publish+share; admin deactivate user).
- [ ] Booking source code uses the verbatim `FOR UPDATE SKIP LOCKED` pattern (CI grep check).
- [ ] No P2 features merged.
- [ ] This `Agent.md` is up to date with reality.

---

## 10. When You're Stuck

- DB question → re-read `Documentation/appointment_db_design.docx`.
- API contract question → re-read `.AI/MVP/PRD.md` §6.
- Why does X behave weirdly? → search `.AI/Context/gotchas.md` first.
- Folder layout uncertain → `.AI/Context/Architecture.md` §1.
- Version conflict → `.AI/Context/Techstack.md`.
- UI/UX uncertain → `Documentation/screenshots/` + `Documentation/flow.png` + `owl_odoo_components_handbook`.

If a decision is not covered, decide based on the five anchors and document it in `.AI/Context/Architecture.md` §14 (Decision Log). Do not silently invent conventions.

---

## 11. What Not To Do

- Do not rewrite the schema. The docx is authoritative.
- Do not introduce new dependencies not listed in `.AI/Context/Techstack.md`.
- Do not add ORM relationships you don't immediately use — they cause hidden eager loads in async.
- Do not skip writing the test alongside the feature. The 22h plan budgets time for tests.
- Do not optimize for production scale. Optimize for demo correctness.
- Do not refactor "while you're in there." Single-purpose changes only.
- Do not commit secrets. `.env` is gitignored; `.env.example` is committed with placeholders.
- Do not adopt OWL as the frontend framework. We use React. OWL handbook is UI-pattern reference only.
- Do not build P2 features. See §6.

---

## 12. Project Status Tracker

Update this section at the end of each work block. Format: `YYYY-MM-DD HH:MM | dev | what changed`.

| Timestamp | Dev | Status |
|---|---|---|
| 2026-05-02 | Setup | Repo bootstrapped; PRD + Context files written; ready for hour-0 build start |
| 2026-05-02 12:15 | Codex | MVP scaffold created: FastAPI backend, 18-table SQLAlchemy schema, Alembic migration, seed script, React/Vite frontend, Docker Compose, and initial tests |
| 2026-05-02 12:34 | Codex | Restored Documentation from origin/main; started isolated Docker Postgres on localhost:5433; migrated, seeded, and restarted backend successfully |
| 2026-05-02 12:37 | Codex | Switched backend to local PostgreSQL on localhost:5432 via ignored .env; migrated, seeded, restarted, and verified health/login |
| 2026-05-02 12:49 | Codex | Improved frontend flow: role-aware login redirects, richer navigation, booking readiness states, organiser type overview, and safer customer appointment actions |
| 2026-05-02 12:58 | Codex | Fixed booking empty-state flow by auto-selecting next available date; verified full customer booking reaches confirmation |
| | | |

---

**Ready? Start with `Documentation/appointment_db_design.docx`. Then `.AI/MVP/PRD.md`. Then write code.**

# Architecture — System Design Conventions

This document defines the **structural conventions** every coding agent must follow. Decisions here are derived from `.AI/MVP/PRD.md` Section 2 (architectural anchors) and `Documentation/appointment_db_design.docx`. Do not deviate without updating this file first.

---

## 1. Repository Layout

```
OverClocked_Appointment_app/
├── Agent.md                          # entry point — read first
├── docker-compose.yml                # postgres + backend + frontend + mailhog
├── .env.example                      # all env vars listed
├── .AI/
│   ├── Context/                      # YOU ARE HERE
│   ├── MVP/PRD.md                    # spec of record
│   ├── Skills/                       # agent skill packs
│   └── Tasks/                        # per-feature task breakdowns
├── Documentation/                    # human-authored references
└── SRC/
    ├── Backend/
    │   ├── main.py                   # FastAPI app factory + router includes
    │   ├── config.py                 # pydantic-settings Settings class
    │   ├── db/
    │   │   ├── session.py            # async engine, async_sessionmaker, get_db dep
    │   │   ├── base.py               # declarative Base
    │   │   └── models/               # one file per domain (auth.py, config.py, scheduling.py, booking.py, comms.py)
    │   ├── schemas/                  # Pydantic v2 request/response DTOs, one file per resource
    │   ├── routes/                   # APIRouter modules, one file per resource (auth.py, appointment_types.py, bookings.py, ...)
    │   ├── services/                 # business logic — pure functions on a session
    │   │   ├── auth_service.py
    │   │   ├── slot_generation_service.py
    │   │   ├── booking_service.py
    │   │   ├── appointment_service.py    # status state machine
    │   │   ├── notification_service.py
    │   │   └── payment_service.py
    │   ├── core/
    │   │   ├── security.py           # JWT encode/decode, password hash
    │   │   ├── deps.py               # get_current_user, require_role
    │   │   ├── errors.py             # exception classes + handlers
    │   │   └── time.py               # UTC helpers, tz conversion
    │   ├── jobs/
    │   │   ├── complete_past_appointments.py   # cron every 10min
    │   │   └── nightly_slot_generation.py      # cron 00:05 UTC
    │   ├── scripts/
    │   │   └── seed_test_data.py
    │   ├── alembic/                  # migration env + versions/
    │   └── tests/
    │       ├── unit/                 # pytest
    │       └── api/                  # supertest+jest (package.json + jest.config.js here)
    └── Frontend/
        ├── package.json
        ├── vite.config.ts
        ├── tailwind.config.js
        ├── tsconfig.json
        ├── index.html
        ├── src/
        │   ├── main.tsx              # React root + Router
        │   ├── App.tsx               # route table
        │   ├── api/                  # axios client + per-resource hooks
        │   │   ├── client.ts         # axios instance with JWT interceptor
        │   │   ├── auth.ts
        │   │   ├── appointmentTypes.ts
        │   │   ├── bookings.ts
        │   │   └── admin.ts
        │   ├── auth/
        │   │   ├── AuthContext.tsx
        │   │   └── useAuth.ts
        │   ├── pages/                # one folder per route family
        │   │   ├── public/           # Login, Signup, Otp, ForgotPassword, ResetPassword
        │   │   ├── booking/          # BookingPage, ConfirmationPage
        │   │   ├── customer/         # MyAppointments, Profile, Reschedule
        │   │   ├── organiser/        # AppointmentTypes, NewType, ConfigForm, Bookings, Calendar, Resources
        │   │   └── admin/            # Users, Stats
        │   ├── components/           # reusable presentational components
        │   │   ├── booking/          # DatePickerLeft, ResourceChips, TimeSlotsPanel, BookingDetailsSidebar
        │   │   ├── forms/            # OtpInput, DynamicForm
        │   │   ├── layout/           # NavBar, Sidebar, AuthShell, AppShell
        │   │   └── ui/               # Button, Modal, Toast, Card primitives
        │   ├── lib/
        │   │   ├── zod-schemas.ts    # mirrors backend Pydantic
        │   │   ├── time.ts           # browser tz utils
        │   │   └── format.ts
        │   └── styles/index.css
        └── tests/
            └── e2e/                  # playwright specs + page-objects/
```

**Rule:** files are placed in their directory by *resource* (auth, appointment_types, bookings, ...), not by *layer*. A single PR for "appointment types" touches `models/`, `schemas/`, `routes/`, `services/`, `tests/` for that one resource.

---

## 2. Backend Request Lifecycle

```
Client request
  └─► FastAPI route handler (routes/*.py)
        ├─► Pydantic schema parses body              (raises 422 on shape errors)
        ├─► Depends(get_current_user) decodes JWT    (raises 401)
        ├─► Depends(require_role(...))               (raises 403)
        ├─► Depends(get_db) yields AsyncSession
        └─► Calls service function with (session, payload, current_user)
              └─► Service opens `async with session.begin():` if it mutates
                    ├─► Performs reads/writes
                    ├─► Raises domain exception on failure (booking.errors.*)
                    └─► Returns ORM model OR dict
        └─► Route maps return → response Pydantic model → JSON
```

**Rules:**
- Route handlers are **thin**: parse input, call one service function, return one schema. No business logic in routes.
- Services are **pure functions on a session** — never instantiate their own engine, never read settings except via injection.
- Services raise typed domain exceptions defined in `core/errors.py`. The global FastAPI exception handler maps each to its HTTP code.
- Transactions are explicit: `async with session.begin():` wraps any multi-statement write. Routes do not begin transactions.

---

## 3. Domain Exception Map

`core/errors.py` defines the exception hierarchy and the FastAPI exception-handler maps each to a status. Add a new exception → register a handler in the same file.

| Exception | HTTP | Body |
|---|---|---|
| `ValidationError` (Pydantic) | 422 | `{detail: [...]}` |
| `InvalidCredentialsError` | 401 | `{detail: "invalid_credentials"}` |
| `AccountUnverifiedError` | 403 | `{detail: "account_unverified"}` |
| `AccountDisabledError` | 403 | `{detail: "account_disabled"}` |
| `OtpExpiredError` | 410 | `{detail: "otp_expired"}` |
| `EmailExistsError` | 409 | `{detail: "email_exists"}` |
| `NotOwnerError` | 403 | `{detail: "not_owner"}` |
| `RoleRequiredError` | 403 | `{detail: "role_required", required: "..."}` |
| `SlotUnavailableError` | 409 | `{detail: "slot_unavailable"}` |
| `CapacityExceededError` | 409 | `{detail: "capacity_exceeded"}` |
| `IntakeAnswerMissingError` | 422 | `{detail: "intake_answer_missing", question_id: int}` |
| `CancelWindowClosedError` | 409 | `{detail: "cancel_window_closed"}` |
| `RescheduleWindowClosedError` | 409 | `{detail: "reschedule_window_closed"}` |
| `SameSlotRescheduleError` | 422 | `{detail: "same_slot_reschedule"}` |
| `InvalidTransitionError` | 409 | `{detail: "invalid_transition", from: "...", to: "..."}` |
| `ConfigIncompleteError` | 422 | `{detail: "config_incomplete", missing: [...]}` |
| `LastAdminProtectedError` | 422 | `{detail: "last_admin_protected"}` |
| `SelfDeactivationForbiddenError` | 422 | `{detail: "self_deactivation_forbidden"}` |
| `PaymentRequiredError` (P1) | 402 | `{detail: "payment_required", payment_url: "..."}` |
| `NotFoundError` | 404 | `{detail: "not_found", resource: "..."}` |

---

## 4. Database Conventions

- **Engine:** single `create_async_engine(DATABASE_URL, pool_size=20, max_overflow=10, pool_pre_ping=True)`.
- **Session:** `async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)`. The `expire_on_commit=False` setting is mandatory — without it, post-commit attribute access triggers refetches that fail in async context.
- **Dependency:** `get_db` yields a session and `await session.close()` in finally. Sessions never cross requests.
- **Migrations:** every schema change ships with an Alembic migration. Auto-generate with `alembic revision --autogenerate -m "..."` then **manually review** — autogen misses partial indexes, check constraints, and enum changes (see gotchas.md).
- **Indexes:** all listed in PRD §7 must exist by hour 3 of build. The `idx_generated_slots_lookup` partial index is the hottest path.
- **Timestamps:** every table has `created_at` and `updated_at` `TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()`. Updates use `onupdate=func.now()` at the model layer.
- **Soft deletes:** none for MVP. Cancel = status change, not delete.

### Transaction discipline
A single logical operation = a single `async with session.begin():`. Do not nest. Do not commit manually inside services.

```python
# CORRECT
async def create_booking(session: AsyncSession, payload, actor):
    async with session.begin():
        slot = await _lock_slot(session, payload.slot_id)
        if slot is None:
            raise SlotUnavailableError()
        ...
        return appointment

# WRONG — manual commits, multiple transactions
async def create_booking_bad(session, payload, actor):
    slot = await _lock_slot(session, payload.slot_id)
    await session.commit()           # closes lock window — race opens
    await session.execute(insert_appt)
    await session.commit()
```

---

## 5. Auth & RBAC Conventions

- **Token shape:** `{sub: str(user_id), roles: ["customer"|"organiser"|"admin"], exp: epoch}`. Algorithm HS256. Secret in env var `JWT_SECRET`.
- **TTL:** access token 8h. No refresh tokens for MVP.
- **Issuance:** `auth_service.issue_token(user)` is the only producer. Roles snapshot at login — admin role mutation requires re-login.
- **Verification:** `core/deps.get_current_user` decodes, fetches user from DB (one query, cached per-request), raises `InvalidCredentialsError` on bad token, `AccountDisabledError` if `is_active=FALSE`.
- **Role gates:** `Depends(require_role("organiser"))` — accepts varargs for multi-role allow.
- **Ownership gates:** `Depends(require_owner_of_appointment_type)` and `Depends(require_owner_of_booking)` defined in `core/deps.py`. Routes use them after `require_role` to layer ownership on top of role.
- **Password hashing:** bcrypt via `passlib.context.CryptContext(schemes=["bcrypt"])`. Cost factor default 12.

---

## 6. Slot Lifecycle

```
Trigger ─► slot_generation_service.regenerate(appointment_type_id)
                │
                ▼
   For each (date, working_hours, resource):
        Compute slot windows of duration_minutes
        UPSERT generated_slots ON CONFLICT (appointment_type_id, resource_id, start_datetime) DO NOTHING
                │
                ▼
       Returns count_inserted
```

Triggers:
1. `PATCH /appointment-types/:id/publish` — synchronous.
2. `POST /appointment-types/:id/working-hours` — synchronous (replaces hours, regenerates).
3. `POST/DELETE /appointment-types/:id/resources` — synchronous.
4. Cron `jobs/nightly_slot_generation.py` at 00:05 UTC — extends rolling window.

**Invariant:** existing rows with `booked_count > 0` are never deleted or mutated by regeneration. ON CONFLICT DO NOTHING enforces this.

---

## 7. Booking Concurrency Pattern

This is the single most important section. The pattern is non-negotiable.

```python
async def create_booking(session: AsyncSession, payload: BookingCreate, actor: User) -> Appointment:
    async with session.begin():
        # 1. Lock the slot row, verify capacity in one shot
        result = await session.execute(text("""
            SELECT * FROM generated_slots
              WHERE id = :slot_id
                AND is_blocked = FALSE
                AND booked_count < max_capacity
              FOR UPDATE SKIP LOCKED
        """), {"slot_id": payload.slot_id})
        slot_row = result.first()
        if slot_row is None:
            raise SlotUnavailableError()

        if slot_row.booked_count + payload.people_count > slot_row.max_capacity:
            raise CapacityExceededError()

        # 2. Insert appointment
        appt = Appointment(...)
        session.add(appt)
        await session.flush()   # populates appt.id

        # 3. Capacity bump + audit
        await session.execute(
            update(GeneratedSlot)
            .where(GeneratedSlot.id == payload.slot_id)
            .values(booked_count=GeneratedSlot.booked_count + payload.people_count)
        )
        session.add(SlotCapacityLog(slot_id=payload.slot_id, appointment_id=appt.id, delta=payload.people_count, ...))
        session.add(AuditLog(event="booking.created", ...))

    # session.begin() committed on context exit
    return appt
```

**Cancellation** uses `FOR UPDATE` (no SKIP) on the same row before decrementing — we own the booking, no contention concern.

**Reschedule** locks both old and new slots in id-sorted order to prevent deadlock under bidirectional concurrent reschedules.

---

## 8. Status State Machine

`appointment_service.transition(session, appt_id, target, actor, reason=None)` is the **only** place `appointments.status` mutates. Direct UPDATEs are forbidden — enforced by code review and a unit test that greps for `UPDATE appointments SET status` outside this service.

```
            ┌───────────┐
            │  pending  │
            └─┬───┬─────┘
              │   │
       confirm│   │cancel
              ▼   ▼
       ┌──────────┐    ┌───────────┐
       │confirmed │    │ cancelled │
       └─┬─┬─┬────┘    └───────────┘
         │ │ │
 complete│ │ │reschedule
         ▼ │ ▼
 ┌────────┐│ ┌─────────────┐
 │complete││ │ rescheduled │
 └────────┘│ └─────────────┘
           │
    cancel ▼
       ┌───────────┐
       │ cancelled │
       └───────────┘
```

Every transition writes one `audit_logs` row with `event="status.transition"`, `before`, `after`, `actor_id`, `reason`.

---

## 9. Time & Timezone

- **Storage:** all `TIMESTAMP WITH TIME ZONE` columns store UTC.
- **Backend computation:** `datetime.now(timezone.utc)` only. No naive datetimes anywhere. Helper `core.time.utcnow()` is the canonical source.
- **API I/O:** ISO 8601 with offset (`2026-05-02T14:30:00+00:00`).
- **Slot generation:** `appointment_types.timezone` defines the wall-clock timezone of the working_hours rows. Slot times are computed in that tz, then converted to UTC for storage.
- **Availability endpoint:** `tz_offset_minutes` query param tells backend the customer's local offset for grouping by date — does not affect stored times.
- **Frontend display:** convert UTC → browser tz at render only. Use `Intl.DateTimeFormat` with `timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone`.

---

## 10. Frontend Architecture

- **Routing:** React Router v6 with nested layouts. Public routes wrapped in `<AuthShell>`, app routes wrapped in `<AppShell>` which redirects to `/login` if no token.
- **State:** React Context for auth + per-page hooks for data (`useAppointmentTypes`, `useAvailability`, `useMyAppointments`). No Redux, no Zustand.
- **Data fetching:** custom hooks wrap axios calls and expose `{data, loading, error, refetch}`. No SWR/React Query for MVP — too much new dependency surface.
- **Forms:** React Hook Form + Zod resolver. The Zod schema for each request mirrors the backend Pydantic schema by hand. Field names match exactly.
- **Styling:** Tailwind utility classes only. No CSS modules, no styled-components. Reusable visual primitives in `components/ui/`.
- **API client:** single axios instance in `src/api/client.ts` with:
  - `baseURL: import.meta.env.VITE_API_BASE_URL` (default `http://localhost:8000/api/v1`)
  - Request interceptor: attach `Authorization: Bearer <token>` from localStorage
  - Response interceptor: on 401, clear token and redirect to `/login`
- **Error display:** every page renders error toasts via a `ToastProvider` mounted at root. Domain error codes map to user messages in `lib/error-messages.ts`.

---

## 11. Testing Conventions

- **Unit tests** import services directly and use a `pytest` fixture `db_session` that wraps each test in a transaction and rolls back on exit. No real HTTP.
- **API tests** spin the FastAPI app in a separate process via `docker-compose -f docker-compose.test.yml up`. Supertest hits real HTTP. Each test file calls a `resetDb()` helper that truncates and re-seeds.
- **E2E tests** assume `docker-compose up` is running. Tests use Playwright's `request` API to set up state via the API (faster than UI clicks for setup), then drive the UI for the assertion path.
- **Test seed user passwords** are committed in source — `seed_test_data.py` uses `Customer123!`, `Organiser123!`, `Admin123!`. These are fixtures, not real credentials.

---

## 12. Logging & Observability (MVP scope)

- Backend logs to stdout via Python `logging` at INFO. Format: `{timestamp} {level} {logger} {message}`.
- Every booking operation logs: actor_id, slot_id, outcome (created|unavailable|capacity_exceeded).
- No metrics/tracing for MVP. Audit_logs table is the queryable history.

---

## 13. Configuration

`.env` loaded via `pydantic-settings`. Required vars:

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/appointments
JWT_SECRET=<32+ char random string>
JWT_ALGORITHM=HS256
JWT_ACCESS_TTL_SECONDS=28800
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_FROM=noreply@appointments.local
APP_BASE_URL=http://localhost:5173
FUTURE_DAYS_LIMIT_DEFAULT=30
OTP_TTL_SECONDS=600
RESET_TOKEN_TTL_SECONDS=900
```

Frontend uses `VITE_API_BASE_URL` and `VITE_APP_NAME`. All other config is backend-only.

---

## 14. Decision Log (additions go below)

| Date | Decision | Author | Rationale |
|---|---|---|---|
| 2026-05-02 | Adopt PRD anchors AD-1..AD-5 | PRD | See `.AI/MVP/PRD.md` §2 |
| 2026-05-02 | No refresh tokens for MVP | PRD | Reduces auth surface; 8h TTL acceptable for hackathon demo |
| 2026-05-02 | No SWR/React Query | PRD | Keeps frontend dep surface small for 24h build |
| 2026-05-02 | No Redis cache layer | PRD | Postgres alone meets latency needs at hackathon scale |

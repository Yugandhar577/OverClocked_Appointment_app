# Gotchas — Known Pitfalls

Each item: **what bites you → why → how to avoid**. Read before writing code in the affected area.

---

## G-1. The lock query must be VERBATIM
**Bites:** subtle race conditions in production-grade traffic during demo.
**Why:** any deviation — adding `LIMIT`, dropping `is_blocked = FALSE`, reordering — opens a window where two writers can both proceed.
**Avoid:** copy-paste this exact string into `booking_service`:
```sql
SELECT * FROM generated_slots
  WHERE id = :slot_id AND is_blocked = FALSE AND booked_count < max_capacity
  FOR UPDATE SKIP LOCKED
```
A unit test (`test_unit_booking_calls_for_update_skip_locked`) greps for this string in source — keep it as a single string literal, not f-string concatenation.

---

## G-2. `SELECT FOR UPDATE SKIP LOCKED` returns empty rowset, not exception
**Bites:** developers expect an exception/timeout.
**Why:** SKIP LOCKED is a Postgres feature that returns 0 rows when the row is locked by another transaction. No error, no wait.
**Avoid:** check `result.first() is None` and raise `SlotUnavailableError` yourself.

---

## G-3. SQLAlchemy 2.0 async — `expire_on_commit` defaults to True
**Bites:** `AttributeError` or `MissingGreenlet` exceptions when reading attributes after commit.
**Why:** default behavior expires all attributes on commit, forcing a refetch on next access. In async context this triggers a sync DB call inside a coroutine and crashes.
**Avoid:** `async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)`. Always.

---

## G-4. Don't use `session.commit()` inside a `session.begin()` block
**Bites:** `InvalidRequestError: This transaction is already begun`.
**Why:** `async with session.begin():` already manages commit/rollback. Calling `commit()` inside double-commits.
**Avoid:** trust the context manager. To early-commit, restructure to multiple `begin()` blocks (rare — usually means your transaction boundaries are wrong).

---

## G-5. Alembic autogen misses partial indexes
**Bites:** `idx_generated_slots_lookup` (the hot path index) is silently omitted from migrations.
**Why:** Alembic's autogenerate doesn't emit `WHERE is_blocked = FALSE` clauses on indexes.
**Avoid:** in the migration file, add manually:
```python
op.create_index(
    "idx_generated_slots_lookup",
    "generated_slots",
    ["appointment_type_id", "start_datetime", "resource_id"],
    postgresql_where=sa.text("is_blocked = FALSE"),
)
```

---

## G-6. Alembic autogen and PostgreSQL ENUMs
**Bites:** enum changes generate broken migrations (`ALTER TYPE ... ADD VALUE` cannot run inside a transaction).
**Why:** Alembic wraps each migration in a transaction by default; `ALTER TYPE ADD VALUE` requires autocommit.
**Avoid:** for enum additions, use:
```python
def upgrade():
    op.execute("COMMIT")               # close current tx
    op.execute("ALTER TYPE appointment_status ADD VALUE 'rescheduled'")
```
Or use `String` columns with a `CHECK` constraint instead of native ENUMs. **MVP recommendation:** use String + CHECK for `appointments.status` and `payments.status` to avoid this entirely.

---

## G-7. Pydantic v2 — no more `Config` inner class
**Bites:** `Config` is silently ignored, validators don't fire as expected.
**Why:** v2 replaced inner `Config` with `model_config = ConfigDict(...)`.
**Avoid:**
```python
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)   # was orm_mode=True in v1
    id: int
    email: str
```

---

## G-8. Pydantic v2 — `EmailStr` requires `email-validator`
**Bites:** ImportError at startup.
**Why:** validator extracted to optional dep.
**Avoid:** explicitly install `email-validator==2.2.0`.

---

## G-9. JWT — `sub` claim must be a string
**Bites:** `jose.jwt.decode` raises `JWTClaimsError: Subject must be a string` when `sub` is int.
**Why:** RFC 7519 says `sub` is a string; jose enforces.
**Avoid:** `payload = {"sub": str(user.id), "roles": [...], "exp": ...}`.

---

## G-10. bcrypt 4.1+ + passlib 1.7.4 incompatibility
**Bites:** stderr warning `(trapped) error reading bcrypt version`, plus tests that capture stderr fail.
**Why:** bcrypt 4.1 changed its `__about__` module that passlib introspects.
**Avoid:** pin `bcrypt==4.0.1`.

---

## G-11. FastAPI dependency overrides for tests
**Bites:** test using `app.dependency_overrides[get_db] = ...` leaks to other tests.
**Why:** `dependency_overrides` is a module-level dict, not test-scoped.
**Avoid:** use a `pytest` fixture with `yield` and `app.dependency_overrides.clear()` in teardown.

---

## G-12. asyncpg connection pool exhaustion under Playwright concurrent tests
**Bites:** double-book test hangs or returns 500.
**Why:** default pool_size=5 is too small when E2E spins multiple browser contexts hammering the API.
**Avoid:** `create_async_engine(..., pool_size=20, max_overflow=10, pool_pre_ping=True)`.

---

## G-13. Reschedule deadlock under bidirectional concurrent reschedules
**Bites:** rare but real — A reschedules slot 5→7 while B reschedules 7→5; if locks acquired in caller order they deadlock.
**Why:** both transactions hold one lock and wait for the other.
**Avoid:** sort the two slot ids before locking. Always lock lowest-id-first. The `reschedule()` pseudocode in PRD §8.3 reflects this.

---

## G-14. Slot generation timezone bug
**Bites:** generated_slots stored at wrong UTC times when `appointment_types.timezone != UTC`.
**Why:** naive `datetime(date, time)` then `.astimezone(UTC)` does the wrong thing if you don't first attach the source tz.
**Avoid:**
```python
from zoneinfo import ZoneInfo
local_tz = ZoneInfo(appointment_type.timezone)   # e.g. "Asia/Kolkata"
local_dt = datetime.combine(date, wh.start_time, tzinfo=local_tz)
utc_dt = local_dt.astimezone(timezone.utc)
```

---

## G-15. DST transitions break the slot algorithm
**Bites:** on the spring-forward day, a 30-min slot starting at 02:00 local doesn't exist; on fall-back, slots double up.
**Why:** wall-clock arithmetic across DST is undefined for non-existent times.
**Avoid:** for MVP, working with `Asia/Kolkata` (no DST) is safe. If a user picks a DST-observing timezone, document the limitation. Do not attempt full DST-aware slot generation in 24h.

---

## G-16. React Hook Form + Zod — discriminated union resolver
**Bites:** dynamic intake form (text/number/boolean/select/multi_select) fails validation cryptically.
**Why:** Zod's discriminated union must be built with `z.discriminatedUnion("question_type", [...])`, not `z.union([...])`, for clear error paths.
**Avoid:** build the per-field schema imperatively per question, then `z.object({ answers: z.array(...) })`.

---

## G-17. axios interceptor + 401 redirect loop
**Bites:** infinite redirect when /auth/login returns 401 (wrong credentials).
**Why:** the interceptor sees 401 on the login response and redirects to /login again, which has the same response on next attempt.
**Avoid:** in the response interceptor, skip redirect when `error.config.url.endsWith('/auth/login')`.

---

## G-18. localStorage JWT and Playwright auth state
**Bites:** Playwright tests start unauthenticated even after API login.
**Why:** Playwright contexts don't share localStorage; setting it via API `request` doesn't propagate to the browser context.
**Avoid:** use `page.addInitScript(() => localStorage.setItem('token', '...'))` before navigating, or reuse `storageState` via `context.storageState({path})` after one login.

---

## G-19. Vite env vars must be prefixed `VITE_`
**Bites:** `import.meta.env.API_BASE_URL` is undefined.
**Why:** Vite only exposes vars prefixed `VITE_*` to client code.
**Avoid:** name them `VITE_API_BASE_URL`. Add typings in `src/vite-env.d.ts`:
```ts
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
}
```

---

## G-20. Tailwind + shadcn-style class merging
**Bites:** classes don't override as expected (e.g., `bg-blue-500 bg-red-500` — last wins per CSS but not per JSX).
**Why:** order in JSX doesn't equal order in compiled CSS.
**Avoid:** use `clsx` + `tailwind-merge` (or just `clsx` + careful ordering) in shared UI primitives.

---

## G-21. Mailhog SMTP requires no auth
**Bites:** `aiosmtplib.SMTP` rejects with auth error if you set username/password against mailhog.
**Why:** mailhog accepts everything anonymously and rejects auth attempts.
**Avoid:** in dev `SMTP_USER` and `SMTP_PASS` must be empty/unset; conditionally call `await smtp.login(...)` only if `SMTP_USER` is set.

---

## G-22. UTC truncation on the date boundary
**Bites:** customer in IST (+05:30) selects "May 3" on date picker; backend treats it as May 3 UTC and shows May 2 evening slots.
**Why:** comparing slot start_datetime (UTC) to a naive date in different tz misclassifies.
**Avoid:** in `/availability`, accept `tz_offset_minutes` from client; compute `start_utc = (date_at_local_midnight - tz_offset)` and `end_utc = start_utc + 24h`. Filter slots by `start_datetime BETWEEN start_utc AND end_utc`.

---

## G-23. Pagination off-by-one
**Bites:** organiser sees 9 bookings on page 1, then page 2 shows the 10th twice.
**Why:** ordering by a non-unique column without secondary key.
**Avoid:** always `ORDER BY created_at DESC, id DESC` (or `start_datetime DESC, id DESC`). Include `id` as tiebreaker.

---

## G-24. CORS in dev
**Bites:** Frontend at `http://localhost:5173` cannot hit Backend at `http://localhost:8000`.
**Why:** browser CORS.
**Avoid:** in `main.py` add:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## G-25. Docker Compose Postgres — first-boot race
**Bites:** backend starts before postgres is accepting connections; first request returns 500.
**Why:** healthcheck not configured.
**Avoid:** in `docker-compose.yml`:
```yaml
postgres:
  image: postgres:15-alpine
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 2s
    retries: 10
backend:
  depends_on:
    postgres:
      condition: service_healthy
```

---

## G-26. Playwright concurrent contexts share the same DB
**Bites:** double-book test flakes — A creates a booking, B's setup expected fresh slot.
**Why:** tests run against shared docker-compose stack.
**Avoid:** for the concurrency test specifically, both contexts must target the same `slot_id` deliberately. Don't try to isolate. Other tests should call `resetDb()` (an admin-only test endpoint guarded by `if settings.ENV == "test"`).

---

## G-27. Audit logs grow unbounded
**Bites:** N/A for hackathon (24h max), but mention if asked.
**Avoid:** out of scope; no rotation policy for MVP.

---

## G-28. Status transition under reschedule
**Bites:** dev tries to set rescheduled appointment back to confirmed.
**Why:** `rescheduled` is a terminal state.
**Avoid:** state machine in `appointment_service.transition` defines `rescheduled` with empty allowed-transitions set. Test `test_unit_status_invalid_transition_raises` covers this.

---

## G-29. Capacity log delta sign
**Bites:** off-by-sign in `slot_capacity_log` makes capacity reports wrong.
**Why:** booking is `+people_count`, cancel is `-people_count`. Confused on reschedule.
**Avoid:** reschedule writes TWO log rows: `(old_slot, -n)` and `(new_slot, +n)`. Always.

---

## G-30. Frontend re-fetch after booking
**Bites:** customer books, returns to slot list, sees same slot still "available".
**Why:** stale cached availability response.
**Avoid:** AD-5 mandates re-fetch — call `refetch()` in the success handler before navigating to confirmation, OR navigate immediately and let the next page mount trigger its own fetch.

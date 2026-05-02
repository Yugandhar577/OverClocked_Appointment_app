# Payments demo (Razorpay + PostgreSQL)

End-to-end **test** flow: seed a paid appointment → create a Razorpay **Order** on the server → Standard Checkout → **verify** `razorpay_signature` on the server → persist `payments` row and mark the appointment **confirmed**.

Stack matches `docs/appointment_db_design.docx` for the payment slice: **PostgreSQL**, **SQLAlchemy 2.x**, **Alembic**, **FastAPI**. UI is a small **Vite + TypeScript** page.

## Prerequisites

- Docker (for Postgres) or your own PostgreSQL 15+ on port **5435** with DB `appt_db`, user `appt`, password `appt_secret` (see `docker-compose.yml`; host port **5435** avoids clashes with other local Postgres instances).
- Python 3.11+
- Node 20+ (for the frontend)

## Troubleshooting

- **Port 8888 already in use:** Run `uvicorn ... --port 8890` and set `PAYMENTS_API_PORT=8890` when starting Vite (`PAYMENTS_API_PORT=8890 npm run dev` from `frontend/`).

## Security

- **Never** commit real API secrets. `backend/.env` is gitignored.
- You pasted test keys in chat; rotate them in the [Razorpay Dashboard](https://dashboard.razorpay.com/) if this repo is shared.

## 1. Database

From the `payments` folder:

```bash
docker compose up -d
```

## 2. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows — then edit .env
# cp .env.example .env   # macOS/Linux

alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8888
```

Set in `.env`:

- `DATABASE_URL` — default matches Docker Compose (`localhost:5435`).
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` — test mode keys from the dashboard.
- `CORS_ORIGINS` — include `http://127.0.0.1:5174` and `http://localhost:5174` for the standalone payments UI (default Vite port). The main OverClocked app can keep using 5173.

## 3. Frontend (React + Vite + Tailwind v4)

```bash
cd frontend
npm install
npm run dev
```

Open **`http://localhost:5174/`** (standalone default; avoids clashing with the main app on 5173). The UI includes an API health badge, step progress, seed + checkout actions, copyable IDs, and live payment status polling. The API runs on **`http://127.0.0.1:8888`** by default.

Use [Razorpay test cards / methods](https://razorpay.com/docs/payments/payments/test-card-upi-details/) to complete checkout in the browser (this exercises `POST /api/payments/verify`).

### Automated API smoke test (no browser)

With the backend running on port 8888:

```bash
cd frontend
npm run test:api
# optional: BASE_URL=http://127.0.0.1:8890 npm run test:api
```

This calls `GET /health`, `POST /api/demo/reset-and-seed`, `POST /api/payments/initiate`, and `GET /api/payments/status/{id}` (Razorpay order creation uses your test keys).

Checkout uses **Razorpay default methods** from your Dashboard (UPI, cards, netbanking, wallets). The API returns `display_config: null` so the browser **does not** send `options.config` — this avoids the sample integration that **hid UPI** and limited issuers, which broke UPI and many test payments. Optional `options.config` is still supported if the API ever returns a non-empty `display_config`.

**Prefill contact** must be **E.164** (e.g. `+919876543210`); Razorpay’s docs note that a missing country code can default incorrectly. The backend now returns `prefill_contact` in that form.

## API overview

| Method | Path | Purpose |
|--------|------|--------|
| POST | `/api/demo/reset-and-seed` | Wipes demo tables and inserts one `is_paid` appointment (₹10) in `pending` state. |
| POST | `/api/payments/initiate` | Body `{ "appointment_id": "..." }` — creates Razorpay order + `payments` row `initiated`. |
| POST | `/api/payments/verify` | Body with `razorpay_*` fields — verifies HMAC, sets `payments.status=success`, confirms appointment. |
| GET | `/api/payments/status/{appointment_id}` | Read payment status. |

## Schema (payments-related)

Tables: `users`, `appointment_types`, `generated_slots`, `appointments`, `payments` — minimal columns needed for FKs and the `payments` entity as in the design doc (`amount`, `currency`, `payment_method`, `status`, `payment_gateway_ref`, `payment_gateway`, `paid_at`, `metadata`, …).

## References

- [Configure payment methods (sample)](https://razorpay.com/docs/payments/payment-gateway/web-integration/standard/configure-payment-methods/sample-code/)
- [Standard integration steps](https://razorpay.com/docs/payments/payment-gateway/web-integration/standard/integration-steps/?preferred-country=IN)
- [Node server integration](https://razorpay.com/docs/payments/server-integration/nodejs/integration-steps/) (same Order + verify pattern; this repo uses Python + official `razorpay` package)

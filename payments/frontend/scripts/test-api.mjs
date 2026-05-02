/**
 * Smoke-test backend without the browser (no Razorpay signature).
 * Usage: BASE_URL=http://127.0.0.1:8000 npm run test:api
 */
const base = process.env.BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

async function main() {
  const log = (...a) => console.log(...a);

  const h = await fetch(`${base}/health`);
  if (!h.ok) throw new Error(`GET /health -> ${h.status}`);
  log("OK  GET /health", await h.json());

  const seed = await fetch(`${base}/api/demo/reset-and-seed`, { method: "POST" });
  const seedBody = await seed.json();
  if (!seed.ok) throw new Error(`POST /api/demo/reset-and-seed -> ${seed.status} ${JSON.stringify(seedBody)}`);
  log("OK  POST /api/demo/reset-and-seed", { appointment_id: seedBody.appointment_id });

  const appointmentId = seedBody.appointment_id;
  const init = await fetch(`${base}/api/payments/initiate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ appointment_id: appointmentId }),
  });
  const initBody = await init.json();
  if (!init.ok) {
    throw new Error(`POST /api/payments/initiate -> ${init.status} ${JSON.stringify(initBody)}`);
  }
  log("OK  POST /api/payments/initiate", {
    order_id: initBody.order_id,
    amount_paise: initBody.amount_paise,
    currency: initBody.currency,
  });

  const st = await fetch(`${base}/api/payments/status/${appointmentId}`);
  const stBody = await st.json();
  if (!st.ok) throw new Error(`GET status -> ${st.status}`);
  log("OK  GET /api/payments/status/...", stBody);

  log("\nAll API smoke checks passed. Complete a browser checkout to test /api/payments/verify.");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

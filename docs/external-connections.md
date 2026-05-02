Here's the full breakdown of what to use and why each fits your hackathon:

**Payments — Razorpay** is your only real choice as an Indian team. The sandbox environment lets you test without using real money — just flip to test mode on the dashboard, generate test API keys, and you're set with `import razorpay; client = razorpay.Client(auth=(key, secret))` in two lines. Use ngrok to receive the payment webhook callback locally.

**Email — Resend** is the fastest to connect. You can send up to 3,000 emails/month (100/day) on the free plan, which covers all your booking confirmations, OTP emails, and reminders. No SMTP configs, just `pip install resend` and 4 lines of code.

**Calendar — skip the full Google API** unless you want OAuth complexity. The `ics` library generates a `.ics` file that opens natively in Google Calendar, Apple Calendar, and Outlook — no API key, no OAuth, just a file download link on your confirmation page. Add the Google Calendar API only if you want the "Add to Calendar" button to silently push the event without the user downloading anything.

**APScheduler** is the hidden critical one — your slot generation engine. It runs a job every night at midnight, reads `working_hours`, and fills `generated_slots` for the next 30 days. Without this, your booking page has nothing to display.

**For the viva:** the combination of Razorpay + ngrok is what judges will ask about — be ready to explain the webhook flow: user pays → Razorpay POSTs to your `/webhook` → you verify the signature with `client.utility.verify_payment_signature()` → you update `payments.status` to `'success'` and insert the appointment atomically.
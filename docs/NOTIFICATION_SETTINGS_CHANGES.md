# Notification Settings — Changes

## Summary

Adds org-level email/SMS reminder configuration: organisers can set how many hours before an appointment reminders fire, and customise every outgoing message template using `{{placeholder}}` syntax. A background scheduler enqueues reminders automatically and dispatches all queued notifications via SMTP (MailHog in dev, production SMTP with optional auth) and Twilio SMS.

---

## New database table — `organization_notification_settings`

Migration: `006_org_notification_settings.py` (revises 005)

| Column | Type | Default |
|---|---|---|
| `id` | UUID PK | gen_random_uuid() |
| `organization_id` | UUID FK → organizations (unique, nullable) | — |
| `reminder_email_hours` | int nullable | 24 |
| `reminder_sms_hours` | int nullable | 2 |
| `email_enabled` | bool | true |
| `sms_enabled` | bool | false |
| `sender_name` | varchar(120) | "OverClocked Appointments" |
| `reminder_email_subject` | varchar(200) | see default template |
| `reminder_email_body` | text | see default template |
| `reminder_sms_body` | text | see default template |
| `booking_confirmation_subject` | varchar(200) | see default template |
| `booking_confirmation_body` | text | see default template |
| `cancellation_subject` | varchar(200) | see default template |
| `cancellation_body` | text | see default template |
| `updated_at` | timestamptz | now() |

One row per org (or one global-default row with `organization_id = NULL` for organisers not yet assigned to an org).

---

## New API endpoints

All require `organiser` or `admin` role.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/organiser/notification-settings` | Fetch current org's settings (creates default row on first access) |
| `PUT` | `/api/v1/organiser/notification-settings` | Update settings (partial — only send fields you want to change) |
| `GET` | `/api/v1/organiser/notification-settings/placeholders` | Returns the list of available `{{placeholder}}` names |

---

## New environment variables

Add to `.env` (all optional — defaults shown):

```
SMTP_SENDER_NAME=OverClocked Appointments
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=false
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
```

MailHog works out of the box with no auth. SMS sends fail gracefully (status `failed`, error logged) if Twilio creds are absent.

---

## Background scheduler jobs

Wired into the FastAPI lifespan via APScheduler `AsyncIOScheduler` (UTC).

| Job | Cadence | What it does |
|---|---|---|
| `reminder_dispatcher` | every 5 min | Queries confirmed appointments within 48 h; enqueues `reminder_email` / `reminder_sms` `Notification` rows if the reminder window has opened and no row already exists |
| `notification_dispatcher` | every 1 min | Picks up to 50 `queued` `Notification` rows, dispatches via SMTP / Twilio, marks `sent` or `failed` |

---

## Override semantics

`AppointmentType.reminder_email_hours` / `reminder_sms_hours` take precedence over the org-level defaults when they are non-null. This lets individual appointment types have a different lead time than the org default.

Resolution order (first non-null wins):

```
AppointmentType.reminder_*_hours  →  OrganizationNotificationSettings.reminder_*_hours
```

---

## Available placeholders

| Placeholder | Value |
|---|---|
| `{{customer_name}}` | Appointment `customer_full_name` |
| `{{customer_email}}` | Appointment `customer_email` |
| `{{customer_phone}}` | Appointment `customer_phone` |
| `{{appointment_type}}` | `AppointmentType.title` |
| `{{appointment_date}}` | Slot start formatted as "May 03, 2026" |
| `{{appointment_time}}` | Slot start formatted as "02:30 PM UTC" |
| `{{confirmation_code}}` | Appointment `confirmation_code` |
| `{{organization_name}}` | `Organization.name` (or "OverClocked Appointments" if no org) |
| `{{venue}}` | `AppointmentType.venue` |

---

## Local testing

```bash
docker compose down && docker compose build && docker compose up
```

1. Log in as `org1@test.local` / `Organiser123!`
2. Navigate to **Notifications** in the top nav
3. Edit a template, insert a placeholder chip, click **Save settings**
4. Book an appointment as `cust1@test.local`
5. Open MailHog at http://localhost:8025 — booking confirmation email should arrive within 1 minute using your custom template
6. For reminder testing: manually set a confirmed appointment's `start_at` to `now() + 23 hours` and wait ≤5 min

---

## Known limitations / follow-ups

- WhatsApp channel: field reserved in Notification model but no sender implemented
- Per-customer language / localisation not yet supported
- SMS only fires when `sms_enabled = true` AND Twilio creds are configured
- `AppointmentType.booking_email_template` / `cancellation_email_template` fields (string names from migration 004) are superseded by the new template body fields and can be cleaned up in a future migration

import { zodResolver } from "@hookform/resolvers/zod"
import { useEffect, useRef, useState } from "react"
import { useForm } from "react-hook-form"

import { getNotificationPlaceholders, getNotificationSettings, updateNotificationSettings } from "../../api/notificationSettings"
import { errorMessage } from "../../api/client"
import { notificationSettingsSchema, type NotificationSettingsFormData } from "../../lib/validation"
import { Button } from "../../components/ui/Button"
import { Field, Input, Textarea } from "../../components/ui/Field"
import { Notice } from "../../components/ui/Notice"

const SECTIONS = [
  {
    key: "reminder" as const,
    title: "Reminder",
    description: "Sent automatically before an appointment based on the timing below.",
    fields: [
      { name: "reminder_email_subject" as const, label: "Email subject" },
      { name: "reminder_email_body" as const, label: "Email body", multiline: true },
      { name: "reminder_sms_body" as const, label: "SMS body", multiline: true },
    ],
  },
  {
    key: "confirmation" as const,
    title: "Booking confirmation",
    description: "Sent when a booking is created or confirmed by an organiser.",
    fields: [
      { name: "booking_confirmation_subject" as const, label: "Email subject" },
      { name: "booking_confirmation_body" as const, label: "Email body", multiline: true },
    ],
  },
  {
    key: "cancellation" as const,
    title: "Cancellation",
    description: "Sent when a booking is cancelled.",
    fields: [
      { name: "cancellation_subject" as const, label: "Email subject" },
      { name: "cancellation_body" as const, label: "Email body", multiline: true },
    ],
  },
] as const

function PlaceholderChips({
  placeholders,
  onInsert,
}: {
  placeholders: string[]
  onInsert: (placeholder: string) => void
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {placeholders.map((p) => (
        <button
          key={p}
          type="button"
          onClick={() => onInsert(`{{${p}}}`)}
          className="rounded border border-line bg-white px-2 py-0.5 font-mono text-xs text-neutral-600 hover:border-ink hover:text-ink transition"
          title={`Insert {{${p}}}`}
        >
          {`{{${p}}}`}
        </button>
      ))}
    </div>
  )
}

function TemplateField({
  name,
  label,
  multiline,
  placeholders,
  register,
  error,
  getValues,
  setValue,
}: {
  name: keyof NotificationSettingsFormData
  label: string
  multiline?: boolean
  placeholders: string[]
  register: ReturnType<typeof useForm<NotificationSettingsFormData>>["register"]
  error?: string
  getValues: ReturnType<typeof useForm<NotificationSettingsFormData>>["getValues"]
  setValue: ReturnType<typeof useForm<NotificationSettingsFormData>>["setValue"]
}) {
  const ref = useRef<HTMLTextAreaElement | HTMLInputElement | null>(null)

  function insertPlaceholder(text: string) {
    const el = ref.current
    if (!el) {
      const current = (getValues(name) as string) || ""
      setValue(name as never, (current + text) as never, { shouldValidate: true })
      return
    }
    const start = (el as HTMLInputElement).selectionStart ?? (el as HTMLInputElement).value.length
    const end = (el as HTMLInputElement).selectionEnd ?? start
    const current = (el as HTMLInputElement).value
    const next = current.slice(0, start) + text + current.slice(end)
    setValue(name as never, next as never, { shouldValidate: true })
    setTimeout(() => {
      const newPos = start + text.length
      ;(el as HTMLInputElement).setSelectionRange(newPos, newPos)
      el.focus()
    }, 0)
  }

  const { ref: registerRef, ...rest } = register(name as never)

  return (
    <Field label={label} error={error}>
      <PlaceholderChips placeholders={placeholders} onInsert={insertPlaceholder} />
      {multiline ? (
        <Textarea
          {...rest}
          ref={(el) => {
            registerRef(el)
            ref.current = el
          }}
          rows={5}
          aria-invalid={error ? true : undefined}
          className="font-mono text-xs"
        />
      ) : (
        <Input
          {...rest}
          ref={(el) => {
            registerRef(el)
            ref.current = el
          }}
          type="text"
          aria-invalid={error ? true : undefined}
        />
      )}
    </Field>
  )
}

export function NotificationSettingsPage() {
  const [placeholders, setPlaceholders] = useState<string[]>([])
  const [saved, setSaved] = useState("")
  const [loadError, setLoadError] = useState("")

  const {
    register,
    handleSubmit,
    reset,
    getValues,
    setValue,
    setError,
    clearErrors,
    formState: { errors, isSubmitting },
  } = useForm<NotificationSettingsFormData>({
    resolver: zodResolver(notificationSettingsSchema),
  })

  useEffect(() => {
    Promise.all([getNotificationSettings(), getNotificationPlaceholders()])
      .then(([settings, ph]) => {
        reset({
          reminder_email_hours: settings.reminder_email_hours,
          reminder_sms_hours: settings.reminder_sms_hours,
          email_enabled: settings.email_enabled,
          sms_enabled: settings.sms_enabled,
          sender_name: settings.sender_name,
          reminder_email_subject: settings.reminder_email_subject,
          reminder_email_body: settings.reminder_email_body,
          reminder_sms_body: settings.reminder_sms_body,
          booking_confirmation_subject: settings.booking_confirmation_subject,
          booking_confirmation_body: settings.booking_confirmation_body,
          cancellation_subject: settings.cancellation_subject,
          cancellation_body: settings.cancellation_body,
        })
        setPlaceholders(ph)
      })
      .catch((err) => setLoadError(errorMessage(err)))
  }, [reset])

  async function submit(data: NotificationSettingsFormData) {
    clearErrors("root" as never)
    setSaved("")
    try {
      await updateNotificationSettings(data)
      setSaved("Settings saved.")
      setTimeout(() => setSaved(""), 4000)
    } catch (err) {
      setError("root" as never, { message: errorMessage(err) })
    }
  }

  if (loadError) {
    return (
      <section className="space-y-4">
        <Notice tone="error">{loadError}</Notice>
      </section>
    )
  }

  return (
    <form className="space-y-6" onSubmit={handleSubmit(submit)} noValidate>
      <div>
        <h1 className="text-2xl font-bold text-ink">Email &amp; SMS Settings</h1>
        <p className="mt-1 text-sm text-neutral-600">
          Customise reminder timing and message templates. Use{" "}
          <code className="rounded bg-neutral-100 px-1 font-mono text-xs">{"{{placeholder}}"}</code>{" "}
          chips to insert dynamic values.
        </p>
      </div>

      {(errors as { root?: { message?: string } }).root && (
        <Notice tone="error">{(errors as { root?: { message?: string } }).root?.message}</Notice>
      )}
      {saved && <Notice tone="success">{saved}</Notice>}

      {/* Timing & channels */}
      <div className="rounded-2xl border border-line bg-white p-5 shadow-sm space-y-4">
        <h2 className="text-base font-bold text-ink">Reminder timing</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Email reminder — hours before appointment" error={errors.reminder_email_hours?.message}>
            <Input
              {...register("reminder_email_hours")}
              type="number"
              min={0}
              max={720}
              aria-invalid={errors.reminder_email_hours ? true : undefined}
            />
          </Field>
          <Field label="SMS reminder — hours before appointment" error={errors.reminder_sms_hours?.message}>
            <Input
              {...register("reminder_sms_hours")}
              type="number"
              min={0}
              max={720}
              aria-invalid={errors.reminder_sms_hours ? true : undefined}
            />
          </Field>
        </div>
        <Field label="Sender display name" error={errors.sender_name?.message}>
          <Input
            {...register("sender_name")}
            type="text"
            aria-invalid={errors.sender_name ? true : undefined}
          />
        </Field>
        <div className="flex flex-wrap gap-6">
          <label className="flex cursor-pointer items-center gap-2 text-sm font-semibold">
            <input {...register("email_enabled")} type="checkbox" className="h-4 w-4 rounded border-line accent-ink" />
            Enable email notifications
          </label>
          <label className="flex cursor-pointer items-center gap-2 text-sm font-semibold">
            <input {...register("sms_enabled")} type="checkbox" className="h-4 w-4 rounded border-line accent-ink" />
            Enable SMS notifications
          </label>
        </div>
      </div>

      {/* Template sections */}
      {SECTIONS.map((section) => (
        <div key={section.key} className="rounded-2xl border border-line bg-white p-5 shadow-sm space-y-4">
          <div>
            <h2 className="text-base font-bold text-ink">{section.title}</h2>
            <p className="text-xs text-neutral-500">{section.description}</p>
          </div>
          {section.fields.map((field) => (
            <TemplateField
              key={field.name}
              name={field.name}
              label={field.label}
              multiline={"multiline" in field ? field.multiline : false}
              placeholders={placeholders}
              register={register}
              error={errors[field.name]?.message}
              getValues={getValues}
              setValue={setValue}
            />
          ))}
        </div>
      ))}

      <Button type="submit" className="h-11 px-8" disabled={isSubmitting}>
        {isSubmitting ? "Saving…" : "Save settings"}
      </Button>
    </form>
  )
}

import {
  BtnBold,
  BtnBulletList,
  BtnItalic,
  BtnLink,
  BtnNumberedList,
  BtnRedo,
  BtnUnderline,
  BtnUndo,
  Editor,
  EditorProvider,
  Separator,
  Toolbar,
} from "react-simple-wysiwyg"
import { Eye, RotateCcw, Save } from "lucide-react"
import { useEffect, useMemo, useRef, useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"

import { errorMessage } from "../../api/client"
import {
  createMailTemplate,
  getMailTemplate,
  getTemplatePlaceholders,
  previewMailTemplate,
  resetMailTemplate,
  updateMailTemplate,
  type MailTemplate,
  type TemplateType,
} from "../../api/mailTemplates"
import { Button } from "../../components/ui/Button"
import { Field, Input, Select, Textarea } from "../../components/ui/Field"
import { Notice } from "../../components/ui/Notice"
import { MailTemplatePreviewModal } from "./MailTemplatePreviewModal"

const TEMPLATE_TYPES: Array<{ value: TemplateType; label: string }> = [
  { value: "booking_confirmation", label: "Booking Confirmation" },
  { value: "cancellation", label: "Cancellation" },
  { value: "reminder_email", label: "Reminder Email" },
  { value: "reminder_sms", label: "Reminder SMS" },
]

export function MailTemplateEditPage() {
  const { templateId } = useParams()
  const navigate = useNavigate()
  const isNew = templateId === "new" || !templateId
  const subjectRef = useRef<HTMLInputElement>(null)

  const [template, setTemplate] = useState<MailTemplate | null>(null)
  const [templateType, setTemplateType] = useState<TemplateType>("booking_confirmation")
  const [name, setName] = useState("")
  const [subject, setSubject] = useState("")
  const [bodyHtml, setBodyHtml] = useState("")
  const [description, setDescription] = useState("")
  const [tab, setTab] = useState<"body" | "options">("body")
  const [placeholders, setPlaceholders] = useState<string[]>([])
  const [message, setMessage] = useState("")
  const [saving, setSaving] = useState(false)
  const [preview, setPreview] = useState<{ subject: string | null; body_html: string } | null>(null)

  const canEdit = isNew || Boolean(template?.can_edit)
  const title = useMemo(() => name || "New Template", [name])

  useEffect(() => {
    getTemplatePlaceholders().then(setPlaceholders).catch(() => setPlaceholders([]))
  }, [])

  useEffect(() => {
    if (isNew || !templateId) return
    getMailTemplate(templateId)
      .then((data) => {
        setTemplate(data)
        setTemplateType(data.template_type)
        setName(data.name)
        setSubject(data.subject || "")
        setBodyHtml(data.body_html)
        setDescription(data.description || "")
      })
      .catch((err) => setMessage(errorMessage(err)))
  }, [isNew, templateId])

  function insertIntoSubject(token: string) {
    const el = subjectRef.current
    if (!el) {
      setSubject((current) => `${current}${token}`)
      return
    }
    const start = el.selectionStart ?? subject.length
    const end = el.selectionEnd ?? start
    const next = subject.slice(0, start) + token + subject.slice(end)
    setSubject(next)
    setTimeout(() => {
      const pos = start + token.length
      el.setSelectionRange(pos, pos)
      el.focus()
    }, 0)
  }

  async function save() {
    setSaving(true)
    setMessage("")
    try {
      const payload = {
        template_type: templateType,
        name,
        subject: templateType === "reminder_sms" ? null : subject,
        body_html: bodyHtml,
        description,
      }
      const saved = isNew || !templateId ? await createMailTemplate(payload) : await updateMailTemplate(templateId, payload)
      setTemplate(saved)
      setMessage("Template saved.")
      if (isNew) navigate(`/organiser/mail-templates/${saved.id}`, { replace: true })
    } catch (err) {
      setMessage(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function previewTemplate() {
    if (!templateId || isNew) return
    try {
      setPreview(await previewMailTemplate(templateId))
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  async function resetTemplate() {
    if (!templateId || isNew) return
    try {
      const reset = await resetMailTemplate(templateId)
      setTemplate(reset)
      setSubject(reset.subject || "")
      setBodyHtml(reset.body_html)
      setDescription(reset.description || "")
      setMessage("Template reset to the system default.")
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-neutral-600">
            <Link to="/organiser/mail-templates" className="text-signal hover:underline">Templates</Link>
            <span> / {title}</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold text-ink">{title}</h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="secondary" onClick={previewTemplate} disabled={isNew}>
            <Eye size={16} />
            Preview
          </Button>
          {template?.can_edit && (
            <Button type="button" variant="secondary" onClick={resetTemplate}>
              <RotateCcw size={16} />
              Reset Template
            </Button>
          )}
        </div>
      </div>

      {message && <Notice tone={message.includes("saved") || message.includes("reset") ? "success" : "error"}>{message}</Notice>}
      {!canEdit && <Notice>System defaults are read-only. Create a custom template to edit the content.</Notice>}

      <div className="rounded-md border border-line bg-white">
        <div className="grid gap-4 border-b border-line p-5 md:grid-cols-2">
          {isNew && (
            <Field label="Template Type">
              <Select value={templateType} onChange={(event) => setTemplateType(event.target.value as TemplateType)}>
                {TEMPLATE_TYPES.map((item) => (
                  <option key={item.value} value={item.value}>{item.label}</option>
                ))}
              </Select>
            </Field>
          )}
          <Field label="Template Name">
            <Input value={name} onChange={(event) => setName(event.target.value)} disabled={!canEdit} />
          </Field>
          {templateType !== "reminder_sms" && (
            <Field label="Subject">
              <PlaceholderChips placeholders={placeholders} onInsert={insertIntoSubject} />
              <Input ref={subjectRef} value={subject} onChange={(event) => setSubject(event.target.value)} disabled={!canEdit} />
            </Field>
          )}
        </div>

        <div className="flex border-b border-line">
          <button
            type="button"
            onClick={() => setTab("body")}
            className={`px-5 py-3 text-sm font-bold ${tab === "body" ? "border-t-4 border-ink text-ink" : "text-neutral-600"}`}
          >
            Body
          </button>
          <button
            type="button"
            onClick={() => setTab("options")}
            className={`px-5 py-3 text-sm font-bold ${tab === "options" ? "border-t-4 border-ink text-ink" : "text-neutral-600"}`}
          >
            Options
          </button>
        </div>

        {tab === "body" ? (
          <div className="space-y-3 p-5">
            <PlaceholderChips placeholders={placeholders} onInsert={(token) => setBodyHtml((current) => `${current}${token}`)} />
            <EditorProvider>
              <div className="overflow-hidden rounded-md border border-line bg-white">
                <Toolbar>
                  <BtnBold />
                  <BtnItalic />
                  <BtnUnderline />
                  <Separator />
                  <BtnNumberedList />
                  <BtnBulletList />
                  <Separator />
                  <BtnLink />
                  <BtnUndo />
                  <BtnRedo />
                </Toolbar>
                <Editor value={bodyHtml} onChange={(event) => setBodyHtml(event.target.value)} disabled={!canEdit} />
              </div>
            </EditorProvider>
          </div>
        ) : (
          <div className="grid gap-4 p-5">
            <Field label="Description">
              <Textarea value={description} onChange={(event) => setDescription(event.target.value)} disabled={!canEdit} />
            </Field>
            <Field label="Owner">
              <Input value="Shared with all users" readOnly />
            </Field>
            <div className="rounded-md border border-dashed border-line p-4 text-sm text-neutral-600">Attachments can be added in a future update.</div>
          </div>
        )}
      </div>

      <Button type="button" onClick={save} disabled={!canEdit || saving || !name.trim() || !bodyHtml.trim()}>
        <Save size={16} />
        {saving ? "Saving..." : "Save changes"}
      </Button>
      <MailTemplatePreviewModal
        open={Boolean(preview)}
        subject={preview?.subject || null}
        bodyHtml={preview?.body_html || ""}
        onClose={() => setPreview(null)}
      />
    </section>
  )
}

function PlaceholderChips({ placeholders, onInsert }: { placeholders: string[]; onInsert: (token: string) => void }) {
  return (
    <div className="mb-2 flex flex-wrap gap-1.5">
      {placeholders.map((placeholder) => (
        <button
          key={placeholder}
          type="button"
          onClick={() => onInsert(`{{${placeholder}}}`)}
          className="rounded border border-line bg-paper px-2 py-0.5 font-mono text-xs text-neutral-700 hover:border-ink hover:text-ink"
        >
          {`{{${placeholder}}}`}
        </button>
      ))}
    </div>
  )
}

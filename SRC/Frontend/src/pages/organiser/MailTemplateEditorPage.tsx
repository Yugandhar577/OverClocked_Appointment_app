import { Eye, Link as LinkIcon, List, Redo2, Save, Undo2, X } from "lucide-react"
import { useMemo, useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"

import { Button } from "../../components/ui/Button"
import {
  createMailTemplate,
  getMailTemplate,
  renderTemplate,
  saveMailTemplate,
  templateTokens,
  type MailTemplateType,
} from "../../lib/mailTemplates"

const typeOptions: Array<{ value: MailTemplateType; label: string }> = [
  { value: "booking", label: "Booking Confirmation" },
  { value: "cancellation", label: "Cancellation" },
  { value: "email_reminder", label: "Email Reminder" },
  { value: "sms_reminder", label: "SMS Reminder" },
]

export function MailTemplateEditorPage() {
  const navigate = useNavigate()
  const { templateId } = useParams()
  const existing = templateId && templateId !== "new" ? getMailTemplate(templateId) : undefined
  const isNew = !existing
  const [name, setName] = useState(existing?.name ?? "")
  const [type, setType] = useState<MailTemplateType>(existing?.type ?? "booking")
  const [subject, setSubject] = useState(existing?.subject ?? "")
  const [body, setBody] = useState(existing?.body ?? "")
  const [activeTab, setActiveTab] = useState<"body" | "options">("body")
  const [showPreview, setShowPreview] = useState(false)

  const previewSubject = useMemo(() => renderTemplate(subject || "Booking confirmed: {{appointment_type}}"), [subject])
  const previewBody = useMemo(() => renderTemplate(body || "Hi {{customer_name}}, your booking is confirmed."), [body])

  function appendToken(token: string, target: "subject" | "body") {
    if (target === "subject") setSubject((current) => `${current}${current ? " " : ""}${token}`)
    else setBody((current) => `${current}${current ? " " : ""}${token}`)
  }

  function save() {
    if (existing) {
      saveMailTemplate({
        ...existing,
        name,
        type,
        subject,
        body,
        updated_at: new Date().toISOString(),
        source: existing.source === "System" ? "Custom" : existing.source,
      })
      navigate(`/organiser/mail-templates/${existing.id}`)
      return
    }
    const created = createMailTemplate({
      name: name || "New Template",
      type,
      subject,
      body,
    })
    navigate(`/organiser/mail-templates/${created.id}`)
  }

  return (
    <div className="grid gap-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-semibold">
            <Link to="/organiser/mail-templates" className="text-blue-700 hover:underline">Templates</Link>
            <span className="text-neutral-500"> / {isNew ? "New Template" : name || existing?.name}</span>
          </p>
          <h1 className="text-2xl font-bold text-ink">{isNew ? "New Template" : existing?.name}</h1>
        </div>
        <Button type="button" variant="secondary" onClick={() => setShowPreview(true)}>
          <Eye size={16} />
          Preview
        </Button>
      </div>

      {!isNew && existing?.source === "System" && (
        <div className="rounded-md border border-line bg-white px-4 py-3 text-sm text-neutral-700">
          System defaults are read-only. Saving creates a custom editable version for your workspace.
        </div>
      )}

      <section className="overflow-hidden rounded-md border border-line bg-white">
        <div className="grid gap-4 p-4 md:grid-cols-2">
          <label className="grid gap-2 text-sm font-bold text-ink">
            {isNew ? "Template Type" : "Template Name"}
            {isNew ? (
              <select value={type} onChange={(event) => setType(event.target.value as MailTemplateType)} className="focus-ring h-10 rounded-md border border-line bg-white px-3 font-normal">
                {typeOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            ) : (
              <input value={name} onChange={(event) => setName(event.target.value)} className="focus-ring h-10 rounded-md border border-line bg-white px-3 font-normal" />
            )}
          </label>
          <label className="grid gap-2 text-sm font-bold text-ink">
            {isNew ? "Template Name" : "Subject"}
            {isNew ? (
              <input value={name} onChange={(event) => setName(event.target.value)} className="focus-ring h-10 rounded-md border border-line bg-white px-3 font-normal" />
            ) : (
              <div className="grid gap-2">
                <TokenRow target="subject" onInsert={appendToken} />
                <input value={subject} onChange={(event) => setSubject(event.target.value)} className="focus-ring h-10 rounded-md border border-line bg-white px-3 font-normal" />
              </div>
            )}
          </label>
          {isNew && (
            <label className="grid gap-2 text-sm font-bold text-ink md:col-span-1">
              Subject
              <TokenRow target="subject" onInsert={appendToken} />
              <input value={subject} onChange={(event) => setSubject(event.target.value)} className="focus-ring h-10 rounded-md border border-line bg-white px-3 font-normal" />
            </label>
          )}
        </div>

        <div className="border-t border-line">
          <div className="flex">
            <button type="button" onClick={() => setActiveTab("body")} className={`border-r border-line px-4 py-3 text-sm font-bold ${activeTab === "body" ? "border-t-4 border-t-ink bg-white" : "bg-paper text-neutral-700"}`}>
              Body
            </button>
            <button type="button" onClick={() => setActiveTab("options")} className={`border-r border-line px-4 py-3 text-sm font-bold ${activeTab === "options" ? "border-t-4 border-t-ink bg-white" : "bg-paper text-neutral-700"}`}>
              Options
            </button>
          </div>
          {activeTab === "body" ? (
            <div className="grid gap-3 p-4">
              <TokenRow target="body" onInsert={appendToken} />
              <div className="overflow-hidden rounded-md border border-line bg-white">
                <div className="flex items-center gap-3 border-b border-line bg-neutral-100 px-3 py-2">
                  <b>B</b>
                  <i>I</i>
                  <u>U</u>
                  <List size={16} />
                  <List size={16} />
                  <LinkIcon size={16} className="text-signal" />
                  <Undo2 size={15} />
                  <Redo2 size={15} />
                </div>
                <textarea value={body} onChange={(event) => setBody(event.target.value)} className="min-h-32 w-full resize-y border-0 bg-white p-3 outline-none" />
              </div>
            </div>
          ) : (
            <div className="grid gap-3 p-4 text-sm text-neutral-700">
              <label className="flex items-center gap-2">
                <input type="checkbox" defaultChecked />
                Send automatically when this workflow runs
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" defaultChecked />
                Log each dispatch in the appointment chatter
              </label>
            </div>
          )}
        </div>
      </section>

      <Button type="button" onClick={save} className="w-fit">
        <Save size={16} />
        Save changes
      </Button>

      {showPreview && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
          <section className="w-full max-w-2xl overflow-hidden rounded-md border border-line bg-white shadow-panel">
            <div className="flex items-start justify-between border-b border-line px-5 py-4">
              <div>
                <p className="text-xs font-bold uppercase text-neutral-600">Preview</p>
                <h2 className="text-lg font-bold text-ink">{previewSubject}</h2>
              </div>
              <button type="button" onClick={() => setShowPreview(false)} className="focus-ring rounded-md p-1">
                <X size={18} />
              </button>
            </div>
            <pre className="m-5 whitespace-pre-wrap rounded-md border border-line bg-white p-4 font-sans text-sm leading-6 text-ink">{previewBody}</pre>
          </section>
        </div>
      )}
    </div>
  )
}

function TokenRow({ target, onInsert }: { target: "subject" | "body"; onInsert: (token: string, target: "subject" | "body") => void }) {
  return (
    <div className="flex flex-wrap gap-1">
      {templateTokens.map((token) => (
        <button key={`${target}-${token}`} type="button" onClick={() => onInsert(token, target)} className="rounded border border-line bg-paper px-2 py-1 font-mono text-xs text-neutral-700 hover:bg-white">
          {token}
        </button>
      ))}
    </div>
  )
}

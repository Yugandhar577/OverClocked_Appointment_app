import { Plus } from "lucide-react"
import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"

import { errorMessage } from "../../api/client"
import { listMailTemplates, type MailTemplate } from "../../api/mailTemplates"
import { Button } from "../../components/ui/Button"
import { Notice } from "../../components/ui/Notice"

const TYPE_LABELS: Record<string, string> = {
  booking_confirmation: "Booking",
  cancellation: "Cancellation",
  reminder_email: "Email reminder",
  reminder_sms: "SMS reminder",
}

export function MailTemplatesListPage() {
  const navigate = useNavigate()
  const [templates, setTemplates] = useState<MailTemplate[]>([])
  const [message, setMessage] = useState("")

  useEffect(() => {
    listMailTemplates()
      .then(setTemplates)
      .catch((err) => setMessage(errorMessage(err)))
  }, [])

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-ink">Email Templates</h1>
          <p className="text-sm text-neutral-600">System defaults and custom templates used by appointment types.</p>
        </div>
        <Button type="button" onClick={() => navigate("/organiser/mail-templates/new")}>
          <Plus size={16} />
          New template
        </Button>
      </div>
      {message && <Notice tone="error">{message}</Notice>}
      <div className="overflow-hidden rounded-md border border-line bg-white">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="border-b border-line bg-paper">
            <tr>
              <th className="px-4 py-3 font-bold">Name</th>
              <th className="px-4 py-3 font-bold">Type</th>
              <th className="px-4 py-3 font-bold">Source</th>
              <th className="px-4 py-3 font-bold">Updated</th>
            </tr>
          </thead>
          <tbody>
            {templates.map((template) => (
              <tr
                key={template.id}
                className="cursor-pointer border-b border-line last:border-b-0 hover:bg-paper"
                onClick={() => navigate(`/organiser/mail-templates/${template.id}`)}
              >
                <td className="px-4 py-3 font-semibold text-ink">{template.name}</td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-paper px-2 py-1 text-xs font-bold text-neutral-700">
                    {TYPE_LABELS[template.template_type] || template.template_type}
                  </span>
                </td>
                <td className="px-4 py-3">{template.is_system_default ? "System" : "Custom"}</td>
                <td className="px-4 py-3 text-neutral-600">{new Date(template.updated_at).toLocaleString()}</td>
              </tr>
            ))}
            {templates.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-neutral-500">
                  No templates found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}

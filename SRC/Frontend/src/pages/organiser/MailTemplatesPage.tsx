import { Plus } from "lucide-react"
import { Link } from "react-router-dom"

import { Button } from "../../components/ui/Button"
import { listMailTemplates, templateTypeLabel } from "../../lib/mailTemplates"

export function MailTemplatesPage() {
  const templates = listMailTemplates()

  return (
    <div className="grid gap-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ink">Email Templates</h1>
          <p className="text-sm text-neutral-700">System defaults and custom templates used by appointment types.</p>
        </div>
        <Link to="/organiser/mail-templates/new">
          <Button type="button">
            <Plus size={16} />
            New template
          </Button>
        </Link>
      </div>

      <section className="overflow-hidden rounded-md border border-line bg-white">
        <table className="w-full border-collapse text-left">
          <thead className="bg-paper">
            <tr className="text-sm text-ink">
              <th className="px-4 py-3 font-bold">Name</th>
              <th className="px-4 py-3 font-bold">Type</th>
              <th className="px-4 py-3 font-bold">Source</th>
              <th className="px-4 py-3 font-bold">Updated</th>
            </tr>
          </thead>
          <tbody>
            {templates.map((template) => (
              <tr key={template.id} className="border-t border-line hover:bg-paper/70">
                <td className="px-4 py-3">
                  <Link to={`/organiser/mail-templates/${template.id}`} className="font-semibold text-ink hover:text-signal">
                    {template.name}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-paper px-2 py-1 text-xs font-bold text-neutral-700">
                    {templateTypeLabel(template.type)}
                  </span>
                </td>
                <td className="px-4 py-3 text-neutral-700">{template.source}</td>
                <td className="px-4 py-3 text-neutral-700">{new Date(template.updated_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}

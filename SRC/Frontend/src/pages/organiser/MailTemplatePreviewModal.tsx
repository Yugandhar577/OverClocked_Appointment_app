import { X } from "lucide-react"

import { Button } from "../../components/ui/Button"

export function MailTemplatePreviewModal({
  open,
  subject,
  bodyHtml,
  onClose,
}: {
  open: boolean
  subject: string | null
  bodyHtml: string
  onClose: () => void
}) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/30 p-4">
      <div className="w-full max-w-2xl rounded-md border border-line bg-white shadow-panel">
        <div className="flex items-center justify-between border-b border-line px-5 py-3">
          <div>
            <p className="text-xs font-bold uppercase text-neutral-500">Preview</p>
            <h2 className="text-lg font-bold text-ink">{subject || "(no subject)"}</h2>
          </div>
          <Button type="button" variant="ghost" onClick={onClose} title="Close">
            <X size={18} />
          </Button>
        </div>
        <div className="max-h-[70vh] overflow-auto bg-paper p-5">
          <div
            className="rounded-md border border-line bg-white p-5 text-sm leading-6 text-ink"
            dangerouslySetInnerHTML={{ __html: bodyHtml.replace(/\n/g, "<br />") }}
          />
        </div>
      </div>
    </div>
  )
}

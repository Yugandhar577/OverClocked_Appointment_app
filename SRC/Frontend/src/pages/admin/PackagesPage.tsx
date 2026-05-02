import { useEffect, useState, type FormEvent } from "react"

import { createPackage, listPackages, type PackagePlan } from "../../api/advanced"
import { errorMessage } from "../../api/client"
import { Button } from "../../components/ui/Button"
import { Notice } from "../../components/ui/Notice"

export function PackagesPage() {
  const [packages, setPackages] = useState<PackagePlan[]>([])
  const [name, setName] = useState("")
  const [sessions, setSessions] = useState(5)
  const [price, setPrice] = useState(0)
  const [error, setError] = useState("")

  function load() {
    listPackages().then(setPackages).catch((err) => setError(errorMessage(err)))
  }

  useEffect(load, [])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError("")
    try {
      await createPackage({ name, session_count: sessions, price, currency: "INR" })
      setName("")
      setSessions(5)
      setPrice(0)
      load()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  return (
    <section className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-ink">Packages</h1>
        <p className="text-sm text-neutral-600">Create recurring appointment packages and session bundles.</p>
      </div>
      {error && <Notice tone="error">{error}</Notice>}
      <form onSubmit={submit} className="odoo-surface grid gap-3 p-4 md:grid-cols-4">
        <input className="h-10 rounded border border-line px-3" placeholder="Package name" value={name} onChange={(event) => setName(event.target.value)} required />
        <input className="h-10 rounded border border-line px-3" type="number" min={1} value={sessions} onChange={(event) => setSessions(Number(event.target.value))} />
        <input className="h-10 rounded border border-line px-3" type="number" min={0} value={price} onChange={(event) => setPrice(Number(event.target.value))} />
        <Button type="submit">Create package</Button>
      </form>
      <div className="odoo-surface divide-y divide-[var(--odoo-border)]">
        {packages.map((item) => (
          <div key={item.id} className="flex items-center justify-between p-4 text-sm">
            <div>
              <strong>{item.name}</strong>
              <div className="text-neutral-500">{item.session_count} sessions</div>
            </div>
            <div className="font-semibold">{item.currency} {item.price}</div>
          </div>
        ))}
        {packages.length === 0 && <p className="p-4 text-sm text-neutral-500">No packages created yet.</p>}
      </div>
    </section>
  )
}

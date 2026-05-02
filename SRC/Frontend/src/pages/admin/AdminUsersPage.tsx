import { Power, ShieldCheck } from "lucide-react"
import { useEffect, useState } from "react"

import { activateUser, deactivateUser, listUsers, updateUserRoles } from "../../api/admin"
import { errorMessage } from "../../api/client"
import type { AdminUser } from "../../api/types"
import { Button } from "../../components/ui/Button"
import { Notice } from "../../components/ui/Notice"

export function AdminUsersPage() {
  const [items, setItems] = useState<AdminUser[]>([])
  const [message, setMessage] = useState("")

  function load() {
    listUsers()
      .then((data) => setItems(data.items))
      .catch((err) => setMessage(errorMessage(err)))
  }

  useEffect(load, [])

  async function toggle(user: AdminUser) {
    try {
      if (user.is_active) await deactivateUser(user.id)
      else await activateUser(user.id)
      load()
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  async function makeOrganiser(user: AdminUser) {
    try {
      const roles = Array.from(new Set([...user.roles, "organiser"]))
      await updateUserRoles(user.id, roles)
      load()
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  return (
    <div className="grid gap-5">
      <h1 className="border-b border-line pb-4 text-3xl font-bold text-ink">Users</h1>
      {message && <Notice>{message}</Notice>}
      <div className="overflow-hidden rounded-md border border-line bg-paper">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="bg-white">
            <tr>
              <Th>User</Th>
              <Th>Roles</Th>
              <Th>Status</Th>
              <Th>Actions</Th>
            </tr>
          </thead>
          <tbody>
            {items.map((user) => (
              <tr key={user.id} className="border-t border-line">
                <Td>
                  <div className="font-semibold">{user.full_name}</div>
                  <div className="text-xs text-neutral-600">{user.email}</div>
                </Td>
                <Td>{user.roles.join(", ")}</Td>
                <Td>{user.is_active ? "Active" : "Inactive"}</Td>
                <Td>
                  <div className="flex gap-2">
                    <Button variant="secondary" onClick={() => makeOrganiser(user)}>
                      <ShieldCheck size={16} />
                    </Button>
                    <Button variant={user.is_active ? "danger" : "secondary"} onClick={() => toggle(user)}>
                      <Power size={16} />
                    </Button>
                  </div>
                </Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 font-bold">{children}</th>
}

function Td({ children }: { children: React.ReactNode }) {
  return <td className="px-4 py-3">{children}</td>
}

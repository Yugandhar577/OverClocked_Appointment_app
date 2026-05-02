import { Navigate, Outlet, useLocation } from "react-router-dom"

import { useAuth } from "../../auth/useAuth"
import { Notice } from "../ui/Notice"

export function RequireAuth({ roles }: { roles?: string[] }) {
  const auth = useAuth()
  const location = useLocation()
  if (auth.loading) return <Notice>Loading session...</Notice>
  if (!auth.user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (roles && !auth.hasRole(...roles)) return <Notice tone="error">Access denied.</Notice>
  return <Outlet />
}

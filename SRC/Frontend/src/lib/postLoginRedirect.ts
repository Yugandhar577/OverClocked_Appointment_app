/** First route after password login, when no `from` path is provided. */
export function defaultRouteForRoles(roles: string[]) {
  if (roles.includes("admin")) return "/admin"
  if (roles.includes("organiser")) return "/organiser/types"
  return "/"
}

export function canUseRequestedRoute(roles: string[], route?: string) {
  if (!route) return false
  if (roles.includes("admin")) return route.startsWith("/admin")
  if (roles.includes("organiser")) return route.startsWith("/organiser") || route === "/admin"
  return !route.startsWith("/admin") && !route.startsWith("/organiser")
}

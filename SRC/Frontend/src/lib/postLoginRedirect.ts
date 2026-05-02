/** First route after password login, when no `from` path is provided. */
export function defaultRouteForRoles(roles: string[]) {
  if (roles.includes("admin")) return "/admin"
  if (roles.includes("organiser")) return "/organiser/types"
  return "/"
}

import type { NavigateFunction } from "react-router-dom"

export function slideNavigate(navigate: NavigateFunction, to: string, options?: { replace?: boolean }) {
  const run = () => navigate(to, options)
  const viewDocument = document as Document & { startViewTransition?: (callback: () => void) => void }
  if (viewDocument.startViewTransition) {
    viewDocument.startViewTransition(run)
    return
  }
  document.documentElement.classList.add("route-slide-out")
  window.setTimeout(() => {
    run()
    document.documentElement.classList.remove("route-slide-out")
  }, 220)
}

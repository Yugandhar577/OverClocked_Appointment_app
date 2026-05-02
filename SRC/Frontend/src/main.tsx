import React from "react"
import ReactDOM from "react-dom/client"
import { BrowserRouter } from "react-router-dom"
import { GoogleOAuthProvider } from "@react-oauth/google"

import { App } from "./App"
import { AuthProvider } from "./auth/AuthContext"
import { ThemeProvider } from "./auth/ThemeProvider"
import "./styles/index.css"

const googleClientId = (import.meta.env.VITE_GOOGLE_CLIENT_ID ?? "").trim()

const appTree = (
  <BrowserRouter>
    <AuthProvider>
      <ThemeProvider>
        <App />
      </ThemeProvider>
    </AuthProvider>
  </BrowserRouter>
)

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {googleClientId ? <GoogleOAuthProvider clientId={googleClientId}>{appTree}</GoogleOAuthProvider> : appTree}
  </React.StrictMode>,
)

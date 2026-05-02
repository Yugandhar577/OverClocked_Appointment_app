import { zodResolver } from "@hookform/resolvers/zod"
import { GoogleLogin } from "@react-oauth/google"
import { useForm } from "react-hook-form"
import { Link, useLocation, useNavigate } from "react-router-dom"

import { googleLogin } from "../../api/auth"
import { errorMessage } from "../../api/client"
import { useAuth } from "../../auth/useAuth"
import { defaultRouteForRoles } from "../../lib/postLoginRedirect"
import { loginSchema, type LoginFormData } from "../../lib/validation"
import { Button } from "../../components/ui/Button"
import { Field, Input } from "../../components/ui/Field"
import { Notice } from "../../components/ui/Notice"

const demoAccounts = [
  { label: "Customer", email: "cust1@test.local", password: "Customer123!" },
  { label: "Organiser", email: "org1@test.local", password: "Organiser123!" },
  { label: "Admin", email: "admin@test.local", password: "Admin123!" },
]

export function LoginPage() {
  const auth = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const {
    register,
    handleSubmit,
    setValue,
    setError,
    clearErrors,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "cust1@test.local", password: "Customer123!" },
  })

  function getRedirect(roles: string[]) {
    return (location.state as { from?: string } | null)?.from ?? defaultRouteForRoles(roles)
  }

  async function submit(data: LoginFormData) {
    clearErrors("root")
    try {
      const user = await auth.login(data.email, data.password)
      navigate(getRedirect(user.roles))
    } catch (err) {
      setError("root", { message: errorMessage(err) })
    }
  }

  async function handleGoogleSuccess(credential: string) {
    clearErrors("root")
    try {
      const res = await googleLogin(credential)
      localStorage.setItem("access_token", res.access_token)
      await auth.refresh()
      navigate(getRedirect(res.user.roles))
    } catch (err) {
      setError("root", { message: errorMessage(err) })
    }
  }

  return (
    <div className="grid gap-4">
      {errors.root && <Notice tone="error">{errors.root.message}</Notice>}

      {/* Demo quick-fill buttons */}
      <div className="grid grid-cols-3 gap-2">
        {demoAccounts.map((account) => (
          <button
            key={account.label}
            type="button"
            onClick={() => {
              setValue("email", account.email, { shouldValidate: false })
              setValue("password", account.password, { shouldValidate: false })
              clearErrors()
            }}
            className="focus-ring rounded-md border border-line bg-white px-3 py-2 text-xs font-bold text-ink hover:border-ink"
          >
            {account.label}
          </button>
        ))}
      </div>

      <form className="grid gap-4" onSubmit={handleSubmit(submit)} noValidate>
        <Field label="Email" error={errors.email?.message}>
          <Input
            {...register("email")}
            type="email"
            autoComplete="email"
            aria-invalid={errors.email ? true : undefined}
          />
        </Field>
        <Field label="Password" error={errors.password?.message}>
          <Input
            {...register("password")}
            type="password"
            autoComplete="current-password"
            aria-invalid={errors.password ? true : undefined}
          />
        </Field>
        <Button disabled={isSubmitting}>{isSubmitting ? "Logging in…" : "Login"}</Button>
      </form>

      <div className="relative flex items-center gap-3">
        <div className="h-px flex-1 bg-line" />
        <span className="text-xs text-neutral-400">or continue with</span>
        <div className="h-px flex-1 bg-line" />
      </div>

      <div className="flex justify-center">
        <GoogleLogin
          onSuccess={(res) => {
            if (res.credential) handleGoogleSuccess(res.credential)
          }}
          onError={() => setError("root", { message: "Google sign-in failed. Please try again." })}
          text="signin_with"
          shape="rectangular"
          theme="outline"
          size="large"
          width="368"
        />
      </div>

      <p className="text-sm text-neutral-700">
        New here?{" "}
        <Link className="font-semibold text-signal" to="/signup">
          Create an account
        </Link>
      </p>
    </div>
  )
}

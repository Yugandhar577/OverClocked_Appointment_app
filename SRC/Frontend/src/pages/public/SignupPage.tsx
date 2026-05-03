import { zodResolver } from "@hookform/resolvers/zod"
import { GoogleLogin } from "@react-oauth/google"
import { useForm } from "react-hook-form"
import { Link, useNavigate } from "react-router-dom"

import { googleLogin, signup } from "../../api/auth"
import { errorMessage } from "../../api/client"
import { useAuth } from "../../auth/useAuth"
import { defaultRouteForRoles } from "../../lib/postLoginRedirect"
import { slideNavigate } from "../../lib/routeTransition"
import { signupSchema, type SignupFormData } from "../../lib/validation"
import { Button } from "../../components/ui/Button"
import { Field, Input } from "../../components/ui/Field"
import { Notice } from "../../components/ui/Notice"

const googleClientId = (import.meta.env.VITE_GOOGLE_CLIENT_ID ?? "").trim()

export function SignupPage() {
  const navigate = useNavigate()
  const auth = useAuth()

  const {
    register,
    handleSubmit,
    setError,
    clearErrors,
    formState: { errors, isSubmitting },
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
  })

  async function submit(data: SignupFormData) {
    clearErrors("root")
    try {
      await signup(data.fullName, data.email, data.password)
      slideNavigate(navigate, `/otp?email=${encodeURIComponent(data.email)}`)
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
      slideNavigate(navigate, defaultRouteForRoles(res.user.roles))
    } catch (err) {
      setError("root", { message: errorMessage(err) })
    }
  }

  return (
    <div className="grid gap-4">
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-neutral-500">New workspace</p>
        <h2 className="mt-2 text-3xl font-black text-ink">Create your account</h2>
        <p className="mt-2 text-sm text-neutral-600">Verify your email, then start managing appointments.</p>
      </div>

      {errors.root && <Notice tone="error">{errors.root.message}</Notice>}

      <form className="grid gap-4" onSubmit={handleSubmit(submit)} noValidate>
        <Field label="Full name" error={errors.fullName?.message}>
          <Input {...register("fullName")} autoComplete="name" aria-invalid={errors.fullName ? true : undefined} />
        </Field>
        <Field label="Email" error={errors.email?.message}>
          <Input {...register("email")} type="email" autoComplete="email" aria-invalid={errors.email ? true : undefined} />
        </Field>
        <Field label="Password" error={errors.password?.message}>
          <Input
            {...register("password")}
            type="password"
            autoComplete="new-password"
            aria-invalid={errors.password ? true : undefined}
          />
        </Field>
        <Button className="h-11" disabled={isSubmitting}>{isSubmitting ? "Creating account..." : "Create account"}</Button>
      </form>

      {googleClientId ? (
        <>
          <div className="relative flex items-center gap-3">
            <div className="h-px flex-1 bg-line" />
            <span className="text-xs text-neutral-400">or sign up with</span>
            <div className="h-px flex-1 bg-line" />
          </div>

          <div className="flex justify-center">
            <GoogleLogin
              onSuccess={(res: { credential?: string }) => {
                if (res.credential) handleGoogleSuccess(res.credential)
              }}
              onError={() => setError("root", { message: "Google sign-in failed. Please try again." })}
              text="signup_with"
              shape="rectangular"
              theme="outline"
              size="large"
              width="368"
            />
          </div>
        </>
      ) : null}

      <p className="text-sm text-neutral-700">
        Already registered?{" "}
        <Link
          className="font-semibold text-signal"
          to="/login"
          onClick={(event) => {
            event.preventDefault()
            navigate("/login")
          }}
        >
          Login
        </Link>
      </p>
    </div>
  )
}

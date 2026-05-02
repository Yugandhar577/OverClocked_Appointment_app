import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { Link, useNavigate, useSearchParams } from "react-router-dom"

import { verifyOtp } from "../../api/auth"
import { errorMessage } from "../../api/client"
import { otpSchema, type OtpFormData } from "../../lib/validation"
import { Button } from "../../components/ui/Button"
import { Field, Input } from "../../components/ui/Field"
import { Notice } from "../../components/ui/Notice"

export function OtpPage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    setError,
    clearErrors,
    formState: { errors, isSubmitting },
  } = useForm<OtpFormData>({
    resolver: zodResolver(otpSchema),
    defaultValues: { email: params.get("email") ?? "", otp: "" },
  })

  async function submit(data: OtpFormData) {
    clearErrors("root")
    try {
      await verifyOtp(data.email, data.otp)
      navigate("/login")
    } catch (err) {
      setError("root", { message: errorMessage(err) })
    }
  }

  return (
    <form className="grid gap-4" onSubmit={handleSubmit(submit)} noValidate>
      {errors.root && <Notice tone="error">{errors.root.message}</Notice>}
      <Field label="Email" error={errors.email?.message}>
        <Input
          {...register("email")}
          type="email"
          aria-invalid={errors.email ? true : undefined}
        />
      </Field>
      <Field label="OTP" error={errors.otp?.message}>
        <Input
          {...register("otp")}
          inputMode="numeric"
          autoComplete="one-time-code"
          aria-invalid={errors.otp ? true : undefined}
        />
      </Field>
      <Button disabled={isSubmitting}>{isSubmitting ? "Verifying…" : "Verify"}</Button>
      <Link className="text-sm font-semibold text-signal" to="/login">
        Back to login
      </Link>
    </form>
  )
}

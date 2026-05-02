import { useEffect } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"

import { updateMe } from "../../api/auth"
import { errorMessage } from "../../api/client"
import { useAuth } from "../../auth/useAuth"
import { profileSchema, type ProfileFormData } from "../../lib/validation"
import { Button } from "../../components/ui/Button"
import { Field, Input } from "../../components/ui/Field"
import { Notice } from "../../components/ui/Notice"

export function ProfilePage() {
  const auth = useAuth()

  const {
    register,
    handleSubmit,
    reset,
    setError,
    clearErrors,
    formState: { errors, isSubmitting, isSubmitSuccessful },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      fullName: auth.user?.full_name ?? "",
      phone: auth.user?.phone ?? "",
    },
  })

  useEffect(() => {
    if (auth.user) {
      reset({ fullName: auth.user.full_name, phone: auth.user.phone ?? "" })
    }
  }, [auth.user, reset])

  async function submit(data: ProfileFormData) {
    clearErrors("root")
    try {
      await updateMe({ full_name: data.fullName, phone: data.phone ?? "" })
      await auth.refresh()
    } catch (err) {
      setError("root", { message: errorMessage(err) })
    }
  }

  return (
    <form className="mx-auto grid max-w-xl gap-4" onSubmit={handleSubmit(submit)} noValidate>
      <h1 className="text-3xl font-bold text-ink">Profile</h1>
      {isSubmitSuccessful && !errors.root && <Notice tone="success">Saved.</Notice>}
      {errors.root && <Notice tone="error">{errors.root.message}</Notice>}
      <Field label="Full name" error={errors.fullName?.message}>
        <Input
          {...register("fullName")}
          autoComplete="name"
          aria-invalid={errors.fullName ? true : undefined}
        />
      </Field>
      <Field label="Phone" error={errors.phone?.message}>
        <Input
          {...register("phone")}
          type="tel"
          autoComplete="tel"
          aria-invalid={errors.phone ? true : undefined}
        />
      </Field>
      <Button disabled={isSubmitting}>{isSubmitting ? "Saving…" : "Save"}</Button>
    </form>
  )
}

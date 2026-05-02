import { CalendarDays, ImagePlus, Link2, Package, Plus, Send, Trash2, Users, X } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom"

import {
  addAppointmentNote,
  appointmentActivity,
  createAppointmentType,
  getAppointmentType,
  publishAppointmentType,
  replaceQuestions,
  replaceResources,
  replaceWorkingHours,
  resourceCandidates,
  shareLink,
  sendAppointmentMessage,
  updateAppointmentType,
  updateRules,
} from "../../api/appointmentTypes"
import { errorMessage } from "../../api/client"
import type { ActivityItem, AppointmentTypeDetail, ResourceCandidate } from "../../api/types"
import { Button } from "../../components/ui/Button"
import { Input, Textarea } from "../../components/ui/Field"
import { Notice } from "../../components/ui/Notice"

type Tab = "availabilities" | "questions" | "communication" | "options"

interface ResourceDraft {
  id?: string
  name: string
  capacity: number
  resource_type: string
  user_ref_id?: string | null
}

interface HourDraft {
  day_of_week: number
  start_time: string
  end_time: string
}

interface QuestionDraft {
  label: string
  question_type: string
  required: boolean
  optionsText: string
}

const dayNames = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

const presetDefaults: Record<string, { title: string; duration: number; resourceType: string; resources: ResourceDraft[]; questions: QuestionDraft[] }> = {
  meeting: {
    title: "Meeting",
    duration: 30,
    resourceType: "user",
    resources: [{ name: "Primary organiser", capacity: 1, resource_type: "human" }],
    questions: [{ label: "Phone number", question_type: "phone", required: true, optionsText: "" }],
  },
  video_call: {
    title: "Video Call",
    duration: 45,
    resourceType: "user",
    resources: [{ name: "Video host", capacity: 1, resource_type: "human" }],
    questions: [{ label: "Agenda", question_type: "text", required: false, optionsText: "" }],
  },
  table_booking: {
    title: "Table",
    duration: 120,
    resourceType: "resource",
    resources: [
      { name: "Table 1", capacity: 2, resource_type: "room" },
      { name: "Table 2", capacity: 2, resource_type: "room" },
      { name: "Table 3", capacity: 4, resource_type: "room" },
      { name: "Table 4", capacity: 6, resource_type: "room" },
    ],
    questions: [{ label: "Phone number", question_type: "phone", required: true, optionsText: "" }],
  },
  resource: {
    title: "Book a Resource",
    duration: 60,
    resourceType: "resource",
    resources: [
      { name: "Resource 1", capacity: 1, resource_type: "room" },
      { name: "Resource 2", capacity: 1, resource_type: "room" },
      { name: "Resource 3", capacity: 1, resource_type: "room" },
      { name: "Resource 4", capacity: 1, resource_type: "room" },
    ],
    questions: [{ label: "Phone number", question_type: "phone", required: true, optionsText: "" }],
  },
}

const baseHours: HourDraft[] = [
  { day_of_week: 0, start_time: "09:00", end_time: "12:00" },
  { day_of_week: 0, start_time: "14:00", end_time: "17:00" },
  { day_of_week: 1, start_time: "09:00", end_time: "12:00" },
  { day_of_week: 1, start_time: "14:00", end_time: "17:00" },
  { day_of_week: 2, start_time: "09:00", end_time: "12:00" },
]

export function NewTypePage() {
  const navigate = useNavigate()
  const { appointmentTypeId } = useParams()
  const [searchParams] = useSearchParams()
  const initialPreset = searchParams.get("preset") || "meeting"

  const [activeTab, setActiveTab] = useState<Tab>("availabilities")
  const [message, setMessage] = useState("")
  const [loading, setLoading] = useState(Boolean(appointmentTypeId))
  const [saving, setSaving] = useState(false)
  const [shareUrl, setShareUrl] = useState("")
  const [showPresets, setShowPresets] = useState(!appointmentTypeId && !searchParams.get("preset"))

  const initial = presetDefaults[initialPreset] || presetDefaults.meeting
  const [preset, setPreset] = useState(initialPreset)
  const [title, setTitle] = useState(initial.title)
  const [duration, setDuration] = useState(initial.duration)
  const [venue, setVenue] = useState("OverClocked\nIndia")
  const [description, setDescription] = useState("")
  const [confirmationMsg, setConfirmationMsg] = useState("")
  const [timezone, setTimezone] = useState("Asia/Kolkata")
  const [bookBy, setBookBy] = useState(initial.resourceType)
  const [assignment, setAssignment] = useState("auto")
  const [startsWith, setStartsWith] = useState("date")
  const [manageCapacity, setManageCapacity] = useState(initial.resourceType === "resource")
  const [capacity, setCapacity] = useState(Math.max(1, initial.resources.reduce((sum, resource) => sum + resource.capacity, 0)))
  const [resources, setResources] = useState<ResourceDraft[]>(initial.resources)
  const [hours, setHours] = useState<HourDraft[]>(baseHours)
  const [questions, setQuestions] = useState<QuestionDraft[]>(initial.questions)
  const [requiresConfirmation, setRequiresConfirmation] = useState(false)
  const [allowInvitations, setAllowInvitations] = useState(true)
  const [displayPictures, setDisplayPictures] = useState(false)
  const [futureDays, setFutureDays] = useState(45)
  const [cancelBefore, setCancelBefore] = useState(60)
  const [slotEvery, setSlotEvery] = useState(initial.duration)
  const [isPaid, setIsPaid] = useState(false)
  const [price, setPrice] = useState(0)
  const [imageUrl, setImageUrl] = useState("")
  const [videoUrl, setVideoUrl] = useState("")
  const [bookingEmailTemplate, setBookingEmailTemplate] = useState("Appointment: Attendee Invitation")
  const [cancellationEmailTemplate, setCancellationEmailTemplate] = useState("Appointment: Appointment Canceled")
  const [reminderEmailHours, setReminderEmailHours] = useState(3)
  const [reminderSmsHours, setReminderSmsHours] = useState(1)
  const [resourceName, setResourceName] = useState("")
  const [resourceCapacity, setResourceCapacity] = useState(1)
  const [resourceCandidatesList, setResourceCandidatesList] = useState<ResourceCandidate[]>([])
  const [activityItems, setActivityItems] = useState<ActivityItem[]>([])
  const [composerMode, setComposerMode] = useState<"message" | "note" | null>(null)
  const [composerText, setComposerText] = useState("")
  const [postingActivity, setPostingActivity] = useState(false)
  const [coverImageCompressed, setCoverImageCompressed] = useState<string | null>(null)
  const [coverImageCacheKey, setCoverImageCacheKey] = useState<string | null>(null)
  const [coverImagePreview, setCoverImagePreview] = useState<string>("")

  const totalResourceCapacity = useMemo(() => resources.reduce((sum, resource) => sum + Number(resource.capacity || 0), 0), [resources])
  const displayCapacity = manageCapacity ? Math.max(1, capacity || totalResourceCapacity || 1) : 1

  useEffect(() => {
    if (!appointmentTypeId) return
    getAppointmentType(appointmentTypeId)
      .then((detail) => hydrate(detail))
      .catch((err) => setMessage(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [appointmentTypeId])

  useEffect(() => {
    resourceCandidates(bookBy === "user" ? "user" : "resource")
      .then(setResourceCandidatesList)
      .catch(() => setResourceCandidatesList([]))
  }, [bookBy])

  useEffect(() => {
    if (!appointmentTypeId) return
    loadActivity()
  }, [appointmentTypeId])

  function hydrate(detail: AppointmentTypeDetail) {
    setPreset(detail.preset_type || "meeting")
    setTitle(detail.title)
    setDuration(detail.duration_minutes)
    setSlotEvery(detail.duration_minutes)
    setVenue(detail.venue || "")
    setDescription(detail.description || "")
    setConfirmationMsg(detail.confirmation_msg || "")
    setTimezone(detail.timezone)
    setBookBy(detail.resource_type)
    setAssignment(detail.assignment_method || "auto")
    setStartsWith(detail.starts_with || "date")
    setManageCapacity(detail.manage_capacity)
    setCapacity(detail.max_capacity || 1)
    setRequiresConfirmation(detail.requires_confirmation)
    setAllowInvitations(detail.allow_invitations)
    setDisplayPictures(detail.display_pictures)
    setFutureDays(detail.future_days_limit)
    setCancelBefore(detail.cancel_before_minutes || 60)
    setSlotEvery(detail.slot_interval_minutes || detail.duration_minutes)
    setIsPaid(detail.is_paid)
    setPrice(Number(detail.price || 0))
    setImageUrl(detail.image_url || "")
    setVideoUrl(detail.video_url || "")
    setBookingEmailTemplate(detail.booking_email_template || "Appointment: Attendee Invitation")
    setCancellationEmailTemplate(detail.cancellation_email_template || "Appointment: Appointment Canceled")
    setReminderEmailHours(detail.reminder_email_hours ?? 3)
    setReminderSmsHours(detail.reminder_sms_hours ?? 1)
    setCoverImageCompressed(detail.cover_image_compressed ?? null)
    setCoverImageCacheKey(detail.cover_image_cache_key ?? null)
    setCoverImagePreview(loadCachedCoverImage(detail.cover_image_cache_key) || detail.image_url || detail.cover_image_compressed || "")
    setResources(detail.resources.length ? detail.resources.map((resource) => ({
      id: resource.id,
      name: resource.name,
      capacity: resource.capacity,
      resource_type: resource.resource_type,
      user_ref_id: resource.user_ref_id,
    })) : presetDefaults.meeting.resources)
    setHours(detail.working_hours.length ? detail.working_hours.map((hour) => ({
      day_of_week: hour.day_of_week,
      start_time: hour.start_time.slice(0, 5),
      end_time: hour.end_time.slice(0, 5),
    })) : baseHours)
    setQuestions(detail.questions.length ? detail.questions.map((question) => ({
      label: question.question_text,
      question_type: question.answer_type,
      required: question.is_mandatory,
      optionsText: Array.isArray(question.options) ? question.options.join(", ") : "",
    })) : presetDefaults.meeting.questions)
  }

  function choosePreset(nextPreset: string) {
    const defaults = presetDefaults[nextPreset] || presetDefaults.meeting
    setPreset(nextPreset)
    setTitle(defaults.title)
    setDuration(defaults.duration)
    setSlotEvery(defaults.duration)
    setBookBy(defaults.resourceType)
    setManageCapacity(defaults.resourceType === "resource")
    setResources(defaults.resources)
    setQuestions(defaults.questions)
    setCapacity(Math.max(1, defaults.resources.reduce((sum, resource) => sum + resource.capacity, 0)))
    setShowPresets(false)
  }

  async function save(publish: boolean) {
    setSaving(true)
    setMessage("")
    try {
      const payload = {
        title,
        preset_type: preset,
        description,
        duration_minutes: duration,
        timezone,
        resource_type: bookBy,
        future_days_limit: futureDays,
        venue,
        confirmation_msg: confirmationMsg,
        image_url: imageUrl,
        video_url: videoUrl,
        booking_email_template: bookingEmailTemplate,
        cancellation_email_template: cancellationEmailTemplate,
        reminder_email_hours: reminderEmailHours,
        reminder_sms_hours: reminderSmsHours,
        cover_image_compressed: coverImageCompressed,
        cover_image_cache_key: coverImageCacheKey,
      }
      const id = appointmentTypeId
        ? (await updateAppointmentType(appointmentTypeId, payload)).id
        : (await createAppointmentType(payload)).id

      await replaceResources(id, resources.map((resource) => ({
        name: resource.name,
        capacity: Math.max(1, Number(resource.capacity || 1)),
        resource_type: resource.resource_type || "room",
        id: resource.id,
        user_ref_id: resource.user_ref_id,
      })))
      await replaceWorkingHours(id, hours.map((hour) => ({
        day_of_week: hour.day_of_week,
        start_time: `${hour.start_time}:00`,
        end_time: `${hour.end_time}:00`,
      })))
      await replaceQuestions(id, questions.filter((question) => question.label.trim()).map((question) => ({
        label: question.label,
        question_type: question.question_type,
        required: question.required,
        options: question.optionsText ? question.optionsText.split(",").map((option) => option.trim()).filter(Boolean) : undefined,
      })))
      await updateRules(id, {
        requires_confirmation: requiresConfirmation,
        manage_capacity: manageCapacity,
        is_paid: isPaid,
        price: isPaid ? price : null,
        advance_payment_required: false,
        cancel_before_minutes: cancelBefore,
        reschedule_before_minutes: cancelBefore,
        max_per_slot: displayCapacity,
        future_days_limit: futureDays,
        assignment_method: assignment,
        allow_invitations: allowInvitations,
        display_pictures: displayPictures,
        starts_with: startsWith,
        slot_type: "weekly",
        slot_interval_minutes: slotEvery,
      })

      if (publish) {
        const published = await publishAppointmentType(id)
        const link = await shareLink(id)
        setShareUrl(link.url)
        await navigator.clipboard.writeText(link.url)
        setMessage(`Published with ${published.slots_generated} generated slots. Share URL copied.`)
      } else {
        setMessage("Appointment type saved.")
      }
      if (!appointmentTypeId) navigate(`/organiser/types/${id}`, { replace: true })
      if (appointmentTypeId) loadActivity()
    } catch (err) {
      setMessage(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  function loadActivity() {
    if (!appointmentTypeId) return
    appointmentActivity(appointmentTypeId)
      .then(setActivityItems)
      .catch(() => setActivityItems([]))
  }

  async function copyShareLink() {
    if (!appointmentTypeId) {
      setMessage("Save the appointment type before sharing.")
      return
    }
    try {
      const link = await shareLink(appointmentTypeId)
      setShareUrl(link.url)
      await navigator.clipboard.writeText(link.url)
      setMessage("Share URL copied.")
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  function addTypedResource() {
    const name = resourceName.trim()
    if (!name) {
      setMessage(`Enter a ${bookBy === "user" ? "user" : "resource"} name first.`)
      return
    }
    setResources([
      ...resources,
      {
        name,
        capacity: Math.max(1, resourceCapacity),
        resource_type: bookBy === "user" ? "human" : "room",
      },
    ])
    setResourceName("")
    setResourceCapacity(1)
  }

  function addCandidate(candidateId: string) {
    const candidate = resourceCandidatesList.find((item) => item.id === candidateId)
    if (!candidate || resources.some((resource) => resource.user_ref_id === candidate.user_ref_id || resource.id === candidate.id)) return
    setResources([
      ...resources,
      {
        id: candidate.user_ref_id ? undefined : candidate.id,
        name: candidate.name,
        capacity: Math.max(1, candidate.capacity || 1),
        resource_type: candidate.resource_type,
        user_ref_id: candidate.user_ref_id,
      },
    ])
  }

  function updateResource(index: number, patch: Partial<ResourceDraft>) {
    setResources(resources.map((resource, resourceIndex) => (resourceIndex === index ? { ...resource, ...patch } : resource)))
  }

  function handleImageFile(file?: File) {
    if (!file) return
    if (!file.type.startsWith("image/")) {
      setMessage("Choose an image file.")
      return
    }
    const reader = new FileReader()
    reader.onload = () => setImageUrl(String(reader.result || ""))
    reader.readAsDataURL(file)
  }

  function addVideoUrl() {
    const value = window.prompt("Video meeting URL", videoUrl)
    if (value !== null) setVideoUrl(value.trim())
  }

  function openActivityComposer(kind: "message" | "note") {
    if (!appointmentTypeId) {
      setMessage("Save the appointment type before using activity.")
      return
    }
    setComposerMode(kind)
    setComposerText("")
  }

  async function submitActivity() {
    if (!appointmentTypeId || !composerMode || !composerText.trim()) return
    setPostingActivity(true)
    try {
      const item =
        composerMode === "message"
          ? await sendAppointmentMessage(appointmentTypeId, composerText.trim())
          : await addAppointmentNote(appointmentTypeId, composerText.trim())
      setActivityItems([item, ...activityItems])
      setMessage(composerMode === "message" ? "Message queued and logged." : "Note logged.")
      setComposerMode(null)
      setComposerText("")
    } catch (err) {
      setMessage(errorMessage(err))
    } finally {
      setPostingActivity(false)
    }
  }

  async function handleCoverImage(file: File | null) {
    if (!file) return
    setMessage("")
    try {
      const original = await readFileAsDataUrl(file)
      const compressed = await compressImage(original)
      const cacheKey = `appointment-cover:${appointmentTypeId || "draft"}:${Date.now()}`
      localStorage.setItem(cacheKey, original)
      setImageUrl(compressed)
      setCoverImageCompressed(compressed)
      setCoverImageCacheKey(cacheKey)
      setCoverImagePreview(original)
      setMessage("Image ready. Compressed copy will be saved to the database; original is cached in this browser.")
    } catch {
      setMessage("Could not process that image. Try a smaller PNG or JPG.")
    }
  }

  if (loading) return <Notice>Loading appointment type...</Notice>

  return (
    <div className="grid gap-4">
      <section className="rounded-md border border-line bg-paper">
        <div className="grid gap-4 border-b border-line p-4 lg:grid-cols-[1fr_auto_1fr] lg:items-center">
          <div className="flex items-center gap-3">
            <Link to="/organiser/types">
              <Button type="button" variant="secondary">
                Appointment types
              </Button>
            </Link>
            <div>
              <p className="text-sm font-bold text-signal">Appointments</p>
              <h1 className="text-xl font-bold text-ink">{title || "New appointment type"}</h1>
            </div>
          </div>
          <div className="flex justify-start divide-x divide-line overflow-hidden rounded-md border border-line bg-white lg:justify-center">
            <Counter icon={<Link2 size={18} />} label="Shared Links" value={shareUrl || appointmentTypeId ? 1 : 0} />
            <Counter icon={<Package size={18} />} label="Resources" value={resources.length} />
            <Counter icon={<CalendarDays size={18} />} label="Appointments" value={0} />
          </div>
          <div className="flex flex-wrap justify-start gap-2 lg:justify-end">
            <Button type="button" onClick={copyShareLink}>
              <Send size={16} />
              Share
            </Button>
            {appointmentTypeId && (
              <Link to={`/book/${appointmentTypeId}`}>
                <Button type="button" variant="secondary">Preview</Button>
              </Link>
            )}
          </div>
        </div>

        <div className="flex flex-wrap gap-2 border-b border-line bg-white/70 p-4">
          <Button type="button" onClick={() => save(false)} disabled={saving}>Save</Button>
          <Button type="button" variant="secondary" onClick={() => save(true)} disabled={saving}>
            Save and publish
          </Button>
          {message && <div className="min-w-72 flex-1"><Notice>{message}</Notice></div>}
        </div>

        <div className="grid lg:grid-cols-[minmax(0,1fr)_340px]">
          <div className="grid gap-6 p-5">
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.9fr)]">
              <section className="grid gap-5">
                <label className="grid gap-2">
                  <span className="text-sm font-bold text-ink">Appointment Title</span>
                  <input
                    value={title}
                    onChange={(event) => setTitle(event.target.value)}
                    className="focus-ring min-w-0 border-0 border-b border-transparent bg-transparent text-4xl font-semibold text-ink outline-none focus:border-line"
                  />
                </label>
                <TwoColumn label="Duration">
                  <div className="flex items-center gap-2">
                    <Input type="number" min={5} value={duration} onChange={(event) => setDuration(Number(event.target.value))} className="w-24" />
                    <span>min</span>
                  </div>
                </TwoColumn>
                <TwoColumn label="Location">
                  <Textarea value={venue} onChange={(event) => setVenue(event.target.value)} className="min-h-20" />
                  <button type="button" onClick={addVideoUrl} className="mt-2 inline-flex items-center gap-2 text-sm font-bold text-signal">
                    <Plus size={16} />
                    {videoUrl ? "Change Video" : "Add Video"}
                  </button>
                  {videoUrl && <p className="mt-1 max-w-sm truncate text-xs text-neutral-600">{videoUrl}</p>}
                </TwoColumn>
              </section>

              <section className="grid content-start gap-4 rounded-md border border-line bg-white p-5 shadow-sm">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-neutral-500">Assignment</p>
                    <h2 className="text-lg font-bold text-ink">Staff and resources</h2>
                  </div>
                  <label className="group relative h-20 w-20 shrink-0 cursor-pointer overflow-hidden rounded-md border border-line bg-paper text-neutral-400">
                    {coverImagePreview || imageUrl ? (
                      <img src={coverImagePreview || imageUrl} alt="" className="h-full w-full object-cover" />
                    ) : (
                      <span className="grid h-full w-full place-items-center">
                        <ImagePlus size={42} />
                      </span>
                    )}
                    <span className="absolute inset-0 hidden place-items-center bg-black/45 text-xs font-bold text-white group-hover:grid">
                      Change
                    </span>
                    <input
                      type="file"
                      accept="image/png,image/jpeg,image/webp"
                      className="sr-only"
                      onChange={(event) => handleCoverImage(event.target.files?.[0] ?? null)}
                    />
                  </label>
                </div>
                <p className="text-xs text-neutral-600">
                  Upload an image once: a small compressed copy is stored with the appointment type, and the original stays cached in this browser for sharper previews.
                </p>
                <TwoColumn label="Book">
                  <RadioRow value={bookBy} onChange={setBookBy} options={[["user", "Users"], ["resource", "Resources"]]} />
                </TwoColumn>
                <div className="grid gap-2">
                  <strong className="text-sm text-ink">{bookBy === "user" ? "Users" : "Resources"}</strong>
                  <div className="grid max-w-full gap-3">
                    {bookBy === "user" && (
                      <select
                        className="h-10 w-full min-w-0 rounded-md border border-line bg-white px-3 text-sm"
                        value=""
                        onChange={(event) => addCandidate(event.target.value)}
                      >
                        <option value="">Choose from company individuals...</option>
                        {resourceCandidatesList.map((candidate) => (
                          <option key={candidate.id} value={candidate.id}>
                            {candidate.name}{candidate.email ? ` (${candidate.email})` : ""}
                          </option>
                        ))}
                      </select>
                    )}
                    {resources.map((resource, index) => (
                      <div key={`${resource.id || resource.user_ref_id || resource.name}-${index}`} className="grid max-w-full gap-2 rounded-md border border-line bg-white p-2 md:grid-cols-[minmax(0,1fr)_84px_36px] md:items-center">
                        <Input value={resource.name} onChange={(event) => updateResource(index, { name: event.target.value })} aria-label={`${bookBy === "user" ? "User" : "Resource"} name`} />
                        <Input type="number" min={1} value={resource.capacity} onChange={(event) => updateResource(index, { capacity: Number(event.target.value) })} aria-label="Capacity" />
                        <button type="button" onClick={() => setResources(resources.filter((_item, resourceIndex) => resourceIndex !== index))} className="grid h-9 w-9 place-items-center rounded-md text-warn hover:bg-red-50" aria-label={`Remove ${resource.name}`}>
                          <Trash2 size={16} />
                        </button>
                      </div>
                    ))}
                    <div className="grid max-w-full gap-2 md:grid-cols-[minmax(0,1fr)_84px_auto]">
                      <Input
                        value={resourceName}
                        onChange={(event) => setResourceName(event.target.value)}
                        placeholder={bookBy === "user" ? "Add user name..." : "Add resource name..."}
                      />
                      <Input type="number" min={1} value={resourceCapacity} onChange={(event) => setResourceCapacity(Number(event.target.value))} />
                      <Button type="button" variant="secondary" onClick={addTypedResource}>
                        Add
                      </Button>
                    </div>
                  </div>
                </div>
                <TwoColumn label="Assignment ?">
                  <RadioRow value={assignment} onChange={setAssignment} options={[["auto", "Automatically"], ["visitor", "By visitor"]]} />
                </TwoColumn>
                <TwoColumn label="Starts with ?">
                  <RadioRow value={startsWith} onChange={setStartsWith} options={[["date", "Date"], ["resource", "User / Resource"]]} />
                </TwoColumn>
                <TwoColumn label="Manage Capacities ?">
                  <label className="flex flex-wrap items-center gap-3">
                    <input type="checkbox" checked={manageCapacity} onChange={(event) => setManageCapacity(event.target.checked)} />
                    <span>Allow</span>
                    <Input type="number" min={1} value={capacity} onChange={(event) => setCapacity(Number(event.target.value))} className="w-24" />
                    <span>simultaneous appointment(s) per resource</span>
                  </label>
                </TwoColumn>
              </section>
            </div>

            <div>
              <div className="flex flex-wrap">
                <TabButton active={activeTab === "availabilities"} onClick={() => setActiveTab("availabilities")}>Availabilities</TabButton>
                <TabButton active={activeTab === "questions"} onClick={() => setActiveTab("questions")}>Questions</TabButton>
                <TabButton active={activeTab === "communication"} onClick={() => setActiveTab("communication")}>Communication</TabButton>
                <TabButton active={activeTab === "options"} onClick={() => setActiveTab("options")}>Options</TabButton>
              </div>
              <div className="border border-line bg-white">
                {activeTab === "availabilities" && (
                  <EditableTable
                    headers={["Every", "From", "To", ""]}
                    addLabel="Add a line"
                    onAdd={() => setHours([...hours, { day_of_week: 0, start_time: "09:00", end_time: "17:00" }])}
                  >
                    {hours.map((hour, index) => (
                      <tr key={index} className="border-t border-line">
                        <td className="px-4 py-3">
                          <select value={hour.day_of_week} onChange={(event) => updateHour(index, { day_of_week: Number(event.target.value) })} className="bg-transparent">
                            {dayNames.map((day, dayIndex) => <option key={day} value={dayIndex}>{day}</option>)}
                          </select>
                        </td>
                        <td className="px-4 py-3"><Input type="time" value={hour.start_time} onChange={(event) => updateHour(index, { start_time: event.target.value })} /></td>
                        <td className="px-4 py-3"><Input type="time" value={hour.end_time} onChange={(event) => updateHour(index, { end_time: event.target.value })} /></td>
                        <td className="px-4 py-3 text-right">
                          <button type="button" onClick={() => setHours(hours.filter((_item, hourIndex) => hourIndex !== index))} aria-label="Remove availability">
                            <Trash2 size={16} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </EditableTable>
                )}
                {activeTab === "questions" && (
                  <EditableTable
                    headers={["Question", "Answer Type", "Answers", "Mandatory", ""]}
                    addLabel="Add a line"
                    onAdd={() => setQuestions([...questions, { label: "New question", question_type: "text", required: false, optionsText: "" }])}
                  >
                    {questions.map((question, index) => (
                      <tr key={index} className="border-t border-line">
                        <td className="px-4 py-3"><Input value={question.label} onChange={(event) => updateQuestion(index, { label: event.target.value })} /></td>
                        <td className="px-4 py-3">
                          <select value={question.question_type} onChange={(event) => updateQuestion(index, { question_type: event.target.value })} className="h-10 rounded-md border border-line bg-white px-3">
                            <option value="text">Text</option>
                            <option value="phone">Phone Number</option>
                            <option value="select">Single Choice</option>
                          </select>
                        </td>
                        <td className="px-4 py-3"><Input value={question.optionsText} placeholder="Available answers" onChange={(event) => updateQuestion(index, { optionsText: event.target.value })} /></td>
                        <td className="px-4 py-3"><input type="checkbox" checked={question.required} onChange={(event) => updateQuestion(index, { required: event.target.checked })} /></td>
                        <td className="px-4 py-3 text-right"><button type="button" onClick={() => setQuestions(questions.filter((_item, questionIndex) => questionIndex !== index))}><Trash2 size={16} /></button></td>
                      </tr>
                    ))}
                  </EditableTable>
                )}
                {activeTab === "communication" && (
                  <div className="grid gap-8 p-5 xl:grid-cols-2">
                    <section className="grid gap-4">
                      <h3 className="border-b border-line pb-2 text-sm font-bold uppercase">Introduction page</h3>
                      <Textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder='e.g. "During this meeting, we will..."' className="min-h-36" />
                      <h3 className="border-b border-line pb-2 text-sm font-bold uppercase">Confirmation page</h3>
                      <Textarea value={confirmationMsg} onChange={(event) => setConfirmationMsg(event.target.value)} placeholder='e.g. "Thank you for your trust, we look forward to meeting you."' className="min-h-36" />
                    </section>
                    <section className="grid content-start gap-5">
                      <h3 className="border-b border-line pb-2 text-sm font-bold uppercase">Emails & SMS</h3>
                      <TwoColumn label="Reminders">
                        <div className="flex flex-wrap items-center gap-2">
                          <span>Email</span>
                          <Input type="number" min={0} max={168} value={reminderEmailHours} onChange={(event) => setReminderEmailHours(Number(event.target.value))} className="w-20" />
                          <span>hours</span>
                          <span>SMS</span>
                          <Input type="number" min={0} max={168} value={reminderSmsHours} onChange={(event) => setReminderSmsHours(Number(event.target.value))} className="w-20" />
                          <span>hours</span>
                        </div>
                      </TwoColumn>
                      <TwoColumn label="Booking Email ?">
                        <Input value={bookingEmailTemplate} onChange={(event) => setBookingEmailTemplate(event.target.value)} />
                      </TwoColumn>
                      <TwoColumn label="Cancellation Email ?">
                        <Input value={cancellationEmailTemplate} onChange={(event) => setCancellationEmailTemplate(event.target.value)} />
                      </TwoColumn>
                    </section>
                  </div>
                )}
                {activeTab === "options" && (
                  <div className="grid gap-8 p-5 xl:grid-cols-2">
                    <section className="grid content-start gap-5">
                      <CheckboxLine label="Allow invitations ?" checked={allowInvitations} onChange={setAllowInvitations}>by visitor</CheckboxLine>
                      <CheckboxLine label="Auto Confirm ?" checked={!requiresConfirmation} onChange={(checked) => setRequiresConfirmation(!checked)}>up to 100 % of total capacity</CheckboxLine>
                      <CheckboxLine label="Display pictures ?" checked={displayPictures} onChange={setDisplayPictures}></CheckboxLine>
                      <CheckboxLine label="Paid booking ?" checked={isPaid} onChange={setIsPaid}>
                        <Input type="number" min={0} value={price} onChange={(event) => setPrice(Number(event.target.value))} className="w-28" />
                      </CheckboxLine>
                    </section>
                    <section className="grid content-start gap-5">
                      <TwoColumn label="Schedule">
                        <RadioRow value="weekly" onChange={() => undefined} options={[["weekly", "Weekly"], ["flexible", "Flexible"]]} />
                      </TwoColumn>
                      <TwoColumn label="Allow Bookings">
                        <div className="flex flex-wrap items-center gap-2">
                          <span>Within the next</span>
                          <Input type="number" min={1} value={futureDays} onChange={(event) => setFutureDays(Number(event.target.value))} className="w-24" />
                          <span>days, at least 1h before start time</span>
                        </div>
                      </TwoColumn>
                      <TwoColumn label="Create slot every ?">
                        <div className="flex items-center gap-2">
                          <Input type="number" min={5} value={slotEvery} onChange={(event) => setSlotEvery(Number(event.target.value))} className="w-24" />
                          <span>min</span>
                        </div>
                      </TwoColumn>
                      <TwoColumn label="Cancellation">
                        <div className="flex flex-wrap items-center gap-2">
                          <span>up to</span>
                          <Input type="number" min={0} value={cancelBefore} onChange={(event) => setCancelBefore(Number(event.target.value))} className="w-24" />
                          <span>min before the booking</span>
                        </div>
                      </TwoColumn>
                      <TwoColumn label="Timezone ?">
                        <Input value={timezone} onChange={(event) => setTimezone(event.target.value)} />
                      </TwoColumn>
                    </section>
                  </div>
                )}
              </div>
            </div>
          </div>

          <aside className="border-t border-line bg-[#f6f7f8] p-5 lg:border-l lg:border-t-0">
            <div className="flex flex-wrap gap-2">
              <Button type="button" onClick={() => openActivityComposer("message")}><Send size={16} />Send message</Button>
              <Button type="button" variant="secondary" onClick={() => openActivityComposer("note")}>Log note</Button>
              <Button type="button" variant="secondary" onClick={loadActivity}>Activity</Button>
            </div>
            {composerMode && (
              <div className="mt-3 grid gap-2 rounded-md border border-line bg-white p-3">
                <label className="text-sm font-bold text-ink">{composerMode === "message" ? "Send message" : "Log note"}</label>
                <Textarea
                  value={composerText}
                  onChange={(event) => setComposerText(event.target.value)}
                  placeholder={composerMode === "message" ? "Write a message..." : "Write an internal note..."}
                  className="min-h-24"
                />
                <div className="flex justify-end gap-2">
                  <Button type="button" variant="ghost" onClick={() => setComposerMode(null)}>Cancel</Button>
                  <Button type="button" onClick={submitActivity} disabled={postingActivity || !composerText.trim()}>
                    {composerMode === "message" ? "Send" : "Log"}
                  </Button>
                </div>
              </div>
            )}
            <div className="my-8 flex items-center gap-3 text-sm text-neutral-500">
              <span className="h-px flex-1 bg-line"></span>
              Today
              <span className="h-px flex-1 bg-line"></span>
            </div>
            <div className="grid gap-4">
              {activityItems.length === 0 && (
                <div className="flex gap-3">
                  <span className="grid h-10 w-10 place-items-center rounded-md bg-ink text-paper">P</span>
                  <p className="text-sm">
                    <strong>Organiser</strong> <span className="text-neutral-500">now</span>
                    <br />
                    Appointment Type {appointmentTypeId ? "configured" : "draft ready"}
                  </p>
                </div>
              )}
              {activityItems.map((item) => (
                <div key={item.id} className="flex gap-3">
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-ink text-paper">
                    {(item.actor_name || "O").slice(0, 1)}
                  </span>
                  <p className="text-sm">
                    <strong>{item.actor_name || "Organiser"}</strong>{" "}
                    <span className="text-neutral-500">{new Date(item.created_at).toLocaleString()}</span>
                    <br />
                    {activityLabel(item)}
                  </p>
                </div>
              ))}
            </div>
          </aside>
        </div>
      </section>

      {showPresets && (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/35 p-4">
          <section className="w-full max-w-5xl overflow-hidden rounded-md border border-line bg-paper shadow-panel">
            <div className="flex items-center justify-between border-b border-line px-5 py-4">
              <h2 className="text-xl font-bold text-ink">Choose an appointment preset</h2>
              <button type="button" onClick={() => setShowPresets(false)} className="focus-ring rounded-md p-2 text-neutral-600 hover:bg-white" aria-label="Close">
                <X size={22} />
              </button>
            </div>
            <div className="grid gap-4 p-5 md:grid-cols-2 lg:grid-cols-4">
              {Object.entries(presetDefaults).map(([key, defaults]) => (
                <button key={key} type="button" onClick={() => choosePreset(key)} className="focus-ring grid min-h-48 place-items-center rounded-md border border-line bg-white p-5 text-center hover:border-signal">
                  {defaults.resourceType === "resource" ? <Package size={54} className="text-signal" /> : <Users size={54} className="text-signal" />}
                  <span className="text-lg font-bold text-ink">{defaults.title}</span>
                </button>
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  )

  function updateHour(index: number, patch: Partial<HourDraft>) {
    setHours(hours.map((hour, hourIndex) => (hourIndex === index ? { ...hour, ...patch } : hour)))
  }

  function updateQuestion(index: number, patch: Partial<QuestionDraft>) {
    setQuestions(questions.map((question, questionIndex) => (questionIndex === index ? { ...question, ...patch } : question)))
  }
}

function Counter({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <div className="flex min-w-36 items-center gap-2 px-4 py-2 text-sm">
      <span className="text-signal">{icon}</span>
      <span>{label}<br /><strong>{value}</strong></span>
    </div>
  )
}

function TwoColumn({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-3 sm:grid-cols-[160px_minmax(0,1fr)]">
      <strong className="text-sm text-ink">{label}</strong>
      <div className="min-w-0 text-sm text-ink">{children}</div>
    </div>
  )
}

function RadioRow({ value, onChange, options }: { value: string; onChange: (value: string) => void; options: Array<[string, string]> }) {
  return (
    <div className="flex flex-wrap gap-4">
      {options.map(([optionValue, label]) => (
        <label key={optionValue} className="inline-flex items-center gap-2">
          <input type="radio" checked={value === optionValue} onChange={() => onChange(optionValue)} />
          {label}
        </label>
      ))}
    </div>
  )
}

function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`border border-line px-5 py-3 text-sm font-semibold ${active ? "border-t-4 border-t-ink bg-white text-ink" : "bg-paper text-ink"}`}
    >
      {children}
    </button>
  )
}

function EditableTable({ headers, addLabel, onAdd, children }: { headers: string[]; addLabel: string; onAdd: () => void; children: React.ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[760px] text-left text-sm">
        <thead>
          <tr>
            {headers.map((header) => <th key={header} className="px-4 py-3 font-bold">{header}</th>)}
          </tr>
        </thead>
        <tbody>
          {children}
          <tr className="border-t border-line">
            <td colSpan={headers.length} className="px-4 py-3">
              <button type="button" onClick={onAdd} className="font-bold text-signal">{addLabel}</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}

function activityLabel(item: ActivityItem) {
  if (item.message) return item.message
  const labels: Record<string, string> = {
    appointment_type_created: "Appointment Type created",
    appointment_type_updated: "Appointment Type configured",
    appointment_type_resources_updated: "Resources updated",
    appointment_type_rules_updated: "Options updated",
    note_added: "Note logged",
    message_sent: "Message sent",
  }
  return labels[item.action] || item.action.replaceAll("_", " ")
}

function CheckboxLine({ label, checked, onChange, children }: { label: string; checked: boolean; onChange: (checked: boolean) => void; children?: React.ReactNode }) {
  return (
    <TwoColumn label={label}>
      <label className="flex flex-wrap items-center gap-3">
        <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
        {children}
      </label>
    </TwoColumn>
  )
}

function loadCachedCoverImage(cacheKey?: string | null) {
  if (!cacheKey) return ""
  try {
    return localStorage.getItem(cacheKey) || ""
  } catch {
    return ""
  }
}

function readFileAsDataUrl(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ""))
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

function compressImage(dataUrl: string) {
  return new Promise<string>((resolve, reject) => {
    const image = new Image()
    image.onload = () => {
      const maxSide = 360
      const scale = Math.min(1, maxSide / Math.max(image.width, image.height))
      const canvas = document.createElement("canvas")
      canvas.width = Math.max(1, Math.round(image.width * scale))
      canvas.height = Math.max(1, Math.round(image.height * scale))
      const context = canvas.getContext("2d")
      if (!context) {
        reject(new Error("canvas_unavailable"))
        return
      }
      context.drawImage(image, 0, 0, canvas.width, canvas.height)
      resolve(canvas.toDataURL("image/jpeg", 0.62))
    }
    image.onerror = () => reject(new Error("image_load_failed"))
    image.src = dataUrl
  })
}

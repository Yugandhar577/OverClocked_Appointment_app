export interface User {
  id: string
  email: string
  full_name: string
  roles: string[]
  is_verified: boolean
  is_active: boolean
  phone?: string | null
  timezone: string
}

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface AppointmentTypeListItem {
  id: string
  title: string
  duration_minutes: number
  is_paid: boolean
  price?: string | null
  organiser_name: string
  preset_type?: string | null
}

export interface Resource {
  id: string
  name: string
  resource_type: string
  capacity: number
  timezone: string
  is_active: boolean
}

export interface Question {
  id: string
  question_text: string
  answer_type: string
  options?: string[] | Record<string, unknown> | null
  is_mandatory: boolean
  display_order: number
}

export interface AppointmentTypeDetail {
  id: string
  organiser_id: string
  title: string
  description?: string | null
  duration_minutes: number
  timezone: string
  preset_type?: string | null
  resource_type: string
  assignment_method: string
  is_published: boolean
  share_token?: string | null
  is_paid: boolean
  price?: string | null
  currency: string
  requires_confirmation: boolean
  manage_capacity: boolean
  max_capacity?: number | null
  future_days_limit: number
  allow_cancel: boolean
  cancel_before_minutes?: number | null
  allow_reschedule: boolean
  reschedule_before_minutes?: number | null
  venue?: string | null
  confirmation_msg?: string | null
  resources: Resource[]
  questions: Question[]
}

export interface AvailabilitySlot {
  slot_id: string
  start_datetime: string
  end_datetime: string
  remaining_capacity: number
  max_capacity: number
  resource_id?: string | null
}

export interface Booking {
  id: string
  appointment_type_id: string
  slot_id: string
  customer_id: string
  resource_id?: string | null
  status: string
  people_count: number
  confirmation_code: string
  created_at: string
  updated_at: string
  slot_start?: string | null
  slot_end?: string | null
  appointment_title?: string | null
  venue?: string | null
}

export interface BookingCreateResponse {
  booking_id: string
  status: string
  confirmation_code: string
  slot_start: string
  slot_end: string
  venue?: string | null
  organiser_name: string
  payment_required: boolean
  payment_url?: string | null
}

export interface AdminUser extends User {
  created_at: string
}

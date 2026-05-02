import { api } from "./client"
import type { AvailabilitySlot, Booking, BookingCreateResponse, Paginated } from "./types"

export async function availability(params: {
  appointment_type_id: string
  resource_id?: string | null
  date: string
  tz_offset_minutes?: number
}): Promise<AvailabilitySlot[]> {
  const res = await api.get<AvailabilitySlot[]>("/availability", { params })
  return res.data
}

export async function createBooking(payload: {
  appointment_type_id: string
  slot_id: string
  resource_id?: string | null
  people_count: number
  answers: Array<{ question_id: string; value: string | number | boolean | string[] }>
  customer_info: { full_name?: string; email?: string; phone?: string }
}): Promise<BookingCreateResponse> {
  const res = await api.post<BookingCreateResponse>("/bookings", payload)
  return res.data
}

export async function getBooking(id: string): Promise<Booking> {
  const res = await api.get<Booking>(`/bookings/${id}`)
  return res.data
}

export async function myAppointments(status?: string, page = 1, pageSize = 10): Promise<Paginated<Booking>> {
  const res = await api.get<Paginated<Booking>>("/me/appointments", { params: { status, page, page_size: pageSize } })
  return res.data
}

export async function cancelBooking(id: string, reason?: string): Promise<Booking> {
  const res = await api.patch<Booking>(`/bookings/${id}/cancel`, { reason })
  return res.data
}

export async function rescheduleBooking(id: string, new_slot_id: string): Promise<{ old_id: string; new_id: string }> {
  const res = await api.patch(`/bookings/${id}/reschedule`, { new_slot_id })
  return res.data
}

export async function organiserBookings(params: { status?: string | null; page?: number; pageSize?: number } = {}): Promise<Paginated<Booking>> {
  const res = await api.get<Paginated<Booking>>("/organiser/bookings", {
    params: {
      status: params.status === "all" ? undefined : params.status,
      page: params.page ?? 1,
      page_size: params.pageSize ?? 10,
    },
  })
  return res.data
}

export async function confirmBooking(id: string): Promise<Booking> {
  const res = await api.patch<Booking>(`/bookings/${id}/confirm`)
  return res.data
}

export async function organiserCancelBooking(id: string, reason?: string): Promise<Booking> {
  const res = await api.patch<Booking>(`/organiser/bookings/${id}/cancel`, { reason })
  return res.data
}

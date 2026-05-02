import { Navigate, Route, Routes } from "react-router-dom"

import { AppShell } from "./components/layout/AppShell"
import { AuthShell } from "./components/layout/AuthShell"
import { RequireAuth } from "./components/layout/RequireAuth"
import { AdminStatsPage } from "./pages/admin/AdminStatsPage"
import { AdminUsersPage } from "./pages/admin/AdminUsersPage"
import { BookingPage } from "./pages/booking/BookingPage"
import { ConfirmationPage } from "./pages/booking/ConfirmationPage"
import { MyAppointmentsPage } from "./pages/customer/MyAppointmentsPage"
import { ProfilePage } from "./pages/customer/ProfilePage"
import { ReschedulePage } from "./pages/customer/ReschedulePage"
import { AppointmentTypesPage } from "./pages/organiser/AppointmentTypesPage"
import { NewTypePage } from "./pages/organiser/NewTypePage"
import { OrganiserBookingsPage } from "./pages/organiser/OrganiserBookingsPage"
import { HomePage } from "./pages/public/HomePage"
import { LoginPage } from "./pages/public/LoginPage"
import { OtpPage } from "./pages/public/OtpPage"
import { SignupPage } from "./pages/public/SignupPage"

export function App() {
  return (
    <Routes>
      <Route element={<AuthShell />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/otp" element={<OtpPage />} />
      </Route>
      <Route element={<AppShell />}>
        <Route index element={<HomePage />} />
        <Route path="/book/:appointmentTypeId" element={<BookingPage />} />
        <Route path="/book/share/:shareToken" element={<BookingPage share />} />
        <Route element={<RequireAuth />}>
          <Route path="/booking/:bookingId/confirmation" element={<ConfirmationPage />} />
          <Route path="/booking/:bookingId/reschedule" element={<ReschedulePage />} />
          <Route path="/me/appointments" element={<MyAppointmentsPage />} />
          <Route path="/me/profile" element={<ProfilePage />} />
        </Route>
        <Route element={<RequireAuth roles={["organiser", "admin"]} />}>
          <Route path="/organiser/types" element={<AppointmentTypesPage />} />
          <Route path="/organiser/types/new" element={<NewTypePage />} />
          <Route path="/organiser/bookings" element={<OrganiserBookingsPage />} />
        </Route>
        <Route element={<RequireAuth roles={["admin"]} />}>
          <Route path="/admin/users" element={<AdminUsersPage />} />
          <Route path="/admin/stats" element={<AdminStatsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

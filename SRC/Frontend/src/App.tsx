import { Navigate, Route, Routes, useParams } from "react-router-dom"

import { AdminLayout } from "./components/admin/AdminLayout"
import { AppShell } from "./components/layout/AppShell"
import { AuthShell } from "./components/layout/AuthShell"
import { RequireAuth } from "./components/layout/RequireAuth"
import { AdminDashboardPage } from "./pages/admin/AdminDashboardPage"
import { AnalyticsDashboardPage } from "./pages/admin/AnalyticsDashboardPage"
import { AdminOrganizationDetailPage } from "./pages/admin/AdminOrganizationDetailPage"
import { AdminOrganizationsPage } from "./pages/admin/AdminOrganizationsPage"
import { AdminUsersPage } from "./pages/admin/AdminUsersPage"
import { ManualBookingPage } from "./pages/admin/ManualBookingPage"
import { PackagesPage } from "./pages/admin/PackagesPage"
import { ThemeSettingsPage } from "./pages/admin/ThemeSettingsPage"
import { WaitlistDashboardPage } from "./pages/admin/WaitlistDashboardPage"
import { BookingPage } from "./pages/booking/BookingPage"
import { ConfirmationPage } from "./pages/booking/ConfirmationPage"
import { PaymentPage } from "./pages/booking/PaymentPage"
import { MyAppointmentsPage } from "./pages/customer/MyAppointmentsPage"
import { ProfilePage } from "./pages/customer/ProfilePage"
import { ReschedulePage } from "./pages/customer/ReschedulePage"
import { AppointmentTypesPage } from "./pages/organiser/AppointmentTypesPage"
import { MailTemplateEditorPage } from "./pages/organiser/MailTemplateEditorPage"
import { MailTemplatesPage } from "./pages/organiser/MailTemplatesPage"
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
          <Route path="/booking/:bookingId/pay" element={<PaymentPage />} />
          <Route path="/booking/:bookingId/payment" element={<PaymentRedirect />} />
          <Route path="/booking/:bookingId/confirmation" element={<ConfirmationPage />} />
          <Route path="/booking/:bookingId/reschedule" element={<ReschedulePage />} />
          <Route path="/me/appointments" element={<MyAppointmentsPage />} />
          <Route path="/me/profile" element={<ProfilePage />} />
        </Route>
        <Route element={<RequireAuth roles={["organiser", "admin"]} />}>
          <Route path="/organiser/types" element={<AppointmentTypesPage />} />
          <Route path="/organiser/types/new" element={<NewTypePage />} />
          <Route path="/organiser/types/:appointmentTypeId" element={<NewTypePage />} />
          <Route path="/organiser/bookings" element={<OrganiserBookingsPage />} />
          <Route path="/organiser/mail-templates" element={<MailTemplatesPage />} />
          <Route path="/organiser/mail-templates/new" element={<MailTemplateEditorPage />} />
          <Route path="/organiser/mail-templates/:templateId" element={<MailTemplateEditorPage />} />
        </Route>
        <Route element={<RequireAuth roles={["organiser", "admin"]} />}>
          <Route element={<AdminLayout />}>
            <Route path="/admin" element={<AdminDashboardPage />} />
            <Route path="/admin/analytics" element={<AnalyticsDashboardPage />} />
            <Route path="/admin/waitlist" element={<WaitlistDashboardPage />} />
            <Route path="/admin/manual-booking" element={<ManualBookingPage />} />
            <Route path="/admin/packages" element={<PackagesPage />} />
            <Route path="/admin/theme" element={<ThemeSettingsPage />} />
            <Route element={<RequireAuth roles={["admin"]} />}>
              <Route path="/admin/users" element={<AdminUsersPage />} />
              <Route path="/admin/organizations" element={<AdminOrganizationsPage />} />
              <Route path="/admin/organizations/:orgId" element={<AdminOrganizationDetailPage />} />
            </Route>
          </Route>
          <Route path="/admin/stats" element={<Navigate to="/admin" replace />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

function PaymentRedirect() {
  const { bookingId } = useParams()
  if (!bookingId) return <Navigate to="/" replace />
  return <Navigate to={`/booking/${bookingId}/pay`} replace />
}

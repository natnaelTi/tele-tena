import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { LocaleProvider } from "./hooks/useLocale";
import { SessionProvider } from "./hooks/useSession";
import {
  AuthLayout,
  PublicLayout,
  RequireSession,
  WorkspaceLayout,
} from "./layouts/Layouts";
import Homepage, { ClinicianInvitation } from "./pages/Homepage";
import SignIn from "./pages/SignIn";
import Onboarding from "./pages/Onboarding";
import {
  Appointments,
  Booking,
  Discovery,
  PatientHome,
  Payments,
  BookingLink,
} from "./pages/Patient";
import {
  Availability,
  CareRecords,
  ClinicianToday,
  CareRecordDetail,
  ClinicianEarnings,
  PendingFeature,
  Services,
} from "./pages/Clinician";
import Account from "./pages/Account";
import { Applications, FinancialDisputes, Scopes } from "./pages/Admin";
import ConsultationPage, { ConsultationRoomPage } from "./pages/ConsultationPage";
import Showcase from "./pages/Showcase";
import { ClinicianRequestInbox, PatientOpenRequests, PublicClinicianProfile } from "./pages/OpenRequests";
import { ClinicianScopeApplications, VettingQueue } from "./pages/Vetting";
import { ClinicianAffiliations, ClinicMembershipPortal, ClinicReview } from "./pages/Clinics";
import PWAUpdateNotice from "./components/PWAUpdateNotice";
import "./App.css";
export default function App() {
  return (
    <BrowserRouter basename={import.meta.env.PROD ? "/teletena" : "/"}>
      <SessionProvider>
        <LocaleProvider>
          <PWAUpdateNotice />
          <a className="skip-link" href="#main-content">
            Skip to content
          </a>
          <Routes>
            <Route element={<PublicLayout />}>
              <Route path="/" element={<Homepage />} />
              <Route path="/for-clinicians" element={<ClinicianInvitation />} />
              <Route
                path="/showcase"
                element={
                  import.meta.env.DEV ? (
                    <Showcase />
                  ) : (
                    <Navigate to="/" replace />
                  )
                }
              />
            </Route>
            <Route element={<AuthLayout />}>
              <Route path="/sign-in" element={<SignIn />} />
            <Route element={<RequireSession />}>
              <Route path="/onboarding" element={<Onboarding />} />
            </Route>
            </Route>
            <Route element={<RequireSession />}>
              <Route path="/consultation/:id/room" element={<><div className="demo-bar" role="note">Demonstration environment — no real payments or clinical care.</div><ConsultationRoomPage /></>} />
              <Route
                path="/patient"
                element={<WorkspaceLayout kind="patient" />}
              >
                <Route index element={<PatientHome />} />
                <Route path="discovery" element={<Discovery />} />
                <Route path="requests" element={<PatientOpenRequests />} />
                <Route path="clinicians/:clinicianId" element={<PublicClinicianProfile />} />
                <Route path="book/:offering" element={<Booking />} />
                <Route path="book-link/:token" element={<BookingLink />} />
                <Route path="appointments" element={<Appointments />} />
                <Route path="account" element={<Account />} />
                <Route path="clinic-access" element={<ClinicMembershipPortal />} />
                <Route path="payments" element={<Payments />} />
                <Route
                  path="consultations/:id"
                  element={<ConsultationPage />}
                />
              </Route>
              <Route
                path="/clinician"
                element={<WorkspaceLayout kind="clinician" />}
              >
                <Route index element={<ClinicianToday />} />
                <Route
                  path="appointments"
                  element={<Appointments base="/clinician" />}
                />
                <Route path="availability" element={<Availability />} />
                <Route path="services" element={<Services />} />
                <Route path="account" element={<Account />} />
                <Route path="clinic-access" element={<ClinicMembershipPortal />} />
                <Route
                  path="consultations/:id"
                  element={<ConsultationPage />}
                />
                <Route path="requests" element={<ClinicianRequestInbox />} />
                <Route path="care" element={<CareRecords />} />
                <Route path="care/:id" element={<CareRecordDetail />} />
                <Route path="earnings" element={<ClinicianEarnings />} />
                <Route path="vetting" element={<ClinicianScopeApplications />} />
                <Route path="affiliations" element={<ClinicianAffiliations />} />
              </Route>
              <Route path="/admin" element={<WorkspaceLayout kind="admin" />}>
                <Route index element={<Applications />} />
                <Route path="scopes" element={<Scopes />} />
                <Route path="vetting" element={<VettingQueue />} />
                <Route path="clinics" element={<ClinicReview />} />
                <Route path="financial-disputes" element={<FinancialDisputes />} />
                <Route
                  path="exceptions"
                  element={
                    <PendingFeature
                      title="Operational exceptions"
                      description="A dedicated exceptions queue is planned. No patient-record access is granted by this workspace."
                    />
                  }
                />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </LocaleProvider>
      </SessionProvider>
    </BrowserRouter>
  );
}

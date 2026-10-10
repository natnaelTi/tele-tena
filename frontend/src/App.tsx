import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { LocaleProvider } from "./hooks/useLocale";
import { SessionProvider } from "./hooks/useSession";
import {
  AuthLayout,
  PublicLayout,
  RequireSession,
  MedicalLeadLayout,
  WorkspaceLayout,
} from "./layouts/Layouts";
import Homepage, { ClinicianInvitation } from "./pages/Homepage";
import BookingConfirmation from "./pages/BookingConfirmation";
import {ClinicianOffers,ClinicianOfferDetail} from "./pages/ClinicianOffers";
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
import ServiceDetails from "./pages/ServiceDetails";
import Account from "./pages/Account";
import { AdminOverview, Applications, FinancialDisputes, Scopes, ServiceCatalog } from "./pages/Admin";
import ConsultationPage, { ConsultationRoomPage } from "./pages/ConsultationPage";
import Showcase from "./pages/Showcase";
import { ClinicianRequestInbox, PatientOpenRequests, PatientRequestDetail, PatientRequestOfferDetail, PublicClinicianProfile } from "./pages/OpenRequests";
import { ClinicianScopeApplications, VettingQueue, VettingRubricManagementPage } from "./pages/Vetting";
import { ClinicianAffiliations, ClinicMembershipPortal, ClinicReview } from "./pages/Clinics";
import ClinicCalendar from "./pages/ClinicCalendar";
import Couples, { CoupleInvitation } from './pages/Couples';
import Relationships, { RelationshipInvitationEntry } from "./pages/Relationships";
import FinancialActivityDetail from "./pages/FinancialActivity";
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
              <Route path="/couple-invitation" element={<CoupleInvitation />} />
              <Route path="/relationship-invitation" element={<RelationshipInvitationEntry />} />
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
              <Route path="/admin/rubrics" element={<MedicalLeadLayout />}><Route index element={<VettingRubricManagementPage />} /></Route>
              <Route path="/consultation/:id/room" element={<><div className="demo-bar" role="note">Demonstration environment — no real payments or clinical care.</div><ConsultationRoomPage /></>} />
              <Route path="/clinic" element={<WorkspaceLayout kind="clinic" />}>
                <Route index element={<ClinicMembershipPortal workspace />} />
                <Route path="calendar" element={<ClinicCalendar />} />
              </Route>
              <Route
                path="/patient"
                element={<WorkspaceLayout kind="patient" />}
              >
                <Route index element={<PatientHome />} />
                <Route path="discovery" element={<Discovery />} />
                <Route path="requests" element={<PatientOpenRequests />} />
                <Route path="requests/:requestId" element={<PatientRequestDetail />} />
                <Route path="requests/:requestId/offers/:offerId" element={<PatientRequestOfferDetail />} />
                <Route path="clinicians/:clinicianId" element={<PublicClinicianProfile />} />
                <Route path="services/:offering" element={<ServiceDetails />} />
                <Route path="book/:offering" element={<Booking />} />
                <Route path="book-link/:token" element={<BookingLink />} />
                <Route path="booked/:id" element={<BookingConfirmation />} />
                <Route path="appointments" element={<Appointments />} />
                <Route path="account" element={<Account />} />
                <Route path="couples" element={<Couples />} />
                <Route path="relationships" element={<Relationships />} />
                <Route path="clinic-access" element={<ClinicMembershipPortal />} />
                <Route path="payments" element={<Payments />} />
                <Route path="payments/transactions/:activityId" element={<FinancialActivityDetail />} />
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
                <Route path="offers" element={<ClinicianOffers />} />
                <Route path="offers/:offerId" element={<ClinicianOfferDetail />} />
                <Route path="care" element={<CareRecords />} />
                <Route path="care/:id" element={<CareRecordDetail />} />
                <Route path="earnings" element={<ClinicianEarnings />} />
                <Route path="earnings/transactions/:activityId" element={<FinancialActivityDetail />} />
                <Route path="vetting" element={<ClinicianScopeApplications />} />
                <Route path="affiliations" element={<ClinicianAffiliations />} />
              </Route>
              <Route path="/admin" element={<WorkspaceLayout kind="admin" />}>
                <Route index element={<AdminOverview />} />
                <Route path="applications" element={<Applications />} />
                <Route path="scopes" element={<Scopes />} />
                <Route path="services" element={<ServiceCatalog />} />
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

import { api } from './api'

type Sharing = { name: boolean; history: boolean }
export type Profile = { kind: 'patient' | 'clinician'; display_name: string; history: string; share_name: boolean; share_history: boolean; languages?: string }
export type Session = { user: string; roles: string[]; profile: Profile | null; csrf_token: string; simulation: boolean }
export type Service = { id: string; label: string }
export type Offer = { id: string; clinician_id:string; display_name: string; label: string; price: number; minutes: number; schedule_id?: string | null; schedule_timezone?: string | null; consultation_format?: 'video' | 'audio' }
export type Application = { user: string; display_name: string; statement: string; status: 'Pending' | 'Approved' | 'Rejected'; requested_services?: string[]; requested_service_labels?:string[]; resume_uploaded?: boolean; resume_size?: number; submission_date_available?: boolean; submitted_at?: string | null; evidence_complete?: boolean; verified_contacts?: {channel: string; contact: string; verified_at: string}[] }
export type Disclosure = { request: string; name?: string; history?: string }
export type Appointment = { id: string; start: string; end: string; state: string; price: number; minutes: number; service_label: string; disclosure: Disclosure; timezone?: string | null; consultation_format?: string; confirmation_mode?: string; expires_at?: string | null; confirmed_at?: string | null; cancelled_by?: string | null; cancelled_at?: string | null; cancel_reason?: string | null; call_state?: string; call_ended?: string | null; documentation_state?: string | null; display_identity?:string }
export type Window = { start: string; end: string }
export type TimeSlot = {start: string; end: string; local_time: string; timezone: string; schedule_timezone: string | null}
export type ScheduleInterval = {weekday: number; start_local: string; end_local: string}
export type ScheduleException = {date: string; kind: 'unavailable' | 'replace' | 'break'; start_local?: string | null; end_local?: string | null}
export type Schedule = {id: string; offering: string; schedule_name: string; timezone: string; consultation_format: 'audio'|'video'; confirmation_mode: 'automatic'|'manual'; minimum_notice_minutes: number; horizon_days: number; buffer_before: number; buffer_after: number; status: 'Draft'|'Published'|'Paused'; service_label: string; minutes: number; intervals: ScheduleInterval[]; exceptions: ScheduleException[]}

/** Domain-facing API. Frappe method names and HTTP/CSRF details stay out of views. */
export const journeyApi = {
  session: () => api<Session>('session'),
  services: () => api<Service[]>('services'),
  discover: (service = '') => api<Offer[]>('discover', service ? { service } : {}),
  wallet: () => api<{ available: number; reserved: number }>('wallet'),
  applications: () => api<Application[]>('applications'),
  serviceScopes: () => api<{ clinician: string; service: string; status: string }[]>('service_scopes'),
  appointments: () => api<Appointment[]>('appointments'),
  calendar: (offering: string, from_date: string, display_timezone: string) =>
    api<{days:{date:string;slots:TimeSlot[]}[];timezone:string;schedule_timezone:string|null;duration:number;format:string;price:number}>('tele_tena.api.scheduling.calendar', { offering, from_date, days: 35, display_timezone }),
  schedules: () => api<Schedule[]>('tele_tena.api.scheduling.schedules'),
  saveSchedule: (data: Record<string, unknown>) => api('tele_tena.api.scheduling.save_schedule', data, true),
  bookingLink: (offering: string) => api<{token:string}>('tele_tena.api.scheduling.booking_link',{offering},true),
  resolveBookingLink: (token: string) => api<{offering:string;service:string;clinician:string;price:number;minutes:number;format:'audio'|'video';timezone:string}>('tele_tena.api.scheduling.resolve_booking_link',{token}),
  appointmentDetail: (appointment: string) => api<any>('tele_tena.api.presentation.appointment_detail', { appointment }),
  cancelAppointment: (appointment: string, reason: string) => api('tele_tena.api.presentation.cancel_appointment', { appointment, reason }, true),
  respondToRequest: (appointment: string, decision: 'confirm'|'decline') => api('tele_tena.api.presentation.respond_to_request', { appointment, decision }, true),
  saveNoteDraft: (appointment: string, private_note: string, patient_summary: string) => api('tele_tena.api.presentation.save_note_draft', { appointment, private_note, patient_summary }, true),
  previewSummary: (appointment: string, summary?:string) => api<{revision:number;summary:string}>('tele_tena.api.presentation.preview_patient_summary', { appointment, summary }, true),
  finalizeConsultation: (appointment: string, publish_summary: boolean) => api('tele_tena.api.presentation.finalize_consultation', { appointment, publish_summary }, true),
  careDirectory: (data: Record<string, unknown>) => api<{rows:any[];total:number;page:number;page_size:number;pages:number}>('tele_tena.api.presentation.care_directory', data),
  careDetail: (appointment: string) => api<any>('tele_tena.api.presentation.care_detail', { appointment }),
  carePatientRecord: (appointment: string) => api<{patient_label:string;encounters:any[]}>('tele_tena.api.presentation.care_patient_record', { appointment }),
  preferences: () => api<{locale:string;timezone:string|null;notification_preferences?:string|null}>('tele_tena.api.presentation.preferences'),
  savePreferences: (locale:string, timezone_name:string) => api('tele_tena.api.presentation.save_preferences', {locale,timezone_name}, true),
  tourState: (tour_id:string) => api<{role:string;state:string|null;version:number}>('tele_tena.api.presentation.tour_state', {tour_id}),
  saveTourState: (tour_id:string,state:'Dismissed'|'Completed') => api('tele_tena.api.presentation.save_tour_state', {tour_id,state}, true),
  resumeStatus: () => api<{uploaded:boolean;filename?:string;content_size?:number;revision?:number}>('tele_tena.api.presentation.resume_status'),
  uploadResume: (filename:string,content_base64:string) => api('tele_tena.api.presentation.upload_resume', {filename,content_base64}, true),
  removeResume: () => api('tele_tena.api.presentation.remove_resume', {}, true),
  windows: (offering: string) => api<{ windows: Window[]; busy: Window[] }>('windows', { offering }),
  logout: () => api('frappe.handler.logout', {}, true),
  saveProfile: (data: Record<string, unknown>) => api('save_profile', data, true),
  saveService: (service: string, label: string) => api('save_service', { service, label }, true),
  reviewApplication: (clinician: string, decision: 'Approved' | 'Rejected') =>
    api('review', { clinician, decision }, true),
  reviewServiceScope: (clinician: string, service: string, decision: 'Approved' | 'Revoked') =>
    api('review_service_scope', { clinician, service, decision }, true),
  apply: (statement: string, requested_services:string[] = []) => api('apply', { statement, requested_services }, true),
  publish: (service: string, price: string, minutes: string) => api('publish', { service, price, minutes }, true),
  walletActivity: () => api<{available:number;reserved:number;currency:string;activity:{kind:string;amount:number;created:string}[]}>('tele_tena.api.presentation.wallet_summary'),
  simulatedDeposit: (retryKey: string) => api('simulated_deposit', { amount: 10000, retry_key: retryKey }, true),
  preview: (requestText: string, sharing: Sharing) =>
    api<{ disclosure: Disclosure }>('preview', { request_text: requestText, sharing }, true),
  book: (data: Record<string, unknown>) => api('book', data, true),
  publishRequest: (data: Record<string, unknown>) => api<any>('tele_tena.api.open_requests.publish_request', data, true),
  myRequests: () => api<any[]>('tele_tena.api.open_requests.my_requests'),
  findMoreOptions: (request_id: string) => api<any>('tele_tena.api.open_requests.find_more_options', {request_id}, true),
  cancelRequest: (request_id: string) => api<any>('tele_tena.api.open_requests.close_request', {request_id}, true),
  respondOffer: (request_id: string, offer_id: string, decision: 'accept'|'decline', sharing?:Sharing, expected_disclosure?:Disclosure) => api<any>('tele_tena.api.open_requests.respond_offer', {request_id,offer_id,decision,sharing,expected_disclosure}, true),
  requestPresence: () => api<any>('tele_tena.api.open_requests.request_presence'),
  setRequestPresence: (ready: boolean) => api<any>('tele_tena.api.open_requests.set_request_presence', {ready}, true),
  clinicianRequests: () => api<any[]>('tele_tena.api.open_requests.clinician_requests'),
  clinicianOffers: (page=0) => api<{items:any[];page:number;has_more:boolean}>('tele_tena.api.open_requests.clinician_offers', {page}),
  acknowledgeInboxFetch: (request_ids:string[]) => api<any>('tele_tena.api.open_requests.acknowledge_inbox_fetch',{request_ids},true),
  submitOffer: (data: Record<string, unknown>) => api<any>('tele_tena.api.open_requests.submit_offer', data, true),
  withdrawOffer: (offer_id: string) => api<any>('tele_tena.api.open_requests.withdraw_offer', {offer_id}, true),
  recordOfferAcceptFailure: (request_id:string,offer_id:string,attempt_key:string,reason:string) => api<any>('tele_tena.api.open_requests.record_accept_failure',{request_id,offer_id,attempt_key,reason},true),
  publicClinician: (clinician_id:string) => api<any>('tele_tena.api.open_requests.clinician_profile',{clinician_id}),
  vettingServices: () => api<any[]>('tele_tena.api.vetting.vetting_services'),
  myScopeApplications: () => api<any[]>('tele_tena.api.vetting.my_scope_applications'),
  saveScopeApplication: (service:string, values:Record<string,unknown>, submit=false) => api<any>('tele_tena.api.vetting.save_scope_application',{service,values,submit:submit?1:0},true),
  reviewScopeApplication: (data:Record<string,unknown>) => api<any>('tele_tena.api.vetting.review_scope_application',data,true),
  assignScopeReviewer: (application:string,reviewer:string) => api<any>('tele_tena.api.vetting.assign_scope_reviewer',{application,reviewer},true),
}

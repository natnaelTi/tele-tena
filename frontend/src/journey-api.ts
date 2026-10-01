import { api } from './api'

type Sharing = { name: boolean; history: boolean }
export type Profile = { kind: 'patient' | 'clinician'; display_name: string; history: string; share_name: boolean; share_history: boolean }
export type Session = { user: string; roles: string[]; profile: Profile | null; csrf_token: string; simulation: boolean }
export type Service = { id: string; label: string }
export type Offer = { id: string; display_name: string; label: string; price: number; minutes: number }
export type Application = { user: string; statement: string; status: 'Pending' | 'Approved' | 'Rejected' }
export type Disclosure = { request: string; name?: string; history?: string }
export type Appointment = { id: string; start: string; end: string; state: string; price: number; minutes: number; service_label: string; disclosure: Disclosure }
export type Window = { start: string; end: string }

/** Domain-facing API. Frappe method names and HTTP/CSRF details stay out of views. */
export const journeyApi = {
  session: () => api<Session>('session'),
  services: () => api<Service[]>('services'),
  discover: (service = '') => api<Offer[]>('discover', service ? { service } : {}),
  wallet: () => api<{ available: number; reserved: number }>('wallet'),
  applications: () => api<Application[]>('applications'),
  serviceScopes: () => api<{ clinician: string; service: string; status: string }[]>('service_scopes'),
  appointments: () => api<Appointment[]>('appointments'),
  windows: (offering: string) => api<{ windows: Window[]; busy: Window[] }>('windows', { offering }),
  logout: () => api('frappe.handler.logout', {}, true),
  saveProfile: (data: Record<string, unknown>) => api('save_profile', data, true),
  saveService: (service: string, label: string) => api('save_service', { service, label }, true),
  reviewApplication: (clinician: string, decision: 'Approved' | 'Rejected') =>
    api('review', { clinician, decision }, true),
  reviewServiceScope: (clinician: string, service: string, decision: 'Approved' | 'Revoked') =>
    api('review_service_scope', { clinician, service, decision }, true),
  apply: (statement: string) => api('apply', { statement }, true),
  publish: (service: string, price: string, minutes: string) => api('publish', { service, price, minutes }, true),
  addAvailability: (start: string, end: string) => api('add_availability', { start, end }, true),
  simulatedDeposit: (retryKey: string) => api('simulated_deposit', { amount: 10000, retry_key: retryKey }, true),
  preview: (requestText: string, sharing: Sharing) =>
    api<{ disclosure: Disclosure }>('preview', { request_text: requestText, sharing }, true),
  book: (data: Record<string, unknown>) => api('book', data, true),
}

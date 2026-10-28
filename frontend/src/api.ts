export class ApiError extends Error {
  code: string
  status: number
  constructor(code: string, status = 0) { super('Request failed'); this.code = code; this.status = status }
}
let csrf = ''
let interfaceLocale='en'
export function setInterfaceLocale(value:string){interfaceLocale=['en','am','om'].includes(value)?value:'en'}
export function setCsrf(token: string) { csrf = token }
async function classifyError(response: Response, method: string): Promise<ApiError> {
  const result = await response.json().catch(() => ({}))
  let code = typeof result.tele_tena_error === 'string' ? result.tele_tena_error : 'unknown'
  if ((response.status === 401 || response.status === 403) && code === 'unknown' && !method.includes('contact_auth.session')) {
    try {
      const session = await fetch('/api/method/tele_tena.api.contact_auth.session', { credentials: 'same-origin', cache: 'no-store' })
      const body = await session.json()
      code = body.message?.authenticated ? 'permission_denied' : 'session_required'
    } catch { code = 'permission_denied' }
  }
  return new ApiError(code, response.status)
}
export async function api<T>(method: string, data: Record<string, unknown> = {}, post = false, signal?: AbortSignal): Promise<T> {
  const path = method.startsWith('frappe.') || method.startsWith('tele_tena.') ? '/api/method/' + method : '/api/method/tele_tena.api.journey.' + method
  const query = new URLSearchParams(Object.entries(data).map(([k, v]) => [k, String(v)]))
  const response = await fetch(path + (!post && query.size ? '?' + query : ''), {
    method: post ? 'POST' : 'GET', credentials: 'same-origin', cache: 'no-store', signal,
    headers: post ? { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf,'X-TeleTena-Locale':interfaceLocale } : {'X-TeleTena-Locale':interfaceLocale},
    body: post ? JSON.stringify(data) : undefined,
  })
  if (!response.ok) {
    throw await classifyError(response, method)
  }
  const result = await response.json()
  return result.message as T
}
export async function signIn(email: string, password: string) {
  let response: Response
  try {
    response = await fetch('/api/method/login', { method: 'POST', credentials: 'same-origin', cache: 'no-store',
      headers: { 'Content-Type': 'application/json','X-TeleTena-Locale':interfaceLocale }, body: JSON.stringify({ usr: email, pwd: password }) })
  } catch {
    throw new ApiError('network_error')
  }
  if (!response.ok) {
    // Do not surface Frappe's raw login response or distinguish unknown users.
    if (response.status === 401 || response.status === 403 || response.status === 417)
      throw new ApiError('credentials_invalid', response.status)
    throw new ApiError(response.status >= 500 ? 'service_unavailable' : 'login_failed', response.status)
  }
}

export async function phoneAuth<T>(method: string, data: Record<string, unknown>, csrf?: string): Promise<T> {
  const bootstrap = method === 'csrf_token'
  const response = await fetch('/api/method/tele_tena.api.phone_auth.' + method, {
    method: bootstrap ? 'GET' : 'POST', credentials: 'same-origin', cache: 'no-store',
    headers: bootstrap ? {'X-TeleTena-Locale':interfaceLocale} : { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf || '','X-TeleTena-Locale':interfaceLocale },
    body: bootstrap ? undefined : JSON.stringify(data),
  })
  if (!response.ok) {
    throw await classifyError(response, 'phone_auth.' + method)
  }
  return (await response.json()).message as T
}

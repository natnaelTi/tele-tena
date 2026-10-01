export class ApiError extends Error {
  code: string
  constructor(code: string) { super('Request failed'); this.code = code }
}
let csrf = ''
export function setCsrf(token: string) { csrf = token }
export async function api<T>(method: string, data: Record<string, unknown> = {}, post = false): Promise<T> {
  const path = method.startsWith('frappe.') || method.startsWith('tele_tena.') ? '/api/method/' + method : '/api/method/tele_tena.api.journey.' + method
  const query = new URLSearchParams(Object.entries(data).map(([k, v]) => [k, String(v)]))
  const response = await fetch(path + (!post && query.size ? '?' + query : ''), {
    method: post ? 'POST' : 'GET', credentials: 'same-origin', cache: 'no-store',
    headers: post ? { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf } : {},
    body: post ? JSON.stringify(data) : undefined,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new ApiError(typeof error.tele_tena_error === 'string' ? error.tele_tena_error : 'unknown')
  }
  const result = await response.json()
  return result.message as T
}
export async function signIn(email: string, password: string) {
  const response = await fetch('/api/method/login', { method: 'POST', credentials: 'same-origin', cache: 'no-store',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ usr: email, pwd: password }) })
  if (!response.ok) throw new Error('Sign in failed')
}

export async function phoneAuth<T>(method: string, data: Record<string, unknown>, csrf?: string): Promise<T> {
  const bootstrap = method === 'csrf_token'
  const response = await fetch('/api/method/tele_tena.api.phone_auth.' + method, {
    method: bootstrap ? 'GET' : 'POST', credentials: 'same-origin', cache: 'no-store',
    headers: bootstrap ? {} : { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf || '' },
    body: bootstrap ? undefined : JSON.stringify(data),
  })
  if (!response.ok) {
    const result = await response.json().catch(() => ({}))
    throw new ApiError(typeof result.tele_tena_error === 'string' ? result.tele_tena_error : 'unknown')
  }
  return (await response.json()).message as T
}

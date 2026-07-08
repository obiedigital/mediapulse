const API_BASE = import.meta.env.VITE_API_BASE ?? "/api"
const TOKEN_KEY = "mp_token"

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers = new Headers(options.headers)
  headers.set("Accept", "application/json")
  if (token) headers.set("Authorization", `Bearer ${token}`)

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = await response.json()
      detail = body.detail ?? detail
    } catch {
      // response wasn't JSON — keep statusText
    }
    throw new ApiError(response.status, detail)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export function apiGet<T>(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  const query = params
    ? "?" + new URLSearchParams(
        Object.entries(params).filter(([, v]) => v !== undefined && v !== "") as [string, string][],
      ).toString()
    : ""
  return request<T>(`${path}${query}`)
}

export function apiPost<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
}

export async function login(email: string, password: string) {
  const body = new URLSearchParams({ username: email, password })
  const token = getToken()
  const headers: Record<string, string> = { "Content-Type": "application/x-www-form-urlencoded" }
  const response = await fetch(`${API_BASE}/auth/login`, { method: "POST", headers, body })
  if (!response.ok) {
    let detail = "Login failed"
    try {
      detail = (await response.json()).detail ?? detail
    } catch {
      /* ignore */
    }
    throw new ApiError(response.status, detail)
  }
  void token
  return response.json()
}

export async function downloadCsv(path: string, params: Record<string, string | undefined>, filename: string) {
  const query = "?" + new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== "") as [string, string][],
  ).toString()
  const token = getToken()
  const headers = new Headers()
  if (token) headers.set("Authorization", `Bearer ${token}`)
  const response = await fetch(`${API_BASE}${path}${query}`, { headers })
  if (!response.ok) throw new ApiError(response.status, "Export failed")
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

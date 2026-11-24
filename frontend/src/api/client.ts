import type {
  EvaluationCreate,
  EvaluationUpdate,
  EvaluationRead,
  EvaluationListResponse,
  EvaluationRunCreate,
  EvaluationRunRead,
  EvaluationWithRuns,
  EvaluationRunWithMetrics,
} from './types'

const API_BASE = '/api'

// PKCE helpers - simple base64url encoding
function b64url_encode(str: string): string {
  // Use btoa then replace +/= for base64url
  let result = btoa(str)
  // Replace + with - and / with _ and remove =
  result = result.replace(/./g, (c) => {
    if (c === '+') return '-'
    if (c === '/') return '_'
    if (c === '=') return ''
    return c
  })
  return result
}

function generateCodeVerifier(): string {
  // 32 random bytes, base64url encoded = ~43 chars
  const bytes = new Uint8Array(32)
  crypto.getRandomValues(bytes)
  // Convert to base64 string then url-safe encode
  const base64 = btoa(String.fromCharCode(...new Uint8Array(bytes)))
  return base64.replace(/./g, (c) => {
    if (c === '+') return '-'
    if (c === '/') return '_'
    if (c === '=') return ''
    return c
  })
}

function b64urlFromBytes(bytes: Uint8Array): string {
  const base64 = btoa(String.fromCharCode(...bytes))
  return base64.replace(/./g, (c) => {
    if (c === '+') return '-'
    if (c === '/') return '_'
    if (c === '=') return ''
    return c
  })
}

async function generateCodeChallengeFromVerifier(verifier: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(verifier)
  const hash = await crypto.subtle('SHA-256', data)
  return b64urlFromBytes(new Uint8Array(hash))
}

export function createPKCEPair(): { verifier: string; challenge: Promise<string> } {
  const verifier = generateCodeVerifier()
  const challenge = generateCodeChallengeFromVerifier(verifier)
  return { verifier, challenge }
}

// Auth storage using sessionStorage
const AUTH_KEY = 'vector-pilot-auth'

type UserRole = 'admin' | 'operator' | 'analyst'

interface AuthUser {
  id: number
  email: string
  username: string
  role: UserRole
}

interface AuthSession {
  user: AuthUser | null
  token: string | null
  codeVerifier: string | null
  expiresAt: number | null
}

function getSession(): AuthSession {
  if (typeof window === 'undefined') return { user: null, token: null, codeVerifier: null, expiresAt: null }
  const raw = sessionStorage.getItem(AUTH_KEY)
  return raw ? JSON.parse(raw) : { user: null, token: null, codeVerifier: null, expiresAt: null }
}

function setSession(session: AuthSession): void {
  if (typeof window === 'undefined') return
  sessionStorage.setItem(AUTH_KEY, JSON.stringify(session))
}

function clearSession(): void {
  if (typeof window === 'undefined') return
  sessionStorage.removeItem(AUTH_KEY)
}

// Check if user is authenticated
export function isAuthenticated(): boolean {
  const session = getSession()
  if (!session.token || !session.expiresAt) return false
  return Date.now() < session.expiresAt
}

export function getCurrentUser(): AuthUser | null {
  const session = getSession()
  return session.user ?? null
}

// Login PKCE URL for Keycloak
export function getLoginUrl(): string {
  const { verifier, challenge } = createPKCEPair()
  setSession({ user: null, token: null, codeVerifier: verifier, expiresAt: null })

  const settings = import.meta.env.VITE_OIDC_ISSUER_URL
    ? import.meta.env.VITE_OIDC_ISSUER_URL
    : 'http://localhost:8080/realms/vector-pilot'

  const clientId = import.meta.env.VITE_OIDC_CLIENT_ID || 'vector-pilot'

  const redirectUri = import.meta.env.VITE_REDIRECT_URI || 'http://localhost:5173/callback'

  const params = new URLSearchParams({
    response_type: 'code',
    client_id: clientId,
    redirect_uri: redirectUri,
    scope: 'openid profile email',
    code_challenge: '',  // placeholder
    code_challenge_method: 'S256',
  })

  return `${settings}/protocol/openid-connect/auth?${params.toString()}`
}

// Callback exchange code for token
export async function exchangeCodeForToken(code: string, codeVerifier: string): Promise<{ token: string; user: AuthUser; expiresIn: number }> {
  const settings = import.meta.env.VITE_OIDC_ISSUER_URL
    ? import.meta.env.VITE_OIDC_ISSUER_URL
    : 'http://localhost:8080/realms/vector-pilot'

  const clientId = import.meta.env.VITE_OIDC_CLIENT_ID || 'vector-pilot'

  const params = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: clientId,
    code,
    code_verifier: codeVerifier,
    redirect_uri: import.meta.env.VITE_REDIRECT_URI || 'http://localhost:5173/callback',
  })

  const response = await fetch(`${settings}/protocol/openid-connect/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: params.toString(),
  })

  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.error_description || 'Failed to exchange code for token')
  }

  const expiresIn = data.expires_in || 3600
  const token = data.access_token
  const user: AuthUser = {
    id: 0,
    email: data.email || '',
    username: data.preferred_username || 'unknown',
    role: data.realm_access?.roles?.[0] as UserRole || 'analyst',
  }

  const expiresAt = Date.now() + expiresIn * 1000
  setSession({ user, token, codeVerifier: null, expiresAt })

  return { token, user, expiresIn }
}

// Logout
export function logout(): void {
  setSession({ user: null, token: null, codeVerifier: null, expiresAt: null })
}

// API client with auth
async function fetchJsonWithAuth<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const session = getSession()

  const headers = new Headers(options.headers || {})

  // Add auth token if authenticated
  if (session.token && isAuthenticated()) {
    headers.append('Authorization', `Bearer ${session.token}`)
  }

  const response = await fetch(`${API_BASE}${url}`, {
    headers,
    ...options,
  })

  // If 401 and we have a token, try clearing
  if (response.status === 401 && session.token) {
    clearSession()
    throw new Error('Authentication expired. Please log in again.')
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

export const api = {
  evaluations: {
    list: (params?: { page?: number; page_size?: number; status?: string }) => {
      const search = new URLSearchParams()
      if (params?.page) search.set('page', params.page.toString())
      if (params?.page_size) search.set('page_size', params.page_size.toString())
      if (params?.status) search.set('status', params.status)
      return fetchJsonWithAuth<EvaluationListResponse>(`/evaluations?${search.toString()}`)
    },

    get: (id: number) => fetchJsonWithAuth<EvaluationWithRuns>(`/evaluations/${id}`),

    create: (data: EvaluationCreate) =>
      fetchJsonWithAuth<EvaluationRead>('/evaluations', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    update: (id: number, data: EvaluationUpdate) =>
      fetchJsonWithAuth<EvaluationRead>(`/evaluations/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),

    delete: (id: number) =>
      fetchJsonWithAuth<void>(`/evaluations/${id}`, {
        method: 'DELETE',
      }),

    createRun: (evaluationId: number, data: EvaluationRunCreate) =>
      fetchJsonWithAuth<EvaluationRunRead>(`/evaluations/${evaluationId}/runs`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    getRun: (evaluationId: number, runId: number) =>
      fetchJsonWithAuth<EvaluationRunWithMetrics>(`/evaluations/${evaluationId}/runs/${runId}`),
  },

  health: {
    check: () => fetchJsonWithAuth<{ status: string; service: string }>('/health'),
  },
}

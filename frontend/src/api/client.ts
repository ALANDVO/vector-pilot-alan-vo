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

async function fetchJson<T>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

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
      return fetchJson<EvaluationListResponse>(`/evaluations?${search.toString()}`)
    },

    get: (id: number) => fetchJson<EvaluationWithRuns>(`/evaluations/${id}`),

    create: (data: EvaluationCreate) =>
      fetchJson<EvaluationRead>('/evaluations', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    update: (id: number, data: EvaluationUpdate) =>
      fetchJson<EvaluationRead>(`/evaluations/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),

    delete: (id: number) =>
      fetchJson<void>(`/evaluations/${id}`, {
        method: 'DELETE',
      }),

    createRun: (evaluationId: number, data: EvaluationRunCreate) =>
      fetchJson<EvaluationRunRead>(`/evaluations/${evaluationId}/runs`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    getRun: (evaluationId: number, runId: number) =>
      fetchJson<EvaluationRunWithMetrics>(`/evaluations/${evaluationId}/runs/${runId}`),
  },

  health: {
    check: () => fetchJson<{ status: string; service: string }>('/health'),
  },
}
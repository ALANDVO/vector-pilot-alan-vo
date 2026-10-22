import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { EvaluationRead, EvaluationListResponse } from '../api/types'

interface EvaluationListProps {
  onEvaluationSelect?: (evaluation: EvaluationRead) => void
}

export function EvaluationList({ onEvaluationSelect }: EvaluationListProps) {
  const navigate = useNavigate()
  const [evaluations, setEvaluations] = useState<EvaluationRead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const pageSize = 20

  const fetchEvaluations = async () => {
    try {
      setLoading(true)
      setError(null)
      const response: EvaluationListResponse = await api.evaluations.list({ page, page_size: pageSize })
      setEvaluations(response.items)
      setTotal(response.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load evaluations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchEvaluations()
  }, [page])

  const handleRowClick = (evaluation: EvaluationRead) => {
    if (onEvaluationSelect) {
      onEvaluationSelect(evaluation)
    } else {
      navigate(`/evaluations/${evaluation.id}`)
    }
  }

  const getStatusBadge = (status: string) => {
    const badges: Record<string, string> = {
      pending: 'badge-pending',
      running: 'badge-running',
      completed: 'badge-completed',
      failed: 'badge-failed',
    }
    return badges[status] || 'badge-pending'
  }

  if (loading) {
    return <div className="loading">Loading evaluations...</div>
  }

  if (error) {
    return <div className="error-message">{error}</div>
  }

  if (evaluations.length === 0) {
    return (
      <div className="empty-state">
        <h3>No evaluations yet</h3>
        <p>Create your first evaluation to get started.</p>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Dataset</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {evaluations.map((evaluation) => (
              <tr key={evaluation.id} onClick={() => handleRowClick(evaluation)} style={{ cursor: 'pointer' }}>
                <td>{evaluation.name}</td>
                <td>{evaluation.dataset_name} v{evaluation.dataset_version}</td>
                <td>
                  <span className={`badge ${getStatusBadge(evaluation.status)}`}>
                    {evaluation.status}
                  </span>
                </td>
                <td>{new Date(evaluation.created_at).toLocaleDateString()}</td>
                <td>
                  <button
                    className="btn btn-secondary"
                    onClick={(e) => {
                      e.stopPropagation()
                      navigate(`/evaluations/${evaluation.id}`)
                    }}
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {total > pageSize && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '1rem' }}>
          <button
            className="btn btn-secondary"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            Previous
          </button>
          <span style={{ alignSelf: 'center', color: '#6b7280' }}>
            Page {page} of {Math.ceil(total / pageSize)}
          </span>
          <button
            className="btn btn-secondary"
            onClick={() => setPage((p) => Math.min(Math.ceil(total / pageSize), p + 1))}
            disabled={page >= Math.ceil(total / pageSize)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
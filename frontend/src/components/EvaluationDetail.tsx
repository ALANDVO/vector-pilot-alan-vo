import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { EvaluationRead, EvaluationRunRead, EvaluationRunWithMetrics } from '../api/types'
import { EvaluationForm } from './EvaluationForm'

export function EvaluationDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [evaluation, setEvaluation] = useState<EvaluationRead | null>(null)
  const [runs, setRuns] = useState<EvaluationRunRead[]>([])
  const [selectedRun, setSelectedRun] = useState<EvaluationRunWithMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showEditForm, setShowEditForm] = useState(false)
  const [creatingRun, setCreatingRun] = useState(false)
  const [runError, setRunError] = useState<string | null>(null)

  const fetchEvaluation = async () => {
    if (!id) return
    try {
      setLoading(true)
      setError(null)
      const data = await api.evaluations.get(parseInt(id))
      setEvaluation(data)
      setRuns(data.runs || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load evaluation')
    } finally {
      setLoading(false)
    }
  }

  const fetchRun = async (runId: number) => {
    if (!id) return
    try {
      const data = await api.evaluations.getRun(parseInt(id), runId)
      setSelectedRun(data)
    } catch (err) {
      setRunError(err instanceof Error ? err.message : 'Failed to load run')
    }
  }

  useEffect(() => {
    fetchEvaluation()
  }, [id])

  const handleCreateRun = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!id) return

    const formData = new FormData(e.currentTarget)
    const modelProvider = formData.get('model_provider') as string
    const modelName = formData.get('model_name') as string

    if (!modelProvider || !modelName) {
      setRunError('Model provider and name are required')
      return
    }

    try {
      setCreatingRun(true)
      setRunError(null)
      await api.evaluations.createRun(parseInt(id), { model_provider: modelProvider, model_name: modelName })
      fetchEvaluation()
    } catch (err) {
      setRunError(err instanceof Error ? err.message : 'Failed to create run')
    } finally {
      setCreatingRun(false)
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
    return <div className="loading">Loading evaluation...</div>
  }

  if (error) {
    return (
      <div className="card">
        <div className="error-message">{error}</div>
        <button className="btn btn-secondary" onClick={() => navigate('/')}>
          Back to List
        </button>
      </div>
    )
  }

  if (!evaluation) {
    return (
      <div className="card">
        <div className="empty-state">
          <h3>Evaluation not found</h3>
        </div>
        <button className="btn btn-secondary" onClick={() => navigate('/')}>
          Back to List
        </button>
      </div>
    )
  }

  return (
    <div>
      <div className="header">
        <div>
          <h1 className="page-title">{evaluation.name}</h1>
          <p style={{ color: '#6b7280' }}>{evaluation.description || 'No description'}</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-secondary" onClick={() => setShowEditForm(true)}>
            Edit
          </button>
          <button className="btn btn-primary" onClick={() => navigate(`/evaluations/${evaluation.id}/runs/new`)}>
            New Run
          </button>
        </div>
      </div>

      {showEditForm && (
        <EvaluationForm
          initialData={evaluation}
          onSuccess={() => {
            setShowEditForm(false)
            fetchEvaluation()
          }}
        />
      )}

      {!showEditForm && (
        <>
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ marginBottom: '1rem' }}>Details</h3>
            <dl style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '0.5rem 1rem' }}>
              <dt>Dataset</dt>
              <dd>{evaluation.dataset_name} v{evaluation.dataset_version}</dd>
              <dt>Status</dt>
              <dd>
                <span className={`badge ${getStatusBadge(evaluation.status)}`}>
                  {evaluation.status}
                </span>
              </dd>
              <dt>Created</dt>
              <dd>{new Date(evaluation.created_at).toLocaleString()}</dd>
              <dt>Updated</dt>
              <dd>{new Date(evaluation.updated_at).toLocaleString()}</dd>
              {evaluation.completed_at && (
                <>
                  <dt>Completed</dt>
                  <dd>{new Date(evaluation.completed_at).toLocaleString()}</dd>
                </>
              )}
            </dl>
          </div>

          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3>Runs</h3>
              <form onSubmit={handleCreateRun} style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <input
                  type="text"
                  name="model_provider"
                  className="form-input"
                  placeholder="Model provider (e.g., openai, anthropic)"
                  required
                  style={{ minWidth: '200px' }}
                />
                <input
                  type="text"
                  name="model_name"
                  className="form-input"
                  placeholder="Model name (e.g., gpt-4, claude-3)"
                  required
                  style={{ minWidth: '200px' }}
                />
                <button type="submit" className="btn btn-primary" disabled={creatingRun}>
                  {creatingRun ? 'Creating...' : 'Add Run'}
                </button>
              </form>
            </div>

            {runError && <div className="error-message">{runError}</div>}

            {runs.length === 0 ? (
              <div className="empty-state">
                <p>No runs yet. Create a run to start evaluating.</p>
              </div>
            ) : (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Model</th>
                      <th>Status</th>
                      <th>Started</th>
                      <th>Completed</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runs.map((run) => (
                      <tr key={run.id}>
                        <td>{run.model_provider} / {run.model_name}</td>
                        <td>
                          <span className={`badge ${getStatusBadge(run.status)}`}>
                            {run.status}
                          </span>
                        </td>
                        <td>{new Date(run.started_at).toLocaleString()}</td>
                        <td>{run.completed_at ? new Date(run.completed_at).toLocaleString() : '-'}</td>
                        <td>
                          <button
                            className="btn btn-secondary"
                            onClick={() => fetchRun(run.id)}
                          >
                            View Metrics
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {selectedRun && (
              <div className="card" style={{ marginTop: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h3>Run Metrics: {selectedRun.model_provider} / {selectedRun.model_name}</h3>
                  <button className="btn btn-secondary" onClick={() => setSelectedRun(null)}>
                    Close
                  </button>
                </div>
                {selectedRun.metrics.length === 0 ? (
                  <p style={{ color: '#6b7280' }}>No metrics recorded yet.</p>
                ) : (
                  <div className="table-container">
                    <table>
                      <thead>
                        <tr>
                          <th>Metric</th>
                          <th>Value</th>
                          <th>Details</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedRun.metrics.map((metric) => (
                          <tr key={metric.id}>
                            <td>{metric.name}</td>
                            <td>{metric.value.toFixed(4)}</td>
                            <td>{metric.details ? JSON.stringify(JSON.parse(metric.details), null, 2) : '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
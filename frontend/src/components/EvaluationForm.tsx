import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { EvaluationCreate, EvaluationRead } from '../api/types'
interface EvaluationFormProps {
  initialData?: EvaluationRead
  onSuccess?: () => void
}

export function EvaluationForm({ initialData, onSuccess }: EvaluationFormProps) {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const isEditing = !!id

  const [name, setName] = useState(initialData?.name || '')
  const [description, setDescription] = useState(initialData?.description || '')
  const [datasetName, setDatasetName] = useState(initialData?.dataset_name || '')
  const [datasetVersion, setDatasetVersion] = useState(initialData?.dataset_version || '1.0')
  const [config, setConfig] = useState<Record<string, unknown>>(initialData?.config ? JSON.parse(initialData.config as string) : {})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const data: EvaluationCreate = {
        name,
        description: description || undefined,
        dataset_name: datasetName,
        dataset_version: datasetVersion,
        config: Object.keys(config).length > 0 ? config : undefined,
      }

      if (isEditing && id) {
        await api.evaluations.update(parseInt(id), data)
      } else {
        await api.evaluations.create(data)
      }

      onSuccess?.()
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save evaluation')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!id || !isEditing) return
    if (!window.confirm('Are you sure you want to delete this evaluation?')) return

    try {
      setLoading(true)
      await api.evaluations.delete(parseInt(id))
      onSuccess?.()
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete evaluation')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card" style={{ maxWidth: '600px' }}>
      <h2 style={{ marginBottom: '1.5rem' }}>{isEditing ? 'Edit Evaluation' : 'Create Evaluation'}</h2>

      {error && <div className="error-message">{error}</div>}

      <div className="form-group">
        <label htmlFor="name" className="form-label">Name *</label>
        <input
          type="text"
          id="name"
          className="form-input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          placeholder="Enter evaluation name"
        />
      </div>

      <div className="form-group">
        <label htmlFor="description" className="form-label">Description</label>
        <textarea
          id="description"
          className="form-input"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          placeholder="Optional description"
        />
      </div>

      <div className="form-group">
        <label htmlFor="dataset_name" className="form-label">Dataset Name *</label>
        <input
          type="text"
          id="dataset_name"
          className="form-input"
          value={datasetName}
          onChange={(e) => setDatasetName(e.target.value)}
          required
          placeholder="Enter dataset name"
        />
      </div>

      <div className="form-group">
        <label htmlFor="dataset_version" className="form-label">Dataset Version</label>
        <input
          type="text"
          id="dataset_version"
          className="form-input"
          value={datasetVersion}
          onChange={(e) => setDatasetVersion(e.target.value)}
          placeholder="1.0"
        />
      </div>

      <div className="form-group">
        <label htmlFor="config" className="form-label">Config (JSON)</label>
        <textarea
          id="config"
          className="form-input"
          value={JSON.stringify(config, null, 2)}
          onChange={(e) => {
            try {
              setConfig(JSON.parse(e.target.value))
            } catch {
              // Invalid JSON, keep previous
            }
          }}
          rows={5}
          placeholder='{"metric": "accuracy", "threshold": 0.8}'
        />
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.5rem' }}>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Saving...' : isEditing ? 'Update' : 'Create'}
        </button>
        {isEditing && (
          <button type="button" className="btn btn-danger" onClick={handleDelete} disabled={loading}>
            Delete
          </button>
        )}
        <button type="button" className="btn btn-secondary" onClick={() => navigate('/')} disabled={loading}>
          Cancel
        </button>
      </div>
    </form>
  )
}
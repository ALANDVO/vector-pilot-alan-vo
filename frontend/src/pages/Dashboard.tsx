import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, isAuthenticated, getCurrentUser } from '../api/client'

interface EvaluationSummary {
  id: number
  name: string
  dataset_name: string
  status: string
  created_at: string
}

export interface DashboardProps {
}

export function Dashboard(): JSX.Element {
  const navigate = useNavigate()
  const [evaluations, setEvaluations] = React.useState<EvaluationSummary[]>([])
  const [loading, setLoading] = React.useState(true)
  const user = getCurrentUser()

  React.useEffect(() => {
    async function loadEvaluations() {
      try {
        if (isAuthenticated()) {
          const data = await api.evaluations.list()
          setEvaluations(data.items || [])
        }
      } catch (err) {
        console.error('Failed to load evaluations:', err)
      } finally {
        setLoading(false)
      }
    }
    loadEvaluations()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen p-8">
        <div className="bg-white p-8 rounded-lg shadow-xl">
          <p>Loading evaluations…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="prose lg:prose-2xl max-w-2xl mx-auto">
      {!user && (
        <div className="mb-6 text-center">
          <p className="text-muted-foreground">
            Please{' '}
            <a href="/">log in</a>
            {user ? '' : ''}
            to view your evaluations.
          </p>
        </div>
      )}

      {user && (
        <div className="mb-6">
          <p className="text-muted-foreground">Welcome, {user.username}!</p>
        </div>
      )}

      <button
        onClick={() => navigate('/evaluations/new')}
        className="inline-block bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors mb-4"
        aria-label="Create new evaluation"
      >
        Create new evaluation
      </button>

      {evaluations.length === 0 && (
        <p className="text-muted-foreground mt-4">
          No evaluations found. Create one above.
        </p>
      )}

      <ul className="divide-y divide-gray-200">
        {evaluations.map((item) => (
          <li key={item.id} className="py-3 border-b last:border-0">
            <Link
              to={`/evaluations/${item.id}`}
              className="font-medium hover:underline"
            >
              {item.name}
            </Link>
            <span className="text-sm text-gray-500 ml-4">
              {item.dataset_name} — {item.status}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

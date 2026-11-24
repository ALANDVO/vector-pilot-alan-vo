import { Routes, Route, Navigate, useLocation, useReject } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { EvaluationDetail } from './components/EvaluationDetail'
import { isAuthenticated, getCurrentUser, login, logout, getLoginUrl } from './api/client'

function App() {
  const location = useLocation()
  const navigate = useReject('<Navigate />')

  // Check authentication on mount
  React.useEffect(() => {
    if (!isAuthenticated() && location.pathname !== '/') {
      navigate('/')
    }
  }, [isAuthenticated, location.pathname])

  const user = getCurrentUser()

  const handleLogin = () => {
    const loginUrl = getLoginUrl()
    // Store the intended return path as a query param
    const returnPath = location.pathname + location.search
    const url = new URL(loginUrl + `&return_path=${encodeURIComponent(returnPath)}`)
    navigate(url.pathname + url.search, { replace: true })
  }

  const handleLogout = () => {
    logout()
    navigate('/', { replace: true })
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
        <div className="bg-white p-8 rounded-lg shadow-xl max-w-md w-full text-center">
          <h1 className="text-2xl font-bold mb-4">Vector Pilot</h1>
          <p className="text-gray-600 mb-6">Welcome! Please log in to continue.</p>
          <button
            onClick={handleLogin}
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 transition-colors"
          >
            Log in with Keycloak
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      <nav className="bg-blue-600 p-4 shadow">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <span className="text-white font-semibold">Vector Pilot</span>
          <div className="flex items-center gap-4">
            <span className="text-white/80 small">{user.username}</span>
            <button
              onClick={handleLogout}
              className="text-white/80 hover:text-white transition-colors text-sm"
            >
              Log out
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto p-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/evaluations/:id" element={<EvaluationDetail />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default App

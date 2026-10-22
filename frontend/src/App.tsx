import { Routes, Route, Navigate } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { EvaluationDetail } from './components/EvaluationDetail'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/evaluations/:id" element={<EvaluationDetail />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
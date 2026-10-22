import { useState } from 'react'
import { EvaluationList } from '../components/EvaluationList'
import { EvaluationForm } from '../components/EvaluationForm'
import { EvaluationDetail } from '../components/EvaluationDetail'
import type { EvaluationRead } from '../api/types'

export function Dashboard() {
  const [view, setView] = useState<'list' | 'create' | 'detail'>('list')
  const [selectedEvaluation, setSelectedEvaluation] = useState<EvaluationRead | null>(null)

  const handleEvaluationSelect = (evaluation: EvaluationRead) => {
    setSelectedEvaluation(evaluation)
    setView('detail')
  }

  const handleCreateClick = () => {
    setView('create')
  }

  const handleCreateSuccess = () => {
    setView('list')
  }

  return (
    <div className="container">
      {view === 'list' && (
        <>
          <div className="header">
            <h1 className="page-title">Evaluations</h1>
            <button className="btn btn-primary" onClick={handleCreateClick}>
              New Evaluation
            </button>
          </div>
          <EvaluationList onEvaluationSelect={handleEvaluationSelect} />
        </>
      )}

      {view === 'create' && (
        <EvaluationForm onSuccess={handleCreateSuccess} />
      )}

      {view === 'detail' && selectedEvaluation && (
        <EvaluationDetail />
      )}
    </div>
  )
}
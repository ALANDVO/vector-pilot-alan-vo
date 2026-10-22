import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { EvaluationList } from './EvaluationList'
import { api } from '../api/client'
import type { EvaluationRead, EvaluationListResponse } from '../api/types'

const mockEvaluations: EvaluationRead[] = [
  {
    id: 1,
    name: 'Test Evaluation 1',
    description: 'First test',
    dataset_name: 'dataset-1',
    dataset_version: '1.0',
    status: 'completed',
    owner_id: 1,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    completed_at: '2024-01-15T11:00:00Z',
  },
  {
    id: 2,
    name: 'Test Evaluation 2',
    description: 'Second test',
    dataset_name: 'dataset-2',
    dataset_version: '2.0',
    status: 'running',
    owner_id: 1,
    created_at: '2024-01-16T10:00:00Z',
    updated_at: '2024-01-16T10:00:00Z',
    completed_at: null,
  },
]

const mockResponse: EvaluationListResponse = {
  items: mockEvaluations,
  total: 2,
  page: 1,
  page_size: 20,
}

vi.mock('../api/client', () => ({
  api: {
    evaluations: {
      list: vi.fn(),
    },
  },
}))

function renderWithRouter() {
  return render(
    <BrowserRouter>
      <EvaluationList />
    </BrowserRouter>
  )
}

describe('EvaluationList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(api.evaluations.list as vi.Mock).mockResolvedValue(mockResponse)
  })

  it('shows loading state initially', () => {
    renderWithRouter()
    expect(screen.getByText('Loading evaluations...')).toBeInTheDocument()
  })

  it('displays evaluations after loading', async () => {
    renderWithRouter()
    await waitFor(() => {
      expect(screen.getByText('Test Evaluation 1')).toBeInTheDocument()
      expect(screen.getByText('Test Evaluation 2')).toBeInTheDocument()
    })
  })

  it('shows status badges', async () => {
    renderWithRouter()
    await waitFor(() => {
      expect(screen.getByText('completed')).toBeInTheDocument()
      expect(screen.getByText('running')).toBeInTheDocument()
    })
  })

  it('displays empty state when no evaluations', async () => {
    ;(api.evaluations.list as vi.Mock).mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 })
    renderWithRouter()
    await waitFor(() => {
      expect(screen.getByText('No evaluations yet')).toBeInTheDocument()
    })
  })

  it('displays error message on failure', async () => {
    ;(api.evaluations.list as vi.Mock).mockRejectedValue(new Error('Network error'))
    renderWithRouter()
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })
  })
})
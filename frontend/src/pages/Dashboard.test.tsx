import { vi, describe, it, beforeEach, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { Dashboard } from './Dashboard'
import { api } from '../api/client'

const mockEvaluations = [
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
]

vi.mock('../api/client', () => ({
  api: {
    evaluations: {
      list: vi.fn(),
      create: vi.fn(),
    },
  },
}))

function renderWithRouter(component: React.ReactElement) {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  )
}

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(api.evaluations.list as vi.Mock).mockResolvedValue({
      items: mockEvaluations,
      total: 1,
      page: 1,
      page_size: 20,
    })
  })

  it('shows evaluation list by default', async () => {
    renderWithRouter(<Dashboard />)
    await waitFor(() => {
      expect(screen.getByText('Test Evaluation 1')).toBeInTheDocument()
    })
  })

  it('shows create button', async () => {
    renderWithRouter(<Dashboard />)
    expect(screen.getByRole('button', { name: 'New Evaluation' })).toBeInTheDocument()
  })

  it('navigates to create form when clicking New Evaluation', async () => {
    renderWithRouter(<Dashboard />)
    await waitFor(() => {
      screen.getByRole('button', { name: 'New Evaluation' }).click()
    })
    expect(screen.getByRole('heading', { name: 'Create Evaluation' })).toBeInTheDocument()
  })
})
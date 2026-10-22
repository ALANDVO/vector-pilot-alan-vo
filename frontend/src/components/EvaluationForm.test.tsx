import { vi, describe, it, beforeEach, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { EvaluationForm } from './EvaluationForm'
import { api } from '../api/client'

vi.mock('../api/client', () => ({
  api: {
    evaluations: {
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
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

describe('EvaluationForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    window.confirm = vi.fn(() => true)
  })

  it('renders create form with empty fields', () => {
    renderWithRouter(<EvaluationForm />)
    expect(screen.getByRole('heading', { name: 'Create Evaluation' })).toBeInTheDocument()
    expect(screen.getByLabelText('Name *')).toHaveValue('')
    expect(screen.getByLabelText('Dataset Name *')).toHaveValue('')
  })

  it('renders edit form with prefilled data', () => {
    const initialData = {
      id: 1,
      name: 'Existing Evaluation',
      description: 'Test description',
      dataset_name: 'existing-dataset',
      dataset_version: '2.0',
      status: 'completed',
      owner_id: 1,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
      completed_at: '2024-01-15T11:00:00Z',
      config: '{"metric": "accuracy"}',
    }
    // Mock the useParams hook to return an id
    renderWithRouter(<EvaluationForm initialData={initialData} />)
    expect(screen.getByRole('heading', { name: 'Edit Evaluation' })).toBeInTheDocument()
    expect(screen.getByLabelText('Name *')).toHaveValue('Existing Evaluation')
    expect(screen.getByLabelText('Dataset Name *')).toHaveValue('existing-dataset')
  })

  it('submits create form successfully', async () => {
    ;(api.evaluations.create as vi.Mock).mockResolvedValue({})
    renderWithRouter(<EvaluationForm onSuccess={vi.fn()} />)

    screen.getByLabelText('Name *').value = 'New Evaluation'
    screen.getByLabelText('Dataset Name *').value = 'new-dataset'
    screen.getByRole('button', { name: 'Create' }).click()

    await waitFor(() => {
      expect(api.evaluations.create).toHaveBeenCalledWith({
        name: 'New Evaluation',
        description: '',
        dataset_name: 'new-dataset',
        dataset_version: '1.0',
      })
    })
  })

  it('submits edit form successfully', async () => {
    ;(api.evaluations.update as vi.Mock).mockResolvedValue({})
    const initialData = {
      id: 1,
      name: 'Existing Evaluation',
      description: 'Test description',
      dataset_name: 'existing-dataset',
      dataset_version: '2.0',
      status: 'completed',
      owner_id: 1,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
      completed_at: '2024-01-15T11:00:00Z',
    }
    renderWithRouter(<EvaluationForm initialData={initialData} onSuccess={vi.fn()} />)

    screen.getByLabelText('Name *').value = 'Updated Evaluation'
    screen.getByRole('button', { name: 'Update' }).click()

    await waitFor(() => {
      expect(api.evaluations.update).toHaveBeenCalledWith(1, expect.objectContaining({
        name: 'Updated Evaluation',
      }))
    })
  })

  it('shows validation errors for required fields', async () => {
    renderWithRouter(<EvaluationForm />)
    screen.getByRole('button', { name: 'Create' }).click()
    expect(api.evaluations.create).not.toHaveBeenCalled()
  })
})
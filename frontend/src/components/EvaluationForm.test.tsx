import { vi, describe, it, beforeEach, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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
    }
    renderWithRouter(<EvaluationForm initialData={initialData} />)
    expect(screen.getByRole('heading', { name: 'Edit Evaluation' })).toBeInTheDocument()
    expect(screen.getByLabelText('Name *')).toHaveValue('Existing Evaluation')
    expect(screen.getByLabelText('Dataset Name *')).toHaveValue('existing-dataset')
  })

  it('submits create form successfully', async () => {
    ;(api.evaluations.create as vi.Mock).mockResolvedValue({})
    const onSuccess = vi.fn()
    renderWithRouter(<EvaluationForm onSuccess={onSuccess} />)

    await userEvent.type(screen.getByLabelText('Name *'), 'New Evaluation')
    await userEvent.type(screen.getByLabelText('Dataset Name *'), 'new-dataset')
    await userEvent.click(screen.getByRole('button', { name: 'Create' }))

    await waitFor(() => {
      expect(api.evaluations.create).toHaveBeenCalledWith({
        name: 'New Evaluation',
        description: undefined,
        dataset_name: 'new-dataset',
        dataset_version: '1.0',
        config: undefined,
      })
    })
    expect(onSuccess).toHaveBeenCalled()
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
    const onSuccess = vi.fn()
    renderWithRouter(<EvaluationForm initialData={initialData} onSuccess={onSuccess} />)

    await userEvent.clear(screen.getByLabelText('Name *'))
    await userEvent.type(screen.getByLabelText('Name *'), 'Updated Evaluation')
    await userEvent.click(screen.getByRole('button', { name: 'Update' }))

    await waitFor(() => {
      expect(api.evaluations.update).toHaveBeenCalledWith(1, expect.objectContaining({
        name: 'Updated Evaluation',
      }))
    })
    expect(onSuccess).toHaveBeenCalled()
  })

  it('shows validation errors for required fields', async () => {
    renderWithRouter(<EvaluationForm />)

    await userEvent.click(screen.getByRole('button', { name: 'Create' }))

    await waitFor(() => {
      expect(screen.getByLabelText('Name *')).toHaveAttribute('required')
      expect(screen.getByLabelText('Dataset Name *')).toHaveAttribute('required')
    })
  })
})

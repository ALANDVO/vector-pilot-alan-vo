import '@testing-library/jest-dom'
import { vi, expect, describe, it, beforeEach, afterEach } from 'vitest'

// Mock fetch globally
globalThis.fetch = vi.fn()

// Mock React Router
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useParams: () => ({}),
  }
})
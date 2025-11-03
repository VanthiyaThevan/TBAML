import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface LOBVerificationInput {
  client: string
  client_country: string
  client_role: 'Import' | 'Export'
  product_name: string
}

export interface LOBVerificationOutput {
  id: number
  client: string
  client_country: string
  client_role: string
  product_name: string | null
  ai_response: string | null
  website_source: string | null
  publication_date: string | null
  activity_level: string | null
  flags: string[]
  sources: string[]
  is_red_flag: boolean
  confidence_score: string | null
  data_collected_at: string | null
  data_freshness_score: string | null
  last_verified_at: string | null
  created_at: string
  updated_at: string
}

export const api = {
  verifyLOB: async (input: LOBVerificationInput): Promise<LOBVerificationOutput> => {
    const response = await apiClient.post('/api/v1/lob/verify', input)
    return response.data
  },

  getVerification: async (id: number): Promise<LOBVerificationOutput> => {
    const response = await apiClient.get(`/api/v1/lob/${id}`)
    return response.data
  },

  listVerifications: async (skip = 0, limit = 100): Promise<LOBVerificationOutput[]> => {
    const response = await apiClient.get('/api/v1/lob', {
      params: { skip, limit },
    })
    return response.data
  },

  healthCheck: async (): Promise<{ status: string; version: string }> => {
    const response = await apiClient.get('/health')
    return response.data
  },
}


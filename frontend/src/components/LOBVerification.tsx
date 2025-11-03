import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import axios from 'axios'
import { api, LOBVerificationInput, LOBVerificationOutput } from '../lib/api'
import VerificationForm from './VerificationForm'
import VerificationResults from './VerificationResults'
import LoadingSpinner from './LoadingSpinner'
import ErrorMessage from './ErrorMessage'
import ConnectionStatus from './ConnectionStatus'

export default function LOBVerification() {
  const [results, setResults] = useState<LOBVerificationOutput | null>(null)

  const mutation = useMutation({
    mutationFn: (input: LOBVerificationInput) => api.verifyLOB(input),
    onSuccess: (data) => {
      setResults(data)
    },
  })

  const handleSubmit = (input: LOBVerificationInput) => {
    mutation.mutate(input)
  }

  return (
    <div className="space-y-6">
      <ConnectionStatus />
      
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Verify Line of Business
        </h2>
        <VerificationForm onSubmit={handleSubmit} isSubmitting={mutation.isPending} />
      </div>

      {mutation.isPending && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <LoadingSpinner message="Analyzing line of business..." />
        </div>
      )}

      {mutation.isError && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <ErrorMessage 
            error={
              mutation.error instanceof Error 
                ? mutation.error.message 
                : 'An error occurred'
            }
            details={
              axios.isAxiosError(mutation.error)
                ? mutation.error.code === 'ECONNREFUSED' || mutation.error.code === 'ERR_NETWORK'
                  ? 'Cannot connect to backend API. Make sure the backend is running at http://localhost:8000'
                  : mutation.error.response?.data?.detail || mutation.error.message
                : undefined
            }
          />
        </div>
      )}

      {results && !mutation.isPending && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <VerificationResults results={results} />
        </div>
      )}
    </div>
  )
}


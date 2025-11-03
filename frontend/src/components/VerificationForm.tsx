import { useState, FormEvent } from 'react'
import { LOBVerificationInput } from '../lib/api'

interface VerificationFormProps {
  onSubmit: (input: LOBVerificationInput) => void
  isSubmitting: boolean
}

export default function VerificationForm({ onSubmit, isSubmitting }: VerificationFormProps) {
  const [formData, setFormData] = useState<LOBVerificationInput>({
    client: '',
    client_country: '',
    client_role: 'Export',
    product_name: '',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.client.trim()) {
      newErrors.client = 'Client name is required'
    }

    if (!formData.client_country.trim()) {
      newErrors.client_country = 'Country code is required'
    } else if (formData.client_country.length !== 2) {
      newErrors.client_country = 'Country code must be 2 characters (e.g., US, GB)'
    }

    if (!formData.product_name.trim()) {
      newErrors.product_name = 'Product name is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    
    if (validate()) {
      onSubmit(formData)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="client" className="block text-sm font-medium text-gray-700 mb-1">
          Client Name *
        </label>
        <input
          type="text"
          id="client"
          value={formData.client}
          onChange={(e) => setFormData({ ...formData, client: e.target.value })}
          className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white ${
            errors.client ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="e.g., Shell plc"
          disabled={isSubmitting}
        />
        {errors.client && (
          <p className="mt-1 text-sm text-red-600">{errors.client}</p>
        )}
      </div>

      <div>
        <label htmlFor="client_country" className="block text-sm font-medium text-gray-700 mb-1">
          Country Code (ISO 2-letter) *
        </label>
        <input
          type="text"
          id="client_country"
          value={formData.client_country}
          onChange={(e) => setFormData({ ...formData, client_country: e.target.value.toUpperCase() })}
          maxLength={2}
          className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white ${
            errors.client_country ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="e.g., GB, US"
          disabled={isSubmitting}
        />
        {errors.client_country && (
          <p className="mt-1 text-sm text-red-600">{errors.client_country}</p>
        )}
      </div>

      <div>
        <label htmlFor="client_role" className="block text-sm font-medium text-gray-700 mb-1">
          Client Role *
        </label>
        <select
          id="client_role"
          value={formData.client_role}
          onChange={(e) => setFormData({ ...formData, client_role: e.target.value as 'Import' | 'Export' })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white"
          disabled={isSubmitting}
        >
          <option value="Export">Export</option>
          <option value="Import">Import</option>
        </select>
      </div>

      <div>
        <label htmlFor="product_name" className="block text-sm font-medium text-gray-700 mb-1">
          Product Name *
        </label>
        <input
          type="text"
          id="product_name"
          value={formData.product_name}
          onChange={(e) => setFormData({ ...formData, product_name: e.target.value })}
          className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white ${
            errors.product_name ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="e.g., Oil & Gas"
          disabled={isSubmitting}
        />
        {errors.product_name && (
          <p className="mt-1 text-sm text-red-600">{errors.product_name}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isSubmitting ? 'Verifying...' : 'Verify Line of Business'}
      </button>
    </form>
  )
}


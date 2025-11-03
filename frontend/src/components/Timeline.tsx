import { LOBVerificationOutput } from '../lib/api'

interface TimelineProps {
  results: LOBVerificationOutput
}

export default function Timeline({ results }: TimelineProps) {
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString()
  }

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-gray-900">Timeline</h3>
      
      <div className="bg-gray-50 p-4 rounded-lg space-y-3">
        {results.data_collected_at && (
          <div className="flex items-center space-x-3">
            <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
            <div>
              <p className="text-sm font-medium text-gray-700">Data Collected</p>
              <p className="text-xs text-gray-600">{formatDate(results.data_collected_at)}</p>
            </div>
          </div>
        )}

        {results.publication_date && (
          <div className="flex items-center space-x-3">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            <div>
              <p className="text-sm font-medium text-gray-700">Publication Date</p>
              <p className="text-xs text-gray-600">{results.publication_date}</p>
            </div>
          </div>
        )}

        {results.last_verified_at && (
          <div className="flex items-center space-x-3">
            <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
            <div>
              <p className="text-sm font-medium text-gray-700">Last Verified</p>
              <p className="text-xs text-gray-600">{formatDate(results.last_verified_at)}</p>
            </div>
          </div>
        )}

        <div className="flex items-center space-x-3">
          <span className="w-2 h-2 bg-gray-500 rounded-full"></span>
          <div>
            <p className="text-sm font-medium text-gray-700">Created</p>
            <p className="text-xs text-gray-600">{formatDate(results.created_at)}</p>
          </div>
        </div>
      </div>

      {results.data_freshness_score && (
        <div className="mt-3">
          <p className="text-sm text-gray-600">Data Freshness Score:</p>
          <p className="text-sm font-semibold text-gray-900">{results.data_freshness_score}</p>
        </div>
      )}

      {results.confidence_score && (
        <div>
          <p className="text-sm text-gray-600">Confidence Score:</p>
          <p className="text-sm font-semibold text-gray-900">{results.confidence_score}</p>
        </div>
      )}
    </div>
  )
}


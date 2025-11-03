import { LOBVerificationOutput } from '../lib/api'
import ActivityIndicator from './ActivityIndicator'
import FlagDisplay from './FlagDisplay'
import SourceCitation from './SourceCitation'
import AIResponse from './AIResponse'
import Timeline from './Timeline'

interface VerificationResultsProps {
  results: LOBVerificationOutput
}

export default function VerificationResults({ results }: VerificationResultsProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Verification Results
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600">Verification ID</p>
            <p className="text-lg font-semibold text-gray-900">#{results.id}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600">Client</p>
            <p className="text-lg font-semibold text-gray-900">{results.client}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600">Country</p>
            <p className="text-lg font-semibold text-gray-900">{results.client_country}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600">Role</p>
            <p className="text-lg font-semibold text-gray-900">{results.client_role}</p>
          </div>
        </div>
      </div>

      {results.activity_level && (
        <ActivityIndicator level={results.activity_level} />
      )}

      {results.flags && results.flags.length > 0 && (
        <FlagDisplay flags={results.flags} isRedFlag={results.is_red_flag} />
      )}

      {results.sources && results.sources.length > 0 && (
        <SourceCitation sources={results.sources} website={results.website_source} />
      )}

      {results.ai_response && (
        <AIResponse response={results.ai_response} />
      )}

      <Timeline results={results} />
    </div>
  )
}


import { useState } from 'react'

interface AIResponseProps {
  response: string
}

export default function AIResponse({ response }: AIResponseProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">AI Analysis</h3>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-sm text-primary-600 hover:text-primary-700"
        >
          {isExpanded ? 'Show Less' : 'Show More'}
        </button>
      </div>
      
      <div className="bg-gray-50 p-4 rounded-lg">
        <p className="text-sm text-gray-700 whitespace-pre-wrap">
          {isExpanded ? response : `${response.substring(0, 300)}...`}
        </p>
      </div>
    </div>
  )
}


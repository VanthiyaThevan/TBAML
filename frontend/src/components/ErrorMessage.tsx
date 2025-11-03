interface ErrorMessageProps {
  error: string
  details?: string
}

export default function ErrorMessage({ error, details }: ErrorMessageProps) {
  return (
    <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <span className="text-red-500 text-xl">✗</span>
        </div>
        <div className="ml-3">
          <p className="text-sm font-medium text-red-800">Error</p>
          <p className="text-sm text-red-700 mt-1">{error}</p>
          {details && (
            <p className="text-xs text-red-600 mt-2 italic">{details}</p>
          )}
        </div>
      </div>
    </div>
  )
}


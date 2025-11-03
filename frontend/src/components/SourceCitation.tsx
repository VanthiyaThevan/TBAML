interface SourceCitationProps {
  sources: string[]
  website?: string | null
}

export default function SourceCitation({ sources, website }: SourceCitationProps) {
  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-gray-900">Data Sources</h3>
      
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="space-y-2">
          {sources.map((source, index) => (
            <div key={index} className="flex items-center space-x-2">
              <span className="w-2 h-2 bg-primary-500 rounded-full"></span>
              <span className="text-sm text-gray-700 capitalize">
                {source.replace(/_/g, ' ')}
              </span>
            </div>
          ))}
        </div>
      </div>

      {website && (
        <div className="mt-3">
          <p className="text-sm text-gray-600 mb-1">Website Source:</p>
          <a
            href={website}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 hover:text-primary-700 text-sm underline"
          >
            {website}
          </a>
        </div>
      )}
    </div>
  )
}


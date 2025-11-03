interface FlagDisplayProps {
  flags: string[]
  isRedFlag: boolean
}

export default function FlagDisplay({ flags, isRedFlag }: FlagDisplayProps) {
  const getFlagColor = (flag: string) => {
    if (flag.includes('[HIGH]')) return 'border-red-500 bg-red-50 text-red-800'
    if (flag.includes('[MEDIUM]')) return 'border-yellow-500 bg-yellow-50 text-yellow-800'
    if (flag.includes('[LOW]')) return 'border-blue-500 bg-blue-50 text-blue-800'
    return 'border-gray-500 bg-gray-50 text-gray-800'
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <h3 className="text-lg font-semibold text-gray-900">Flags & Alerts</h3>
        {isRedFlag && (
          <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded">
            RED FLAG
          </span>
        )}
      </div>
      
      <div className="space-y-2">
        {flags.map((flag, index) => (
          <div
            key={index}
            className={`p-3 border-l-4 rounded ${getFlagColor(flag)}`}
          >
            <p className="text-sm font-medium">{flag}</p>
          </div>
        ))}
      </div>
    </div>
  )
}


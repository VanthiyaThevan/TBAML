interface ActivityIndicatorProps {
  level: string
}

const activityColors: Record<string, { bg: string; text: string; icon: string }> = {
  Active: { bg: 'bg-green-100', text: 'text-green-800', icon: '✓' },
  Dormant: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: '⚠' },
  Inactive: { bg: 'bg-gray-100', text: 'text-gray-800', icon: '○' },
  Suspended: { bg: 'bg-red-100', text: 'text-red-800', icon: '✗' },
  Unknown: { bg: 'bg-gray-100', text: 'text-gray-800', icon: '?' },
}

export default function ActivityIndicator({ level }: ActivityIndicatorProps) {
  const config = activityColors[level] || activityColors.Unknown

  return (
    <div className={`${config.bg} p-4 rounded-lg`}>
      <div className="flex items-center space-x-3">
        <span className="text-2xl">{config.icon}</span>
        <div>
          <p className="text-sm font-medium text-gray-600">Activity Level</p>
          <p className={`text-xl font-semibold ${config.text}`}>{level}</p>
        </div>
      </div>
    </div>
  )
}


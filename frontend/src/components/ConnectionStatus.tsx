import { useEffect, useState } from 'react'
import { api } from '../lib/api'

export default function ConnectionStatus() {
  const [isConnected, setIsConnected] = useState<boolean | null>(null)
  const [isChecking, setIsChecking] = useState(true)

  useEffect(() => {
    const checkConnection = async () => {
      try {
        setIsChecking(true)
        await api.healthCheck()
        setIsConnected(true)
      } catch (error) {
        setIsConnected(false)
      } finally {
        setIsChecking(false)
      }
    }

    checkConnection()
    // Check every 5 seconds
    const interval = setInterval(checkConnection, 5000)
    
    return () => clearInterval(interval)
  }, [])

  if (isChecking) {
    return null
  }

  if (!isConnected) {
    return (
      <div className="bg-yellow-50 border-l-4 border-yellow-500 p-3 mb-4 rounded">
        <div className="flex items-center">
          <span className="text-yellow-500 text-lg mr-2">⚠️</span>
          <div>
            <p className="text-sm font-medium text-yellow-800">Backend Not Connected</p>
            <p className="text-xs text-yellow-700 mt-1">
              Make sure the backend is running at http://localhost:8000
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-green-50 border-l-4 border-green-500 p-3 mb-4 rounded">
      <div className="flex items-center">
        <span className="text-green-500 text-lg mr-2">✓</span>
        <p className="text-sm font-medium text-green-800">Connected to Backend API</p>
      </div>
    </div>
  )
}


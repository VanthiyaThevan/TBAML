import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import LOBVerification from './components/LOBVerification'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <h1 className="text-2xl font-bold text-gray-900">
              TBAML System - Line of Business Verification
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Trade-Based Anti-Money Laundering Detection System
            </p>
          </div>
        </header>
        
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <LOBVerification />
        </main>
      </div>
    </QueryClientProvider>
  )
}

export default App


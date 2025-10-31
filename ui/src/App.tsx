import { useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useStore } from './store/useStore'
import { twinsAPI } from './api/client'
import { Header } from './components/Header'
import { TwinSelector } from './components/TwinSelector'
import { ExperimentPanel } from './components/ExperimentPanel'
import { ResultsAggregated } from './components/ResultsAggregated'
import { TwinInsights } from './components/TwinInsights'
import { ChatInterface } from './components/ChatInterface'
import { MetricsPanel } from './components/MetricsPanel'
import { CustomerMappingChart } from './components/CustomerMappingChart'
import { ValidationInfo } from './components/ValidationInfo'

const queryClient = new QueryClient()

function AppContent() {
  const { setTwins, viewMode, setError, selectAllTwins } = useStore()

  useEffect(() => {
    // Load twins on mount
    const loadTwins = async () => {
      try {
        const data = await twinsAPI.getAll()
        setTwins(data.twins)
        // Auto-select all twins on first load
        selectAllTwins()
      } catch (error) {
        console.error('Failed to load twins:', error)
        setError('Failed to load twins. Make sure the API server is running.')
      }
    }
    loadTwins()
  }, [setTwins, setError, selectAllTwins])

  return (
    <div className="min-h-screen bg-neon-darkbg">
      <Header />

      <main className="container mx-auto px-6 py-8 max-w-[1600px]">
        {viewMode === 'experiment' ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Left Column: Twins + Experiment Configuration */}
            <div className="space-y-6">
              {/* Twin Selection */}
              <TwinSelector />

              {/* Experiment Configuration */}
              <ExperimentPanel />
            </div>

            {/* Right Column: Results */}
            <div className="space-y-6">
              {/* Aggregated Results */}
              <div>
                <h2 className="text-2xl font-bold mb-4">
                  <span className="text-neon-green">Aggregated</span> Results
                </h2>
                <ResultsAggregated />
              </div>

              {/* Individual Twin Insights */}
              <div>
                <h2 className="text-2xl font-bold mb-4">
                  <span className="text-neon-blue">Individual</span> Insights
                </h2>
                <TwinInsights />
              </div>
            </div>
          </div>
        ) : viewMode === 'chat' ? (
          <ChatInterface />
        ) : (
          /* Metrics View */
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column: Validation Metrics */}
            <div className="space-y-6">
              <h2 className="text-2xl font-bold mb-4">
                <span className="text-neon-green">Model</span> Performance
              </h2>
              <MetricsPanel />
            </div>

            {/* Middle Column: Customer Distribution */}
            <div className="space-y-6">
              <h2 className="text-2xl font-bold mb-4">
                <span className="text-neon-blue">Twin</span> Distribution
              </h2>
              <CustomerMappingChart />
            </div>

            {/* Right Column: Dataset Info */}
            <div className="space-y-6">
              <h2 className="text-2xl font-bold mb-4">
                <span className="text-neon-green">Dataset</span> Information
              </h2>
              <ValidationInfo />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-neon-surfacelight mt-16 py-8">
        <div className="container mx-auto px-6 text-center text-neon-textsecondary text-sm">
          <p>
            Built with ❤️ by{' '}
            <span className="text-neon-green font-semibold">Darpan Labs</span>
          </p>
          <p className="mt-2">
            Digital Twin Simulator for Airlines - Test pricing, promotions, and customer experiences.
          </p>
        </div>
      </footer>
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  )
}

export default App

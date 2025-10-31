import React from 'react'
import { useStore } from '../store/useStore'

export const Header: React.FC = () => {
  const { viewMode, setViewMode } = useStore()

  return (
    <header className="bg-neon-surface border-b border-neon-surfacelight/50 sticky top-0 z-50 backdrop-blur-sm">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold">
              <span className="text-neon-green">Digital Twin</span>{' '}
              <span className="text-white">Simulator</span>{' '}
              <span className="text-neon-blue">for Airlines</span>
            </h1>
            <p className="text-neon-textsecondary mt-1">
              Test pricing strategies, promotions, and customer experiences with AI-powered personas
            </p>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('experiment')}
              className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                viewMode === 'experiment'
                  ? 'bg-neon-green text-neon-darkbg'
                  : 'bg-neon-surfacelight text-neon-textsecondary hover:text-neon-text'
              }`}
            >
              Experiment
            </button>
            <button
              onClick={() => setViewMode('chat')}
              className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                viewMode === 'chat'
                  ? 'bg-neon-green text-neon-darkbg'
                  : 'bg-neon-surfacelight text-neon-textsecondary hover:text-neon-text'
              }`}
            >
              Chat
            </button>
            <button
              onClick={() => setViewMode('metrics')}
              className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                viewMode === 'metrics'
                  ? 'bg-neon-green text-neon-darkbg'
                  : 'bg-neon-surfacelight text-neon-textsecondary hover:text-neon-text'
              }`}
            >
              Metrics
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}

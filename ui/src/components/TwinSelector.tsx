import React from 'react'
import { useStore } from '../store/useStore'
import { TwinCard } from './TwinCard'
import { Users } from 'lucide-react'

export const TwinSelector: React.FC = () => {
  const { twins, selectedTwinIds, selectAllTwins, clearSelection } = useStore()

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Users className="text-neon-green" size={24} />
          Digital Twins ({twins.length})
        </h2>
        <div className="flex gap-2">
          <button
            onClick={selectAllTwins}
            className="text-sm text-neon-blue hover:text-neon-green transition-colors"
          >
            Select All
          </button>
          <span className="text-neon-textsecondary">|</span>
          <button
            onClick={clearSelection}
            className="text-sm text-neon-textsecondary hover:text-neon-text transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      <p className="text-sm text-neon-textsecondary mb-4">
        Selected: <span className="text-neon-green font-semibold">{selectedTwinIds.length}</span> of {twins.length}
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[600px] overflow-y-auto scrollbar-thin pr-2">
        {twins.map((twin) => (
          <TwinCard key={twin.id} twin={twin} />
        ))}
      </div>
    </div>
  )
}

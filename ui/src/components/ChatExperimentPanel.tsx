import React, { useState } from 'react'
import { X, Zap } from 'lucide-react'
import { useStore } from '../store/useStore'

interface ChatExperimentPanelProps {
  isOpen: boolean
  onClose: () => void
  onRunExperiment: (config: any) => void
}

export const ChatExperimentPanel: React.FC<ChatExperimentPanelProps> = ({
  isOpen,
  onClose,
  onRunExperiment,
}) => {
  const { config: globalConfig } = useStore()

  const [localConfig, setLocalConfig] = useState({
    offerType: globalConfig.offerType,
    discountPct: globalConfig.discountPct,
    flightLength: globalConfig.flightLength,
    tripPurpose: globalConfig.tripPurpose,
    timePressure: globalConfig.timePressure,
    recentDelays: globalConfig.recentDelays,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onRunExperiment(localConfig)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="card max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-neon-surfacelight">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-neon-green" />
            <h3 className="font-bold text-lg">Test Offer</h3>
          </div>
          <button
            onClick={onClose}
            className="text-neon-textsecondary hover:text-neon-text transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Offer Type */}
          <div>
            <label className="block text-sm font-medium mb-2">Offer Type</label>
            <select
              value={localConfig.offerType}
              onChange={(e) =>
                setLocalConfig({ ...localConfig, offerType: e.target.value })
              }
              className="input w-full"
            >
              <option value="legroom">Extra Legroom</option>
              <option value="wifi">WiFi Access</option>
              <option value="lounge">Lounge Access</option>
              <option value="boarding">Priority Boarding</option>
              <option value="baggage">Extra Baggage</option>
            </select>
          </div>

          {/* Discount */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Discount: {(localConfig.discountPct * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={localConfig.discountPct}
              onChange={(e) =>
                setLocalConfig({ ...localConfig, discountPct: parseFloat(e.target.value) })
              }
              className="w-full"
            />
          </div>

          {/* Flight Length */}
          <div>
            <label className="block text-sm font-medium mb-2">Flight Length</label>
            <select
              value={localConfig.flightLength}
              onChange={(e) =>
                setLocalConfig({ ...localConfig, flightLength: e.target.value })
              }
              className="input w-full"
            >
              <option value="short">Short ({"<"}2h)</option>
              <option value="medium">Medium (2-6h)</option>
              <option value="long">Long ({">"}6h)</option>
            </select>
          </div>

          {/* Trip Purpose */}
          <div>
            <label className="block text-sm font-medium mb-2">Trip Purpose</label>
            <select
              value={localConfig.tripPurpose}
              onChange={(e) =>
                setLocalConfig({ ...localConfig, tripPurpose: e.target.value })
              }
              className="input w-full"
            >
              <option value="business">Business</option>
              <option value="leisure">Leisure</option>
            </select>
          </div>

          {/* Time Pressure */}
          <div>
            <label className="block text-sm font-medium mb-2">Time Pressure</label>
            <select
              value={localConfig.timePressure}
              onChange={(e) =>
                setLocalConfig({ ...localConfig, timePressure: e.target.value })
              }
              className="input w-full"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>

          {/* Recent Delays */}
          <div>
            <label className="block text-sm font-medium mb-2">Recent Delays</label>
            <select
              value={localConfig.recentDelays}
              onChange={(e) =>
                setLocalConfig({ ...localConfig, recentDelays: e.target.value })
              }
              className="input w-full"
            >
              <option value="none">None</option>
              <option value="minor">Minor</option>
              <option value="major">Major</option>
            </select>
          </div>

          {/* Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-neon-surfacelight text-neon-text rounded-lg hover:bg-neon-surfacelight/80 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 btn-primary"
            >
              <Zap className="w-4 h-4" />
              Run Test
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

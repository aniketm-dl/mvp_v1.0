import React, { useState } from 'react'
import { useStore } from '../store/useStore'
import { twinsAPI } from '../api/client'
import { Settings, Play, Loader } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'

export const ExperimentPanel: React.FC = () => {
  const { config, updateConfig, selectedTwinIds, setResults, setLoading, setError } = useStore()

  const runExperimentMutation = useMutation({
    mutationFn: async () => {
      if (selectedTwinIds.length === 0) {
        throw new Error('Please select at least one twin')
      }
      return await twinsAPI.batchDecide(selectedTwinIds, config)
    },
    onMutate: () => {
      setLoading(true)
      setError(null)
    },
    onSuccess: (data) => {
      setResults(data.results)
      setLoading(false)
      if (data.errors.length > 0) {
        setError(`${data.failed} requests failed`)
      }
    },
    onError: (error: Error) => {
      setError(error.message)
      setLoading(false)
    },
  })

  return (
    <div className="card">
      <h2 className="text-xl font-bold flex items-center gap-2 mb-6">
        <Settings className="text-neon-blue" size={24} />
        Experiment Configuration
      </h2>

      <div className="space-y-4">
        {/* Offer Type */}
        <div>
          <label className="block text-sm font-semibold text-neon-text mb-2">
            Offer Type
          </label>
          <select
            value={config.offerType}
            onChange={(e) => updateConfig({ offerType: e.target.value })}
            className="input w-full"
          >
            <option value="legroom">Extra Legroom Seat</option>
            <option value="wifi">Inflight WiFi Access</option>
            <option value="lounge">Airport Lounge Access</option>
            <option value="boarding">Priority Boarding</option>
            <option value="baggage">Extra Checked Baggage</option>
          </select>
        </div>

        {/* Discount Slider */}
        <div>
          <label className="block text-sm font-semibold text-neon-text mb-2">
            Discount: <span className="text-neon-green">{(config.discountPct * 100).toFixed(0)}%</span>
          </label>
          <input
            type="range"
            min="0"
            max="0.5"
            step="0.05"
            value={config.discountPct}
            onChange={(e) => updateConfig({ discountPct: parseFloat(e.target.value) })}
            className="w-full h-2 bg-neon-surfacelight rounded-lg appearance-none cursor-pointer slider"
            style={{
              background: `linear-gradient(to right, #B8FF00 0%, #B8FF00 ${config.discountPct * 200}%, #1A1A2E ${config.discountPct * 200}%, #1A1A2E 100%)`
            }}
          />
          <div className="flex justify-between text-xs text-neon-textsecondary mt-1">
            <span>0%</span>
            <span>50%</span>
          </div>
        </div>

        {/* Flight Context */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold text-neon-text mb-2">
              Flight Length
            </label>
            <select
              value={config.flightLength}
              onChange={(e) => updateConfig({ flightLength: e.target.value })}
              className="input w-full"
            >
              <option value="short">Short (&lt;3 hrs)</option>
              <option value="medium">Medium (3-6 hrs)</option>
              <option value="long">Long (&gt;6 hrs)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-neon-text mb-2">
              Trip Purpose
            </label>
            <select
              value={config.tripPurpose}
              onChange={(e) => updateConfig({ tripPurpose: e.target.value })}
              className="input w-full"
            >
              <option value="business">Business</option>
              <option value="leisure">Leisure</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold text-neon-text mb-2">
              Time Pressure
            </label>
            <select
              value={config.timePressure}
              onChange={(e) => updateConfig({ timePressure: e.target.value })}
              className="input w-full"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-neon-text mb-2">
              Recent Delays
            </label>
            <select
              value={config.recentDelays}
              onChange={(e) => updateConfig({ recentDelays: e.target.value })}
              className="input w-full"
            >
              <option value="none">None</option>
              <option value="minor">Minor</option>
              <option value="major">Major</option>
            </select>
          </div>
        </div>

        {/* Seed */}
        <div>
          <label className="block text-sm font-semibold text-neon-text mb-2">
            Random Seed (for reproducibility)
          </label>
          <input
            type="number"
            value={config.seed || 42}
            onChange={(e) => updateConfig({ seed: parseInt(e.target.value) || undefined })}
            className="input w-full"
            placeholder="42"
          />
        </div>

        {/* Run Button */}
        <button
          onClick={() => runExperimentMutation.mutate()}
          disabled={runExperimentMutation.isPending || selectedTwinIds.length === 0}
          className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {runExperimentMutation.isPending ? (
            <>
              <Loader className="animate-spin" size={20} />
              Running Experiment...
            </>
          ) : (
            <>
              <Play size={20} />
              Run Experiment ({selectedTwinIds.length} Twin{selectedTwinIds.length !== 1 ? 's' : ''})
            </>
          )}
        </button>

        {selectedTwinIds.length === 0 && (
          <p className="text-sm text-red-400 text-center">
            ⚠️ Please select at least one twin to run the experiment
          </p>
        )}
      </div>
    </div>
  )
}

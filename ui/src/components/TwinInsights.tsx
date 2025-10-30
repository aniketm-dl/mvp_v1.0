import React, { useState } from 'react'
import { useStore } from '../store/useStore'
import { User, Tag, Plane, DollarSign, Clock } from 'lucide-react'
import type { TwinDecision } from '../types'

export const TwinInsights: React.FC = () => {
  const { results, twins } = useStore()
  const [activeTwinIndex, setActiveTwinIndex] = useState(0)

  if (results.length === 0) {
    return (
      <div className="card text-center py-10">
        <p className="text-neon-textsecondary">
          No results yet. Run an experiment to see individual twin insights.
        </p>
      </div>
    )
  }

  const activeResult = results[activeTwinIndex]
  const activeTwin = twins.find(t => t.id === activeResult.twin_id)

  return (
    <div className="card">
      <h3 className="text-lg font-bold mb-4">Individual Twin Insights</h3>

      {/* Twin Tabs */}
      <div className="flex overflow-x-auto gap-2 mb-6 pb-2 scrollbar-thin">
        {results.map((result, index) => (
          <button
            key={result.twin_id}
            onClick={() => setActiveTwinIndex(index)}
            className={`px-4 py-2 rounded-lg font-semibold whitespace-nowrap transition-all ${
              index === activeTwinIndex
                ? 'bg-neon-green text-neon-darkbg'
                : 'bg-neon-surfacelight text-neon-textsecondary hover:text-neon-text'
            }`}
          >
            {result.twin_id}
          </button>
        ))}
      </div>

      {/* Twin Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left Column: Twin Info */}
        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-semibold text-neon-textsecondary mb-2">Twin Profile</h4>
            <div className="card-glow">
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 rounded-full bg-neon-green/20 flex items-center justify-center">
                  <User className="text-neon-green" size={24} />
                </div>
                <div className="flex-1">
                  <h5 className="font-bold text-neon-text mb-1">{activeResult.twin_label}</h5>
                  {activeTwin && (
                    <div className="space-y-1 text-sm text-neon-textsecondary">
                      <p>
                        <User className="inline w-4 h-4 mr-1" />
                        {activeTwin.demographics.gender}, {activeTwin.demographics.age_band}
                      </p>
                      <p>
                        <Plane className="inline w-4 h-4 mr-1" />
                        {activeTwin.travel_profile.type_of_travel} • {activeTwin.travel_profile.flight_class}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {activeTwin && activeTwin.psychographics.length > 0 && (
                <div className="mt-3 pt-3 border-t border-neon-surfacelight">
                  <p className="text-xs text-neon-textsecondary mb-2">Psychographics:</p>
                  <div className="flex flex-wrap gap-2">
                    {activeTwin.psychographics.map(tag => (
                      <span key={tag} className="badge-blue text-xs">
                        <Tag className="inline w-3 h-3 mr-1" />
                        {tag.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-neon-textsecondary mb-2">Offer Context</h4>
            <div className="card-glow space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-neon-textsecondary">Offer:</span>
                <span className="font-semibold text-neon-text">{activeResult.task.offer.name}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-neon-textsecondary">Discount:</span>
                <span className="font-semibold text-neon-green">
                  {(activeResult.task.offer.discount_pct * 100).toFixed(0)}% off
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-neon-textsecondary">Price:</span>
                <span className="font-semibold text-neon-text">
                  <DollarSign className="inline w-4 h-4" />
                  {activeResult.task.offer.absolute_price_delta.toFixed(2)}
                </span>
              </div>
              <div className="divider"></div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-neon-textsecondary">Flight:</span>
                  <p className="text-neon-text">{activeResult.task.context.flight_length}</p>
                </div>
                <div>
                  <span className="text-neon-textsecondary">Purpose:</span>
                  <p className="text-neon-text">{activeResult.task.context.trip_purpose}</p>
                </div>
                <div>
                  <span className="text-neon-textsecondary">Time Pressure:</span>
                  <p className="text-neon-text">{activeResult.task.context.time_pressure}</p>
                </div>
                <div>
                  <span className="text-neon-textsecondary">Delays:</span>
                  <p className="text-neon-text">{activeResult.task.context.recent_delays}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Decision & Rationale */}
        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-semibold text-neon-textsecondary mb-2">Decision</h4>
            <div className="card-glow text-center py-8">
              <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full mb-4 ${
                activeResult.response.decision === 'yes'
                  ? 'bg-neon-green/20 text-neon-green'
                  : 'bg-red-500/20 text-red-400'
              }`}>
                <span className="text-4xl font-bold">
                  {activeResult.response.decision === 'yes' ? '✓' : '✗'}
                </span>
              </div>
              <p className="text-3xl font-bold mb-2">
                {activeResult.response.decision.toUpperCase()}
              </p>
              <p className="text-neon-textsecondary text-sm">
                {activeResult.response.decision === 'yes' ? 'Accepts Offer' : 'Declines Offer'}
              </p>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-neon-textsecondary mb-2">Probability</h4>
            <div className="card-glow">
              <div className="flex items-center justify-between mb-2">
                <span className="text-neon-textsecondary">Confidence:</span>
                <span className="text-3xl font-bold text-neon-green">
                  {(activeResult.response.probability * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-neon-surfacelight rounded-full h-4 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-neon-green to-neon-blue rounded-full transition-all duration-500"
                  style={{ width: `${activeResult.response.probability * 100}%` }}
                />
              </div>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-neon-textsecondary mb-2">Rationale</h4>
            <div className="card-glow">
              <p className="text-neon-text leading-relaxed">
                "{activeResult.response.rationale}"
              </p>
              {activeResult.metadata.timestamp && (
                <p className="text-xs text-neon-textsecondary mt-3 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {new Date(activeResult.metadata.timestamp).toLocaleString()}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

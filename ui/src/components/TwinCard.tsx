import React from 'react'
import type { AirlineTwin } from '../types'
import { User, MapPin, Sparkles, Users, TrendingUp } from 'lucide-react'
import { useStore } from '../store/useStore'
import { getTwinName } from '../utils/twinNames'
import { useTwinMetrics } from '../hooks/useTwinMetrics'
import clsx from 'clsx'

interface TwinCardProps {
  twin: AirlineTwin
}

export const TwinCard: React.FC<TwinCardProps> = ({ twin }) => {
  const { selectedTwinIds, toggleTwinSelection } = useStore()
  const { metrics } = useTwinMetrics()
  const isSelected = selectedTwinIds.includes(twin.id)
  const twinName = getTwinName(twin.id)
  const twinMetrics = metrics.get(twin.id)

  return (
    <div
      onClick={() => toggleTwinSelection(twin.id)}
      className={clsx(
        'card cursor-pointer transition-all duration-200 hover:border-neon-blue/30',
        isSelected && 'border-neon-blue bg-neon-surface/80'
      )}
    >
      {/* Header with name and checkbox */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={clsx(
            'w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg',
            isSelected ? 'bg-neon-green text-black' : 'bg-neon-surfacelight text-neon-green'
          )}>
            {twinName.charAt(0)}
          </div>
          <div>
            <h3 className="font-bold text-base text-neon-text">{twinName}</h3>
            <p className="text-xs text-neon-textsecondary">{twin.id}</p>
          </div>
        </div>
        {isSelected && (
          <div className="w-6 h-6 rounded-full bg-neon-green flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-black" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
        )}
      </div>

      {/* Performance Metrics */}
      {twinMetrics && (
        <div className="mb-3 p-3 bg-gradient-to-r from-neon-surface to-neon-surfacelight rounded-lg border border-neon-blue/20">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-center gap-2">
              <Users size={14} className="text-neon-blue" />
              <div>
                <p className="text-xs text-neon-textsecondary">Customers</p>
                <p className="text-sm font-bold text-neon-text">
                  {twinMetrics.customer_count.toLocaleString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <TrendingUp size={14} className="text-neon-green" />
              <div>
                <p className="text-xs text-neon-textsecondary">Cohort Prior</p>
                <p className="text-sm font-bold text-neon-text">
                  {(twinMetrics.cohort_prior * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
          {twinMetrics.avg_satisfaction > 0 && (
            <div className="mt-2 pt-2 border-t border-neon-surface">
              <div className="flex items-center justify-between">
                <span className="text-xs text-neon-textsecondary">Satisfaction</span>
                <span className="text-xs font-semibold text-neon-green">
                  {(twinMetrics.avg_satisfaction * 100).toFixed(0)}%
                </span>
              </div>
              <div className="mt-1 h-1.5 bg-neon-surface rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-neon-blue to-neon-green rounded-full transition-all duration-500"
                  style={{ width: `${twinMetrics.avg_satisfaction * 100}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Demographics - More prominent */}
      <div className="mb-3 p-3 bg-neon-surfacelight rounded-lg border border-neon-surface">
        <div className="flex items-center gap-2 mb-2">
          <User size={16} className="text-neon-blue" />
          <span className="text-sm font-semibold text-neon-text">Demographics</span>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-neon-textsecondary">Gender:</span>
            <span className="ml-1 text-neon-text font-medium">{twin.demographics.gender}</span>
          </div>
          <div>
            <span className="text-neon-textsecondary">Age:</span>
            <span className="ml-1 text-neon-text font-medium">{twin.demographics.age_band}</span>
          </div>
        </div>
      </div>

      {/* Travel Profile */}
      <div className="mb-3 p-3 bg-neon-surfacelight rounded-lg border border-neon-surface">
        <div className="flex items-center gap-2 mb-2">
          <MapPin size={16} className="text-neon-blue" />
          <span className="text-sm font-semibold text-neon-text">Travel Profile</span>
        </div>
        <div className="space-y-1 text-xs">
          <div>
            <span className="text-neon-textsecondary">Purpose:</span>
            <span className="ml-1 text-neon-text font-medium">{twin.travel_profile.type_of_travel}</span>
          </div>
          <div>
            <span className="text-neon-textsecondary">Class:</span>
            <span className="ml-1 text-neon-text font-medium">{twin.travel_profile.flight_class}</span>
          </div>
          <div>
            <span className="text-neon-textsecondary">Distance:</span>
            <span className="ml-1 text-neon-text font-medium capitalize">{twin.travel_profile.distance_band}</span>
          </div>
        </div>
      </div>

      {/* Psychographics */}
      {twin.psychographics.length > 0 && (
        <div className="p-3 bg-neon-surfacelight rounded-lg border border-neon-surface">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles size={16} className="text-neon-green" />
            <span className="text-sm font-semibold text-neon-text">Traits</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {twin.psychographics.map((tag) => (
              <span key={tag} className="badge-blue text-xs px-2 py-1">
                {tag.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

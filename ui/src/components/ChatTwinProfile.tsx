import React, { useState } from 'react'
import { User, Plane, Heart, ChevronDown, ChevronUp, DollarSign } from 'lucide-react'
import type { AirlineTwin } from '../types'
import { getTwinName } from '../utils/twinNames'

interface ChatTwinProfileProps {
  twin: AirlineTwin | null
}

export const ChatTwinProfile: React.FC<ChatTwinProfileProps> = ({ twin }) => {
  const [showExperience, setShowExperience] = useState(false)

  if (!twin) {
    return (
      <div className="card p-6 text-center text-neon-textsecondary">
        <User className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>Select a twin to view their profile</p>
      </div>
    )
  }

  const twinName = getTwinName(twin.id)

  // Get recent experience data if available
  const recentExperience = (twin as any).recent_experience || {}
  const experienceKeys = Object.keys(recentExperience)

  // Get cohort priors for price sensitivity
  const cohortPriors = (twin as any).cohort_priors || {}
  const priceSensitivity = cohortPriors.price_sensitivity || 'unknown'

  return (
    <div className="space-y-4">
      {/* Twin Header */}
      <div className="card p-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-12 h-12 rounded-full bg-neon-blue/20 flex items-center justify-center text-neon-blue font-bold text-xl">
            {twinName.charAt(0)}
          </div>
          <div>
            <h3 className="font-bold text-lg">{twinName}</h3>
            <p className="text-xs text-neon-textsecondary">{twin.id}</p>
          </div>
        </div>
      </div>

      {/* Demographics */}
      <div className="card p-4">
        <div className="flex items-center gap-2 mb-3">
          <User className="w-4 h-4 text-neon-blue" />
          <h4 className="font-semibold text-sm">Demographics</h4>
        </div>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-neon-textsecondary">Gender:</span>
            <span className="font-medium">{twin.demographics.gender}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-neon-textsecondary">Age:</span>
            <span className="font-medium">
              {twin.demographics.age} ({twin.demographics.age_band})
            </span>
          </div>
        </div>
      </div>

      {/* Travel Profile */}
      <div className="card p-4">
        <div className="flex items-center gap-2 mb-3">
          <Plane className="w-4 h-4 text-neon-blue" />
          <h4 className="font-semibold text-sm">Travel Profile</h4>
        </div>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-neon-textsecondary">Type:</span>
            <span className="font-medium">{twin.travel_profile.customer_type}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-neon-textsecondary">Purpose:</span>
            <span className="font-medium">{twin.travel_profile.type_of_travel}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-neon-textsecondary">Class:</span>
            <span className="font-medium">{twin.travel_profile.flight_class}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-neon-textsecondary">Distance:</span>
            <span className="font-medium">{twin.travel_profile.distance_band}</span>
          </div>
        </div>
      </div>

      {/* Psychographics */}
      <div className="card p-4">
        <div className="flex items-center gap-2 mb-3">
          <Heart className="w-4 h-4 text-neon-green" />
          <h4 className="font-semibold text-sm">Psychographics</h4>
        </div>
        <div className="flex flex-wrap gap-2">
          {twin.psychographics.map((trait) => (
            <span
              key={trait}
              className="px-2 py-1 bg-neon-green/10 border border-neon-green/30 rounded text-xs font-medium"
            >
              {trait.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      </div>

      {/* Price Sensitivity */}
      {priceSensitivity !== 'unknown' && (
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-3">
            <DollarSign className="w-4 h-4 text-neon-green" />
            <h4 className="font-semibold text-sm">Price Sensitivity</h4>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-neon-surfacelight rounded-full overflow-hidden">
              <div
                className={`h-full ${
                  priceSensitivity === 'high'
                    ? 'bg-red-500 w-[90%]'
                    : priceSensitivity === 'medium'
                    ? 'bg-yellow-500 w-[60%]'
                    : 'bg-green-500 w-[30%]'
                }`}
              />
            </div>
            <span className="text-sm font-medium capitalize">{priceSensitivity}</span>
          </div>
        </div>
      )}

      {/* Recent Experience (Collapsible) */}
      {experienceKeys.length > 0 && (
        <div className="card p-4">
          <button
            onClick={() => setShowExperience(!showExperience)}
            className="flex items-center justify-between w-full text-left"
          >
            <div className="flex items-center gap-2">
              <Heart className="w-4 h-4 text-neon-blue" />
              <h4 className="font-semibold text-sm">Recent Experience</h4>
            </div>
            {showExperience ? (
              <ChevronUp className="w-4 h-4 text-neon-textsecondary" />
            ) : (
              <ChevronDown className="w-4 h-4 text-neon-textsecondary" />
            )}
          </button>

          {showExperience && (
            <div className="mt-3 space-y-2">
              {experienceKeys.map((key) => {
                const rating = recentExperience[key]
                const label = key.replace(/_/g, ' ')
                return (
                  <div key={key} className="text-xs">
                    <div className="flex justify-between mb-1">
                      <span className="text-neon-textsecondary capitalize">{label}:</span>
                      <span className="font-medium">{rating}/5</span>
                    </div>
                    <div className="h-1.5 bg-neon-surfacelight rounded-full overflow-hidden">
                      <div
                        className={`h-full ${
                          rating >= 4
                            ? 'bg-neon-green'
                            : rating >= 3
                            ? 'bg-neon-blue'
                            : 'bg-red-500'
                        }`}
                        style={{ width: `${(rating / 5) * 100}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

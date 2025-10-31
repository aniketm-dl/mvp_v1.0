import React, { useEffect, useState } from 'react'
import { Info, Database, Activity } from 'lucide-react'

interface DatasetInfo {
  demographics: {
    gender: Record<string, number>
    customer_type: Record<string, number>
    type_of_travel: Record<string, number>
    flight_class: Record<string, number>
    age: {
      min: number
      max: number
      mean: number
      median: number
    }
  }
  service_ratings_summary: {
    mean_rating: number
    std_rating: number
  }
  flight_details: {
    flight_distance: {
      min: number
      max: number
      mean: number
      median: number
    }
  }
}

export const ValidationInfo: React.FC = () => {
  const [datasetInfo, setDatasetInfo] = useState<DatasetInfo | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('http://localhost:8000/metrics/validation')
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`)
        }
        return res.json()
      })
      .then(data => {
        console.log('Dataset info loaded:', data)
        setDatasetInfo(data.dataset_info)
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load dataset info:', err)
        setDatasetInfo(null)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="h-4 bg-neon-surfacelight rounded w-1/2 mb-4"></div>
          <div className="h-4 bg-neon-surfacelight rounded w-3/4"></div>
        </div>
      </div>
    )
  }

  if (!datasetInfo) {
    return (
      <div className="card">
        <p className="text-neon-textsecondary">Failed to load dataset information</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Demographics Card */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Database size={20} className="text-neon-blue" />
          <h3 className="text-lg font-bold text-neon-text">Dataset Demographics</h3>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Gender Distribution */}
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-neon-textsecondary">Gender</h4>
            {Object.entries(datasetInfo.demographics.gender || {}).map(([key, value]) => (
              <div key={key} className="flex justify-between text-sm">
                <span className="text-neon-text">{key}</span>
                <span className="text-neon-blue font-mono">{value}</span>
              </div>
            ))}
          </div>

          {/* Customer Type */}
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-neon-textsecondary">Customer Type</h4>
            {Object.entries(datasetInfo.demographics.customer_type || {}).map(([key, value]) => (
              <div key={key} className="flex justify-between text-sm">
                <span className="text-neon-text">{key}</span>
                <span className="text-neon-blue font-mono">{value}</span>
              </div>
            ))}
          </div>

          {/* Travel Type */}
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-neon-textsecondary">Travel Purpose</h4>
            {Object.entries(datasetInfo.demographics.type_of_travel || {}).map(([key, value]) => (
              <div key={key} className="flex justify-between text-sm">
                <span className="text-neon-text">{key}</span>
                <span className="text-neon-blue font-mono">{value}</span>
              </div>
            ))}
          </div>

          {/* Flight Class */}
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-neon-textsecondary">Flight Class</h4>
            {Object.entries(datasetInfo.demographics.flight_class || {}).map(([key, value]) => (
              <div key={key} className="flex justify-between text-sm">
                <span className="text-neon-text">{key}</span>
                <span className="text-neon-blue font-mono">{value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Age Statistics */}
        <div className="mt-4 pt-4 border-t border-neon-surfacelight/30">
          <h4 className="text-sm font-semibold text-neon-textsecondary mb-2">Age Statistics</h4>
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-neon-textsecondary">Min</p>
              <p className="text-neon-text font-mono">{datasetInfo.demographics.age?.min}</p>
            </div>
            <div>
              <p className="text-neon-textsecondary">Max</p>
              <p className="text-neon-text font-mono">{datasetInfo.demographics.age?.max}</p>
            </div>
            <div>
              <p className="text-neon-textsecondary">Mean</p>
              <p className="text-neon-text font-mono">
                {datasetInfo.demographics.age?.mean.toFixed(1)}
              </p>
            </div>
            <div>
              <p className="text-neon-textsecondary">Median</p>
              <p className="text-neon-text font-mono">
                {datasetInfo.demographics.age?.median.toFixed(1)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Service Ratings Card */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Activity size={20} className="text-neon-green" />
          <h3 className="text-lg font-bold text-neon-text">Service Quality Metrics</h3>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-neon-surfacelight rounded-lg">
            <p className="text-neon-textsecondary text-sm mb-1">Average Rating</p>
            <p className="text-2xl font-bold text-neon-green">
              {datasetInfo.service_ratings_summary.mean_rating.toFixed(2)}
            </p>
            <p className="text-xs text-neon-textsecondary mt-1">out of 5.0</p>
          </div>

          <div className="p-4 bg-neon-surfacelight rounded-lg">
            <p className="text-neon-textsecondary text-sm mb-1">Std Deviation</p>
            <p className="text-2xl font-bold text-neon-blue">
              {datasetInfo.service_ratings_summary.std_rating.toFixed(2)}
            </p>
            <p className="text-xs text-neon-textsecondary mt-1">rating variance</p>
          </div>
        </div>

        {/* Flight Distance Stats */}
        <div className="mt-4 pt-4 border-t border-neon-surfacelight/30">
          <h4 className="text-sm font-semibold text-neon-textsecondary mb-2">
            Flight Distance Statistics
          </h4>
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-neon-textsecondary">Min</p>
              <p className="text-neon-text font-mono">
                {datasetInfo.flight_details?.flight_distance?.min.toFixed(0)} km
              </p>
            </div>
            <div>
              <p className="text-neon-textsecondary">Max</p>
              <p className="text-neon-text font-mono">
                {datasetInfo.flight_details?.flight_distance?.max.toFixed(0)} km
              </p>
            </div>
            <div>
              <p className="text-neon-textsecondary">Mean</p>
              <p className="text-neon-text font-mono">
                {datasetInfo.flight_details?.flight_distance?.mean.toFixed(0)} km
              </p>
            </div>
            <div>
              <p className="text-neon-textsecondary">Median</p>
              <p className="text-neon-text font-mono">
                {datasetInfo.flight_details?.flight_distance?.median.toFixed(0)} km
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
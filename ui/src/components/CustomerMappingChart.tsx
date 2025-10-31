import React, { useEffect, useState } from 'react'
import { Users, BarChart3 } from 'lucide-react'
import { getTwinName } from '../utils/twinNames'

interface TwinMetric {
  twin_id: string
  label: string
  customer_count: number
  cohort_prior: number
  satisfaction_rate: number | null
}

export const CustomerMappingChart: React.FC = () => {
  const [twinMetrics, setTwinMetrics] = useState<TwinMetric[]>([])
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
        console.log('Twin metrics data loaded:', data)
        setTwinMetrics(data.twin_metrics || [])
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load twin metrics:', err)
        setTwinMetrics([]) // Set empty array on error
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="h-4 bg-neon-surfacelight rounded w-1/2 mb-4"></div>
          <div className="space-y-2">
            <div className="h-8 bg-neon-surfacelight rounded"></div>
            <div className="h-8 bg-neon-surfacelight rounded"></div>
            <div className="h-8 bg-neon-surfacelight rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (twinMetrics.length === 0) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Users size={20} className="text-neon-green" />
          <h3 className="text-lg font-bold text-neon-text">Customer Distribution</h3>
        </div>
        <p className="text-neon-textsecondary">No twin data available</p>
      </div>
    )
  }

  const maxCount = Math.max(...twinMetrics.map(t => t.customer_count), 1)

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <Users size={20} className="text-neon-green" />
        <h3 className="text-lg font-bold text-neon-text">Customer Distribution</h3>
      </div>

      <div className="space-y-3">
        {twinMetrics.map(twin => {
          const percentage = (twin.customer_count / 400) * 100 // Based on total 400 samples
          const barWidth = (twin.customer_count / maxCount) * 100

          return (
            <div key={twin.twin_id} className="space-y-1">
              <div className="flex justify-between items-center text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-neon-text font-medium">
                    {getTwinName(twin.twin_id)}
                  </span>
                  <span className="text-neon-textsecondary text-xs">
                    ({twin.twin_id})
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-neon-blue font-mono">
                    {twin.customer_count}
                  </span>
                  <span className="text-neon-textsecondary">
                    ({percentage.toFixed(1)}%)
                  </span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="relative h-6 bg-neon-surfacelight rounded-lg overflow-hidden">
                <div
                  className="absolute inset-y-0 left-0 bg-gradient-to-r from-neon-blue to-neon-green rounded-lg transition-all duration-500"
                  style={{ width: `${barWidth}%` }}
                />
                {/* Cohort Prior Indicator */}
                <div className="absolute inset-y-0 flex items-center px-2">
                  <span className="text-xs text-neon-darkbg font-semibold">
                    Prior: {(twin.cohort_prior * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Additional Metrics */}
              <div className="flex gap-4 text-xs text-neon-textsecondary">
                {twin.satisfaction_rate && (
                  <span>
                    Satisfaction: {(twin.satisfaction_rate * 100).toFixed(0)}%
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Summary Stats */}
      <div className="mt-4 pt-4 border-t border-neon-surfacelight/30">
        <div className="grid grid-cols-3 gap-2 text-sm">
          <div>
            <p className="text-neon-textsecondary">Total Twins</p>
            <p className="text-neon-text font-bold">{twinMetrics.length}</p>
          </div>
          <div>
            <p className="text-neon-textsecondary">Total Customers</p>
            <p className="text-neon-text font-bold">
              {twinMetrics.reduce((sum, t) => sum + t.customer_count, 0)}
            </p>
          </div>
          <div>
            <p className="text-neon-textsecondary">Avg per Twin</p>
            <p className="text-neon-text font-bold">
              {Math.round(
                twinMetrics.reduce((sum, t) => sum + t.customer_count, 0) /
                  Math.max(twinMetrics.length, 1)
              )}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
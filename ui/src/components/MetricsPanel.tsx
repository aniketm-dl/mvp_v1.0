import React, { useEffect, useState } from 'react'
import { CheckCircle, XCircle, TrendingUp } from 'lucide-react'

interface ValidationMetrics {
  silhouette_score: number
  jensen_shannon_divergence: number
  ari_stability: number
  thresholds: {
    silhouette_min: number
    mean_jsd_min: number
    ari_min: number
  }
}

interface MetricsData {
  validation_metrics: ValidationMetrics
  training_info: {
    total_samples: number
    train_samples: number
    test_samples: number
    model_version: string
    training_date: string
  }
}

export const MetricsPanel: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null)
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
        console.log('Metrics data loaded:', data)
        setMetrics(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load metrics:', err)
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

  if (!metrics) {
    return (
      <div className="card">
        <p className="text-neon-textsecondary">Failed to load metrics</p>
      </div>
    )
  }

  const { validation_metrics, training_info } = metrics

  const MetricRow = ({
    label,
    value,
    threshold,
    isHigherBetter = true
  }: {
    label: string
    value: number
    threshold: number
    isHigherBetter?: boolean
  }) => {
    const passed = isHigherBetter ? value >= threshold : value <= threshold

    return (
      <div className="flex items-center justify-between py-2 border-b border-neon-surfacelight/30">
        <div className="flex items-center gap-2">
          <span className="text-neon-textsecondary text-sm">{label}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-neon-text font-mono">{value.toFixed(3)}</span>
          <span className="text-neon-textsecondary text-sm">
            (≥ {threshold.toFixed(2)})
          </span>
          {passed ? (
            <CheckCircle size={16} className="text-neon-green" />
          ) : (
            <XCircle size={16} className="text-red-500" />
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Validation Metrics Card */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp size={20} className="text-neon-blue" />
          <h3 className="text-lg font-bold text-neon-text">Validation Metrics</h3>
        </div>

        <div className="space-y-1">
          <MetricRow
            label="Silhouette Score"
            value={validation_metrics.silhouette_score}
            threshold={validation_metrics.thresholds.silhouette_min}
          />
          <MetricRow
            label="Jensen-Shannon Divergence"
            value={validation_metrics.jensen_shannon_divergence}
            threshold={validation_metrics.thresholds.mean_jsd_min}
          />
          <MetricRow
            label="ARI Stability"
            value={validation_metrics.ari_stability}
            threshold={validation_metrics.thresholds.ari_min}
          />
        </div>
      </div>

      {/* Training Info Card */}
      <div className="card">
        <h3 className="text-lg font-bold text-neon-text mb-4">Training Information</h3>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-neon-textsecondary text-sm">Model Version</p>
            <p className="text-neon-text font-mono">{training_info.model_version}</p>
          </div>
          <div>
            <p className="text-neon-textsecondary text-sm">Training Date</p>
            <p className="text-neon-text font-mono">{training_info.training_date}</p>
          </div>
          <div>
            <p className="text-neon-textsecondary text-sm">Total Samples</p>
            <p className="text-neon-text font-mono">{training_info.total_samples}</p>
          </div>
          <div>
            <p className="text-neon-textsecondary text-sm">Train/Test Split</p>
            <p className="text-neon-text font-mono">
              {training_info.train_samples}/{training_info.test_samples}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
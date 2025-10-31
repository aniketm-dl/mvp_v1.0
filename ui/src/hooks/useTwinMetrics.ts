import { useEffect, useState } from 'react'

interface TwinPerformance {
  twin_id: string
  cohort_prior: number
  customer_count: number
  avg_satisfaction: number
}

interface MetricsData {
  twin_performance: TwinPerformance[]
}

const metricsCache: { data: MetricsData | null; timestamp: number } = {
  data: null,
  timestamp: 0
}

const CACHE_DURATION = 60000 // 1 minute cache

export function useTwinMetrics() {
  const [metrics, setMetrics] = useState<Map<string, TwinPerformance>>(new Map())
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadMetrics = async () => {
      const now = Date.now()

      // Check cache
      if (metricsCache.data && (now - metricsCache.timestamp) < CACHE_DURATION) {
        const metricsMap = new Map(
          metricsCache.data.twin_performance.map(perf => [perf.twin_id, perf])
        )
        setMetrics(metricsMap)
        setLoading(false)
        return
      }

      try {
        const response = await fetch('http://localhost:8000/metrics/validation')
        if (!response.ok) throw new Error('Failed to fetch metrics')

        const data: MetricsData = await response.json()

        // Update cache
        metricsCache.data = data
        metricsCache.timestamp = now

        // Convert to Map for easy lookup
        const metricsMap = new Map(
          data.twin_performance.map(perf => [perf.twin_id, perf])
        )
        setMetrics(metricsMap)
      } catch (error) {
        console.error('Failed to load twin metrics:', error)
      } finally {
        setLoading(false)
      }
    }

    loadMetrics()
  }, [])

  return { metrics, loading }
}
import React, { useMemo } from 'react'
import { useStore } from '../store/useStore'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { TrendingUp, CheckCircle, XCircle } from 'lucide-react'

export const ResultsAggregated: React.FC = () => {
  const { results, isLoading, error } = useStore()

  const aggregatedData = useMemo(() => {
    if (results.length === 0) return null

    const acceptanceRate = results.filter(r => r.response.decision === 'yes').length / results.length
    const avgProbability = results.reduce((sum, r) => sum + r.response.probability, 0) / results.length

    const chartData = results
      .sort((a, b) => b.response.probability - a.response.probability)
      .map(r => ({
        twin: r.twin_id,
        probability: r.response.probability,
        decision: r.response.decision,
      }))

    return {
      acceptanceRate,
      avgProbability,
      chartData,
      yesCount: results.filter(r => r.response.decision === 'yes').length,
      noCount: results.filter(r => r.response.decision === 'no').length,
    }
  }, [results])

  if (isLoading) {
    return (
      <div className="card flex items-center justify-center py-20">
        <div className="text-center">
          <div className="animate-spin w-12 h-12 border-4 border-neon-green border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-neon-textsecondary">Running experiment...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card bg-red-500/10 border-red-500/30">
        <p className="text-red-400">❌ {error}</p>
      </div>
    )
  }

  if (!aggregatedData) {
    return (
      <div className="card text-center py-20">
        <TrendingUp className="w-16 h-16 text-neon-textsecondary mx-auto mb-4" />
        <p className="text-neon-textsecondary text-lg">
          Configure and run an experiment to see results
        </p>
      </div>
    )
  }

  const { acceptanceRate, avgProbability, chartData, yesCount, noCount } = aggregatedData

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card text-center">
          <p className="text-neon-textsecondary text-sm mb-2">Acceptance Rate</p>
          <p className="text-4xl font-bold text-neon-green">
            {(acceptanceRate * 100).toFixed(1)}%
          </p>
          <p className="text-neon-textsecondary text-xs mt-2">
            {yesCount} accepted / {results.length} total
          </p>
        </div>

        <div className="card text-center">
          <p className="text-neon-textsecondary text-sm mb-2">Avg Probability</p>
          <p className="text-4xl font-bold text-neon-blue">
            {(avgProbability * 100).toFixed(1)}%
          </p>
          <p className="text-neon-textsecondary text-xs mt-2">
            Across all {results.length} twins
          </p>
        </div>

        <div className="card text-center">
          <p className="text-neon-textsecondary text-sm mb-2">Decision Split</p>
          <div className="flex items-center justify-center gap-4 mt-2">
            <div className="flex items-center gap-2">
              <CheckCircle className="text-neon-green" size={20} />
              <span className="text-2xl font-bold text-neon-text">{yesCount}</span>
            </div>
            <div className="text-neon-textsecondary">/</div>
            <div className="flex items-center gap-2">
              <XCircle className="text-red-400" size={20} />
              <span className="text-2xl font-bold text-neon-text">{noCount}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="card">
        <h3 className="text-lg font-bold mb-4">Acceptance Probability by Twin</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#252540" />
            <XAxis
              dataKey="twin"
              stroke="#A0A0B0"
              tick={{ fill: '#A0A0B0', fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis
              stroke="#A0A0B0"
              tick={{ fill: '#A0A0B0', fontSize: 12 }}
              domain={[0, 1]}
              tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1A1A2E',
                border: '1px solid #252540',
                borderRadius: '8px',
                color: '#FFFFFF',
              }}
              formatter={(value: number) => [`${(value * 100).toFixed(1)}%`, 'Probability']}
            />
            <Bar dataKey="probability" radius={[8, 8, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.decision === 'yes' ? '#B8FF00' : '#EF4444'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Results Table */}
      <div className="card">
        <h3 className="text-lg font-bold mb-4">Detailed Results</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neon-surfacelight">
                <th className="text-left py-3 px-4 text-neon-textsecondary font-semibold">Twin</th>
                <th className="text-left py-3 px-4 text-neon-textsecondary font-semibold">Decision</th>
                <th className="text-left py-3 px-4 text-neon-textsecondary font-semibold">Probability</th>
                <th className="text-left py-3 px-4 text-neon-textsecondary font-semibold">Rationale</th>
              </tr>
            </thead>
            <tbody>
              {results.map((result) => (
                <tr key={result.twin_id} className="border-b border-neon-surfacelight hover:bg-neon-surfacelight/30 transition-colors">
                  <td className="py-3 px-4 font-mono text-neon-blue">{result.twin_id}</td>
                  <td className="py-3 px-4">
                    <span className={result.response.decision === 'yes' ? 'decision-yes' : 'decision-no'}>
                      {result.response.decision.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-neon-surfacelight rounded-full h-2 overflow-hidden">
                        <div
                          className="h-full bg-neon-green rounded-full"
                          style={{ width: `${result.response.probability * 100}%` }}
                        />
                      </div>
                      <span className="text-neon-text font-semibold w-12 text-right">
                        {(result.response.probability * 100).toFixed(0)}%
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-neon-textsecondary max-w-md truncate">
                    {result.response.rationale}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

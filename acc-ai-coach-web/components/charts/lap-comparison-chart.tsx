'use client'

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from 'recharts'
import { TelemetryFrame } from '@/lib/supabase'

interface LapComparisonChartProps {
  lap1Data: TelemetryFrame[]
  lap2Data: TelemetryFrame[]
  lap1Label?: string
  lap2Label?: string
}

export function LapComparisonChart({
  lap1Data,
  lap2Data,
  lap1Label = 'Your Lap',
  lap2Label = 'Reference',
}: LapComparisonChartProps) {
  // Merge data by position for comparison
  const mergedData = lap1Data.map((frame, i) => {
    const lap2Frame = lap2Data.find(f => 
      Math.abs(f.position - frame.position) < 0.01
    ) || lap2Data[i]

    return {
      position: frame.position,
      speed1: frame.speed_kmh,
      speed2: lap2Frame?.speed_kmh || 0,
      speedDelta: frame.speed_kmh - (lap2Frame?.speed_kmh || 0),
      throttle1: frame.throttle,
      throttle2: lap2Frame?.throttle || 0,
      brake1: frame.brake,
      brake2: lap2Frame?.brake || 0,
    }
  })

  // Calculate cumulative time delta (simplified)
  let cumulativeDelta = 0
  const dataWithDelta = mergedData.map((d, i) => {
    if (i > 0) {
      // Rough time delta based on speed difference
      const speedDiff = d.speed1 - d.speed2
      cumulativeDelta += speedDiff * -0.001 // Simplified calculation
    }
    return {
      ...d,
      timeDelta: cumulativeDelta * 1000, // Convert to ms
    }
  })

  return (
    <div className="space-y-6">
      {/* Speed Comparison */}
      <div>
        <h4 className="text-sm font-medium text-zinc-400 mb-2">Speed Comparison</h4>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={dataWithDelta}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis
                dataKey="position"
                tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                stroke="#666"
              />
              <YAxis stroke="#666" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                labelFormatter={(v) => `Position: ${(Number(v) * 100).toFixed(1)}%`}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="speed1"
                name={lap1Label}
                stroke="#ef4444"
                dot={false}
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="speed2"
                name={lap2Label}
                stroke="#22c55e"
                dot={false}
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Time Delta */}
      <div>
        <h4 className="text-sm font-medium text-zinc-400 mb-2">Time Delta</h4>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={dataWithDelta}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis
                dataKey="position"
                tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                stroke="#666"
              />
              <YAxis 
                stroke="#666"
                tickFormatter={(v) => `${v > 0 ? '+' : ''}${v.toFixed(0)}ms`}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                labelFormatter={(v) => `Position: ${(Number(v) * 100).toFixed(1)}%`}
                formatter={(v: number) => `${v > 0 ? '+' : ''}${v.toFixed(0)}ms`}
              />
              <ReferenceLine y={0} stroke="#666" strokeDasharray="3 3" />
              <Line
                type="monotone"
                dataKey="timeDelta"
                name="Delta"
                stroke="#f59e0b"
                fill="#f59e0b"
                dot={false}
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Inputs Comparison */}
      <div>
        <h4 className="text-sm font-medium text-zinc-400 mb-2">Inputs Comparison</h4>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={dataWithDelta}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis
                dataKey="position"
                tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                stroke="#666"
              />
              <YAxis stroke="#666" domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                labelFormatter={(v) => `Position: ${(Number(v) * 100).toFixed(1)}%`}
                formatter={(v: number) => `${(v * 100).toFixed(1)}%`}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="throttle1"
                name={`${lap1Label} Throttle`}
                stroke="#ef4444"
                dot={false}
                strokeWidth={1}
                opacity={0.8}
              />
              <Line
                type="monotone"
                dataKey="throttle2"
                name={`${lap2Label} Throttle`}
                stroke="#22c55e"
                dot={false}
                strokeWidth={1}
                opacity={0.8}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

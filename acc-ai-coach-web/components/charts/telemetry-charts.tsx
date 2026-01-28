'use client'

import { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  AreaChart,
  Area,
} from 'recharts'
import { TelemetryFrame } from '@/lib/supabase'

interface TelemetryChartsProps {
  sessionId: string
  telemetryData?: TelemetryFrame[]
}

// Generate demo data for display
function generateDemoData(): TelemetryFrame[] {
  const data: TelemetryFrame[] = []
  
  for (let i = 0; i < 100; i++) {
    const position = i / 100
    const t = position * Math.PI * 10
    
    data.push({
      position,
      speed_kmh: 180 + 80 * Math.sin(t) + Math.random() * 10,
      throttle: Math.max(0, Math.min(1, 0.5 + 0.5 * Math.cos(t + 0.5))),
      brake: Math.max(0, Math.min(1, -0.5 * Math.cos(t + 0.5) - 0.3)),
      steering: 30 * Math.sin(t * 0.5),
      gear: Math.floor(3 + 3 * Math.sin(t)),
      rpm: 5000 + 3000 * Math.sin(t),
      lap: 1,
      g_lat: Math.sin(t * 0.5) * 1.5,
      g_lon: Math.cos(t) * 2,
      temp_fl: 85 + Math.random() * 5,
      temp_fr: 84 + Math.random() * 5,
      temp_rl: 82 + Math.random() * 5,
      temp_rr: 81 + Math.random() * 5,
    })
  }
  
  return data
}

export function TelemetryCharts({ sessionId, telemetryData }: TelemetryChartsProps) {
  const [data, setData] = useState<TelemetryFrame[]>([])
  const [activeChart, setActiveChart] = useState<'speed' | 'inputs' | 'temps' | 'gforce'>('speed')

  useEffect(() => {
    if (telemetryData && telemetryData.length > 0) {
      setData(telemetryData)
    } else {
      // Use demo data for display
      setData(generateDemoData())
    }
  }, [telemetryData])

  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-zinc-500">
        <p>No telemetry data available</p>
        <p className="text-sm mt-2">Telemetry will appear here after recording a session</p>
      </div>
    )
  }

  const chartTabs = [
    { id: 'speed', label: 'Speed & RPM' },
    { id: 'inputs', label: 'Inputs' },
    { id: 'temps', label: 'Tire Temps' },
    { id: 'gforce', label: 'G-Forces' },
  ] as const

  return (
    <div className="space-y-4">
      {/* Chart tabs */}
      <div className="flex space-x-2 border-b border-zinc-800 pb-2">
        {chartTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveChart(tab.id)}
            className={`px-4 py-2 text-sm font-medium rounded-t-md transition-colors ${
              activeChart === tab.id
                ? 'bg-zinc-800 text-zinc-100'
                : 'text-zinc-400 hover:text-zinc-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Speed & RPM Chart */}
      {activeChart === 'speed' && (
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis
                dataKey="position"
                tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                stroke="#666"
              />
              <YAxis yAxisId="speed" stroke="#666" domain={[0, 'auto']} />
              <YAxis yAxisId="rpm" orientation="right" stroke="#666" domain={[0, 'auto']} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                labelFormatter={(v) => `Position: ${(Number(v) * 100).toFixed(1)}%`}
              />
              <Legend />
              <Line
                yAxisId="speed"
                type="monotone"
                dataKey="speed_kmh"
                name="Speed (km/h)"
                stroke="#22c55e"
                dot={false}
                strokeWidth={2}
              />
              <Line
                yAxisId="rpm"
                type="monotone"
                dataKey="rpm"
                name="RPM"
                stroke="#ef4444"
                dot={false}
                strokeWidth={1}
                opacity={0.7}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Inputs Chart */}
      {activeChart === 'inputs' && (
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
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
              <Area
                type="monotone"
                dataKey="throttle"
                name="Throttle"
                stroke="#22c55e"
                fill="#22c55e"
                fillOpacity={0.3}
                strokeWidth={2}
              />
              <Area
                type="monotone"
                dataKey="brake"
                name="Brake"
                stroke="#ef4444"
                fill="#ef4444"
                fillOpacity={0.3}
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Tire Temps Chart */}
      {activeChart === 'temps' && (
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis
                dataKey="position"
                tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                stroke="#666"
              />
              <YAxis stroke="#666" domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                labelFormatter={(v) => `Position: ${(Number(v) * 100).toFixed(1)}%`}
                formatter={(v: number) => `${v.toFixed(1)}°C`}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="temp_fl"
                name="FL"
                stroke="#ef4444"
                dot={false}
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="temp_fr"
                name="FR"
                stroke="#22c55e"
                dot={false}
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="temp_rl"
                name="RL"
                stroke="#3b82f6"
                dot={false}
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="temp_rr"
                name="RR"
                stroke="#eab308"
                dot={false}
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* G-Force Chart */}
      {activeChart === 'gforce' && (
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis
                dataKey="position"
                tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                stroke="#666"
              />
              <YAxis stroke="#666" domain={[-3, 3]} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                labelFormatter={(v) => `Position: ${(Number(v) * 100).toFixed(1)}%`}
                formatter={(v: number) => `${v.toFixed(2)}G`}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="g_lat"
                name="Lateral G"
                stroke="#a855f7"
                dot={false}
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="g_lon"
                name="Longitudinal G"
                stroke="#06b6d4"
                dot={false}
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

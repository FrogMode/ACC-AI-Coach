'use client'

import { TelemetryFrame } from '@/lib/supabase'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  ResponsiveContainer,
} from 'recharts'

interface LiveTelemetryDisplayProps {
  telemetry: TelemetryFrame | null
  history: TelemetryFrame[]
}

export function LiveTelemetryDisplay({ telemetry, history }: LiveTelemetryDisplayProps) {
  if (!telemetry) {
    return null
  }

  return (
    <div className="space-y-6">
      {/* Main gauges */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Speed */}
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-sm text-zinc-400 mb-2">Speed</p>
            <p className="text-5xl font-bold text-zinc-100">
              {telemetry.speed_kmh.toFixed(0)}
            </p>
            <p className="text-sm text-zinc-500">km/h</p>
          </CardContent>
        </Card>

        {/* RPM */}
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-sm text-zinc-400 mb-2">RPM</p>
            <p className="text-5xl font-bold text-red-500">
              {telemetry.rpm.toFixed(0)}
            </p>
            <p className="text-sm text-zinc-500">rev/min</p>
          </CardContent>
        </Card>

        {/* Gear */}
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-sm text-zinc-400 mb-2">Gear</p>
            <p className="text-5xl font-bold text-zinc-100">
              {telemetry.gear === 0 ? 'R' : telemetry.gear === 1 ? 'N' : telemetry.gear - 1}
            </p>
          </CardContent>
        </Card>

        {/* Lap */}
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-sm text-zinc-400 mb-2">Lap</p>
            <p className="text-5xl font-bold text-zinc-100">
              {telemetry.lap}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Inputs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Throttle/Brake bars */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Inputs</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Throttle */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-zinc-400">Throttle</span>
                <span className="text-green-500">{(telemetry.throttle * 100).toFixed(0)}%</span>
              </div>
              <div className="h-4 bg-zinc-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-green-500 transition-all duration-100"
                  style={{ width: `${telemetry.throttle * 100}%` }}
                />
              </div>
            </div>

            {/* Brake */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-zinc-400">Brake</span>
                <span className="text-red-500">{(telemetry.brake * 100).toFixed(0)}%</span>
              </div>
              <div className="h-4 bg-zinc-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-red-500 transition-all duration-100"
                  style={{ width: `${telemetry.brake * 100}%` }}
                />
              </div>
            </div>

            {/* Steering */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-zinc-400">Steering</span>
                <span className="text-yellow-500">{telemetry.steering.toFixed(1)}°</span>
              </div>
              <div className="h-4 bg-zinc-800 rounded-full overflow-hidden relative">
                <div className="absolute left-1/2 top-0 bottom-0 w-px bg-zinc-600" />
                <div 
                  className="absolute top-0 bottom-0 w-2 bg-yellow-500 rounded-full transition-all duration-100"
                  style={{ 
                    left: `calc(50% + ${(telemetry.steering / 180) * 50}% - 4px)` 
                  }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tire temps */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Tire Temperatures</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              {/* Front Left */}
              <div className="text-center p-4 bg-zinc-800/50 rounded-lg">
                <p className="text-xs text-zinc-500 mb-1">FL</p>
                <p className={`text-2xl font-bold ${getTempColor(telemetry.temp_fl)}`}>
                  {telemetry.temp_fl.toFixed(0)}°
                </p>
              </div>
              
              {/* Front Right */}
              <div className="text-center p-4 bg-zinc-800/50 rounded-lg">
                <p className="text-xs text-zinc-500 mb-1">FR</p>
                <p className={`text-2xl font-bold ${getTempColor(telemetry.temp_fr)}`}>
                  {telemetry.temp_fr.toFixed(0)}°
                </p>
              </div>
              
              {/* Rear Left */}
              <div className="text-center p-4 bg-zinc-800/50 rounded-lg">
                <p className="text-xs text-zinc-500 mb-1">RL</p>
                <p className={`text-2xl font-bold ${getTempColor(telemetry.temp_rl)}`}>
                  {telemetry.temp_rl.toFixed(0)}°
                </p>
              </div>
              
              {/* Rear Right */}
              <div className="text-center p-4 bg-zinc-800/50 rounded-lg">
                <p className="text-xs text-zinc-500 mb-1">RR</p>
                <p className={`text-2xl font-bold ${getTempColor(telemetry.temp_rr)}`}>
                  {telemetry.temp_rr.toFixed(0)}°
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Speed trace */}
      {history.length > 10 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Speed Trace</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history.slice(-50)}>
                  <XAxis dataKey="position" hide />
                  <YAxis domain={['auto', 'auto']} hide />
                  <Line
                    type="monotone"
                    dataKey="speed_kmh"
                    stroke="#22c55e"
                    dot={false}
                    strokeWidth={2}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* G-Forces */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">G-Forces</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center">
            <div className="relative w-48 h-48">
              {/* Background circles */}
              <div className="absolute inset-0 rounded-full border border-zinc-700" />
              <div className="absolute inset-4 rounded-full border border-zinc-800" />
              <div className="absolute inset-8 rounded-full border border-zinc-800" />
              
              {/* Center lines */}
              <div className="absolute left-1/2 top-0 bottom-0 w-px bg-zinc-800" />
              <div className="absolute top-1/2 left-0 right-0 h-px bg-zinc-800" />
              
              {/* G-force dot */}
              <div 
                className="absolute w-4 h-4 bg-red-500 rounded-full transform -translate-x-1/2 -translate-y-1/2 transition-all duration-100"
                style={{
                  left: `calc(50% + ${(telemetry.g_lat / 2) * 50}%)`,
                  top: `calc(50% - ${(telemetry.g_lon / 2) * 50}%)`,
                }}
              />
            </div>
            
            <div className="ml-8 space-y-2">
              <div>
                <span className="text-zinc-400 text-sm">Lateral:</span>
                <span className="ml-2 text-zinc-100">{telemetry.g_lat.toFixed(2)}G</span>
              </div>
              <div>
                <span className="text-zinc-400 text-sm">Longitudinal:</span>
                <span className="ml-2 text-zinc-100">{telemetry.g_lon.toFixed(2)}G</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function getTempColor(temp: number): string {
  if (temp < 70) return 'text-blue-400'
  if (temp < 80) return 'text-green-400'
  if (temp < 90) return 'text-yellow-400'
  if (temp < 100) return 'text-orange-400'
  return 'text-red-400'
}

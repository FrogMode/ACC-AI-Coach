'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { TelemetryCharts } from '@/components/charts/telemetry-charts'
import { LapComparisonChart } from '@/components/charts/lap-comparison-chart'
import { TelemetryFrame } from '@/lib/supabase'
import { Brain, Loader2 } from 'lucide-react'

// Generate demo data
function generateDemoLap(variation: number = 0): TelemetryFrame[] {
  const data: TelemetryFrame[] = []
  
  for (let i = 0; i < 100; i++) {
    const position = i / 100
    const t = position * Math.PI * 10
    
    data.push({
      position,
      speed_kmh: 180 + 80 * Math.sin(t) + variation * 5 + Math.random() * 5,
      throttle: Math.max(0, Math.min(1, 0.5 + 0.5 * Math.cos(t + 0.5 + variation * 0.1))),
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

export default function AnalysisPage() {
  const [lap1Data] = useState<TelemetryFrame[]>(generateDemoLap(0))
  const [lap2Data] = useState<TelemetryFrame[]>(generateDemoLap(2))
  const [coachingFeedback, setCoachingFeedback] = useState<string | null>(null)
  const [isLoadingCoaching, setIsLoadingCoaching] = useState(false)

  const handleGetCoaching = async () => {
    setIsLoadingCoaching(true)
    
    try {
      const response = await fetch('/api/coach', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: `Analyze this lap comparison:
          
Average speed: 195 km/h
Max speed: 278 km/h
Smoothness score: 78/100

Corner analysis:
- T1: Lost 0.15s (braking too early)
- Lesmo 1: Lost 0.08s (apex speed too low)
- Parabolica: Gained 0.12s (good exit)

Overall delta: +0.35s slower than reference

Provide specific tips to improve.`,
          trackName: 'Monza',
          carName: 'Porsche 911 GT3 R',
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setCoachingFeedback(data.feedback)
      } else {
        setCoachingFeedback('Unable to get coaching feedback. Please check your API configuration.')
      }
    } catch (error) {
      console.error('Coaching error:', error)
      setCoachingFeedback('Error connecting to coaching service. Make sure ANTHROPIC_API_KEY is configured.')
    } finally {
      setIsLoadingCoaching(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-zinc-100">Analysis</h1>
          <p className="text-zinc-400 mt-1">
            Deep dive into your telemetry data
          </p>
        </div>
      </div>

      {/* Telemetry overview */}
      <Card>
        <CardHeader>
          <CardTitle>Telemetry Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <TelemetryCharts sessionId="demo" telemetryData={lap1Data} />
        </CardContent>
      </Card>

      {/* Lap comparison */}
      <Card>
        <CardHeader>
          <CardTitle>Lap Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <LapComparisonChart
            lap1Data={lap1Data}
            lap2Data={lap2Data}
            lap1Label="Your Lap"
            lap2Label="Best Lap"
          />
        </CardContent>
      </Card>

      {/* AI Coaching */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Brain className="w-5 h-5 mr-2 text-red-500" />
            AI Coaching
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!coachingFeedback ? (
            <div className="text-center py-8">
              <p className="text-zinc-400 mb-4">
                Get personalized coaching feedback based on your telemetry analysis
              </p>
              <Button onClick={handleGetCoaching} disabled={isLoadingCoaching}>
                {isLoadingCoaching ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Brain className="w-4 h-4 mr-2" />
                    Get AI Coaching
                  </>
                )}
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="prose prose-invert max-w-none">
                <div className="p-4 bg-zinc-800/50 rounded-lg whitespace-pre-wrap text-zinc-300">
                  {coachingFeedback}
                </div>
              </div>
              <Button variant="outline" onClick={() => setCoachingFeedback(null)}>
                Get New Analysis
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Performance metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-zinc-400">Smoothness Score</p>
            <p className="text-3xl font-bold text-zinc-100 mt-2">78/100</p>
            <p className="text-sm text-yellow-500 mt-1">Room for improvement</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-zinc-400">Consistency</p>
            <p className="text-3xl font-bold text-zinc-100 mt-2">85/100</p>
            <p className="text-sm text-green-500 mt-1">Good</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-zinc-400">Trail Braking</p>
            <p className="text-3xl font-bold text-zinc-100 mt-2">62/100</p>
            <p className="text-sm text-red-500 mt-1">Needs work</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

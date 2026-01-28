'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { TrackAnimation } from '@/components/track/track-animation'
import { TelemetryFrame } from '@/lib/supabase'
import { getTrackCorners, TRACK_CORNERS } from '@/lib/telemetry'
import { Map } from 'lucide-react'

// Generate demo telemetry data
function generateDemoLap(variation: number = 0): TelemetryFrame[] {
  const data: TelemetryFrame[] = []
  
  for (let i = 0; i < 200; i++) {
    const position = i / 200
    const t = position * Math.PI * 10
    
    data.push({
      position,
      speed_kmh: 180 + 80 * Math.sin(t) + variation * 5 + Math.random() * 5,
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

const TRACK_TIPS: Record<string, string[]> = {
  monza: [
    'T1 (Variante del Rettifilo): Late apex, use all the exit kerb. Trail brake to rotate the car.',
    'Curva Grande: Flat out in GT3 with good setup. Slight lift if unsure.',
    'Lesmo 1 & 2: Patience! Don\'t rush the entry, focus on exit speed for the following straight.',
    'Ascari: One flowing movement through the chicane. Don\'t over-slow.',
    'Parabolica: Early turn-in, progressive throttle, use all the track on exit.',
  ],
  spa: [
    'La Source: Tight hairpin. Focus on exit speed for the run to Eau Rouge.',
    'Eau Rouge/Raidillon: Flat in GT3 with good setup. Commit and trust the car!',
    'Les Combes: Hard braking zone. Trail brake and rotate.',
    'Pouhon: Double apex, carry speed through. One of the best corners in racing.',
    'Bus Stop: Heavy braking. Nail the chicane for good exit onto pit straight.',
  ],
  nurburgring: [
    'T1: Hard braking from high speed. Tight apex.',
    'Mercedes Arena: Flow through, don\'t over-slow.',
    'Ford Kurve: Important corner for lap time. Good exit crucial.',
    'Schumacher S: Rhythm section. Smooth inputs are key.',
    'Coca Cola Kurve: Final corner. Good exit for pit straight.',
  ],
}

export default function TrackGuidePage() {
  const [selectedTrack, setSelectedTrack] = useState('monza')
  const [lap1Data, setLap1Data] = useState<TelemetryFrame[]>([])
  const [lap2Data, setLap2Data] = useState<TelemetryFrame[]>([])

  useEffect(() => {
    // Generate demo data
    setLap1Data(generateDemoLap(0))
    setLap2Data(generateDemoLap(2))
  }, [selectedTrack])

  const corners = getTrackCorners(selectedTrack)
  const tips = TRACK_TIPS[selectedTrack] || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-zinc-100">Track Guide</h1>
          <p className="text-zinc-400 mt-1">
            Animated racing line comparison and corner tips
          </p>
        </div>
      </div>

      {/* Track selector */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Select Track</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {Object.keys(TRACK_CORNERS).map((track) => (
              <Button
                key={track}
                variant={selectedTrack === track ? 'default' : 'outline'}
                onClick={() => setSelectedTrack(track)}
                className="capitalize"
              >
                {track.replace('_', ' ')}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Track animation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Map className="w-5 h-5 mr-2" />
            Racing Line Animation
          </CardTitle>
        </CardHeader>
        <CardContent>
          <TrackAnimation
            lap1Data={lap1Data}
            lap2Data={lap2Data}
            lap1Label="Your Lap"
            lap2Label="Reference"
            trackName={selectedTrack.charAt(0).toUpperCase() + selectedTrack.slice(1)}
          />
          
          <p className="text-sm text-zinc-500 mt-4 text-center">
            Watch how your racing line (red) compares to the reference (green).
            Where the dots separate is where you gain or lose time.
          </p>
        </CardContent>
      </Card>

      {/* Corner analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Corners list */}
        <Card>
          <CardHeader>
            <CardTitle>Corners</CardTitle>
          </CardHeader>
          <CardContent>
            {corners.length > 0 ? (
              <div className="space-y-3">
                {corners.map((corner, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg"
                  >
                    <div>
                      <p className="font-medium text-zinc-100">{corner.name}</p>
                      <p className="text-sm text-zinc-500">
                        Position: {(corner.position * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-zinc-400">Entry</p>
                      <p className="text-lg font-mono text-zinc-100">
                        {(180 + Math.sin(corner.position * 10) * 50).toFixed(0)} km/h
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-zinc-500 text-center py-4">
                No corner data available for this track
              </p>
            )}
          </CardContent>
        </Card>

        {/* Track tips */}
        <Card>
          <CardHeader>
            <CardTitle>Track Tips</CardTitle>
          </CardHeader>
          <CardContent>
            {tips.length > 0 ? (
              <div className="space-y-4">
                {tips.map((tip, i) => (
                  <div key={i} className="flex space-x-3">
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-red-600/20 text-red-500 flex items-center justify-center text-sm font-bold">
                      {i + 1}
                    </div>
                    <p className="text-sm text-zinc-300">{tip}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-zinc-500 text-center py-4">
                No tips available for this track yet
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* General tips */}
      <Card>
        <CardHeader>
          <CardTitle>General Racing Tips</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <h4 className="font-semibold text-zinc-100">Braking</h4>
              <ul className="text-sm text-zinc-400 space-y-1">
                <li>• Brake in a straight line initially</li>
                <li>• Trail brake into the corner</li>
                <li>• Release brake as you add steering</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-zinc-100">Throttle</h4>
              <ul className="text-sm text-zinc-400 space-y-1">
                <li>• Progressive throttle application</li>
                <li>• Unwind steering as you add throttle</li>
                <li>• Full throttle only when straight</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-zinc-100">Racing Line</h4>
              <ul className="text-sm text-zinc-400 space-y-1">
                <li>• Outside-inside-outside</li>
                <li>• Late apex for better exit</li>
                <li>• Use all available track width</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

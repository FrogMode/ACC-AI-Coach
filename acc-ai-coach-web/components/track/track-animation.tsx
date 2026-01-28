'use client'

import { useEffect, useRef, useState } from 'react'
import { TelemetryFrame } from '@/lib/supabase'
import { Button } from '@/components/ui/button'
import { Play, Pause, RotateCcw } from 'lucide-react'

interface TrackAnimationProps {
  lap1Data: TelemetryFrame[]
  lap2Data?: TelemetryFrame[]
  lap1Label?: string
  lap2Label?: string
  trackName?: string
}

// Generate track coordinates from telemetry position
function generateTrackCoordinates(data: TelemetryFrame[]): { x: number; y: number }[] {
  return data.map((frame) => {
    const t = frame.position * Math.PI * 2
    // Create a track-like shape
    const x = Math.cos(t) * 300 + Math.sin(t * 3) * 50
    const y = Math.sin(t) * 200 + Math.cos(t * 2) * 30
    return { x: x + 400, y: y + 250 }
  })
}

export function TrackAnimation({
  lap1Data,
  lap2Data,
  lap1Label = 'Your Lap',
  lap2Label = 'Reference',
  trackName = 'Track',
}: TrackAnimationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const animationRef = useRef<number>()

  const lap1Coords = generateTrackCoordinates(lap1Data)
  const lap2Coords = lap2Data ? generateTrackCoordinates(lap2Data) : null

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Clear canvas
    ctx.fillStyle = '#0a0a0a'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // Draw track outline (faded)
    ctx.strokeStyle = 'rgba(100, 100, 100, 0.3)'
    ctx.lineWidth = 20
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.beginPath()
    lap1Coords.forEach((coord, i) => {
      if (i === 0) {
        ctx.moveTo(coord.x, coord.y)
      } else {
        ctx.lineTo(coord.x, coord.y)
      }
    })
    ctx.closePath()
    ctx.stroke()

    // Draw track center line
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)'
    ctx.lineWidth = 2
    ctx.setLineDash([10, 10])
    ctx.beginPath()
    lap1Coords.forEach((coord, i) => {
      if (i === 0) {
        ctx.moveTo(coord.x, coord.y)
      } else {
        ctx.lineTo(coord.x, coord.y)
      }
    })
    ctx.closePath()
    ctx.stroke()
    ctx.setLineDash([])

    // Calculate current index based on progress
    const currentIndex = Math.floor(progress * (lap1Coords.length - 1))

    // Draw lap 1 progress line
    if (currentIndex > 0) {
      ctx.strokeStyle = '#ef4444'
      ctx.lineWidth = 3
      ctx.beginPath()
      for (let i = 0; i <= currentIndex; i++) {
        if (i === 0) {
          ctx.moveTo(lap1Coords[i].x, lap1Coords[i].y)
        } else {
          ctx.lineTo(lap1Coords[i].x, lap1Coords[i].y)
        }
      }
      ctx.stroke()

      // Draw lap 1 dot
      ctx.fillStyle = '#ef4444'
      ctx.beginPath()
      ctx.arc(lap1Coords[currentIndex].x, lap1Coords[currentIndex].y, 8, 0, Math.PI * 2)
      ctx.fill()
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 2
      ctx.stroke()
    }

    // Draw lap 2 progress line (if exists)
    if (lap2Coords && currentIndex > 0) {
      ctx.strokeStyle = '#22c55e'
      ctx.lineWidth = 3
      ctx.beginPath()
      for (let i = 0; i <= currentIndex; i++) {
        if (i === 0) {
          ctx.moveTo(lap2Coords[i].x, lap2Coords[i].y)
        } else {
          ctx.lineTo(lap2Coords[i].x, lap2Coords[i].y)
        }
      }
      ctx.stroke()

      // Draw lap 2 dot
      ctx.fillStyle = '#22c55e'
      ctx.beginPath()
      ctx.arc(lap2Coords[currentIndex].x, lap2Coords[currentIndex].y, 8, 0, Math.PI * 2)
      ctx.fill()
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 2
      ctx.stroke()
    }

    // Draw legend
    ctx.fillStyle = '#fff'
    ctx.font = '14px sans-serif'
    
    ctx.fillStyle = '#ef4444'
    ctx.fillRect(20, 20, 20, 20)
    ctx.fillStyle = '#fff'
    ctx.fillText(lap1Label, 50, 35)

    if (lap2Coords) {
      ctx.fillStyle = '#22c55e'
      ctx.fillRect(20, 50, 20, 20)
      ctx.fillStyle = '#fff'
      ctx.fillText(lap2Label, 50, 65)
    }

    // Draw track name
    ctx.fillStyle = '#666'
    ctx.font = '12px sans-serif'
    ctx.fillText(trackName, 20, canvas.height - 20)

    // Draw progress
    ctx.fillStyle = '#fff'
    ctx.font = '16px sans-serif'
    ctx.fillText(`${(progress * 100).toFixed(0)}%`, canvas.width - 60, 35)

  }, [progress, lap1Coords, lap2Coords, lap1Label, lap2Label, trackName])

  useEffect(() => {
    if (isPlaying) {
      const animate = () => {
        setProgress(prev => {
          if (prev >= 1) {
            setIsPlaying(false)
            return 1
          }
          return prev + 0.005
        })
        animationRef.current = requestAnimationFrame(animate)
      }
      animationRef.current = requestAnimationFrame(animate)
    } else {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [isPlaying])

  const handleReset = () => {
    setProgress(0)
    setIsPlaying(false)
  }

  return (
    <div className="space-y-4">
      <canvas
        ref={canvasRef}
        width={800}
        height={500}
        className="w-full rounded-lg border border-zinc-800"
      />
      
      {/* Controls */}
      <div className="flex items-center justify-center space-x-4">
        <Button
          variant="outline"
          size="icon"
          onClick={handleReset}
        >
          <RotateCcw className="w-4 h-4" />
        </Button>
        
        <Button
          onClick={() => setIsPlaying(!isPlaying)}
          className="w-32"
        >
          {isPlaying ? (
            <>
              <Pause className="w-4 h-4 mr-2" />
              Pause
            </>
          ) : (
            <>
              <Play className="w-4 h-4 mr-2" />
              Play
            </>
          )}
        </Button>
        
        {/* Progress slider */}
        <input
          type="range"
          min="0"
          max="100"
          value={progress * 100}
          onChange={(e) => setProgress(Number(e.target.value) / 100)}
          className="w-48 accent-red-500"
        />
      </div>
    </div>
  )
}

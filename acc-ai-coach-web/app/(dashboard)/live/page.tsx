'use client'

import { useEffect, useState } from 'react'
import { useSession } from 'next-auth/react'
import { createBrowserSupabaseClient, TelemetryFrame } from '@/lib/supabase'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LiveTelemetryDisplay } from '@/components/dashboard/live-telemetry-display'
import { Gauge, Radio, Wifi, WifiOff } from 'lucide-react'

export default function LivePage() {
  const { data: session } = useSession()
  const [connected, setConnected] = useState(false)
  const [latestTelemetry, setLatestTelemetry] = useState<TelemetryFrame | null>(null)
  const [telemetryHistory, setTelemetryHistory] = useState<TelemetryFrame[]>([])

  useEffect(() => {
    if (!session?.user?.id) return

    const supabase = createBrowserSupabaseClient()

    // Subscribe to live telemetry updates
    const channel = supabase
      .channel('live_telemetry')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'live_telemetry',
          filter: `user_id=eq.${session.user.id}`,
        },
        (payload) => {
          const newData = payload.new as { data: TelemetryFrame }
          if (newData.data) {
            setLatestTelemetry(newData.data)
            setTelemetryHistory(prev => [...prev.slice(-100), newData.data])
            setConnected(true)
          }
        }
      )
      .subscribe()

    // Check for recent telemetry to determine connection status
    const checkConnection = async () => {
      const { data } = await supabase
        .from('live_telemetry')
        .select('*')
        .eq('user_id', session.user.id)
        .order('timestamp', { ascending: false })
        .limit(1)

      if (data && data.length > 0) {
        const lastUpdate = new Date(data[0].timestamp)
        const now = new Date()
        const diffSeconds = (now.getTime() - lastUpdate.getTime()) / 1000
        
        if (diffSeconds < 10) {
          setConnected(true)
          setLatestTelemetry(data[0].data)
        }
      }
    }

    checkConnection()

    // Timeout to mark as disconnected if no updates
    const timeout = setInterval(() => {
      setConnected(prev => {
        if (prev) {
          // Check if we've received data recently
          return prev
        }
        return false
      })
    }, 5000)

    return () => {
      channel.unsubscribe()
      clearInterval(timeout)
    }
  }, [session?.user?.id])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-zinc-100">Live Telemetry</h1>
          <p className="text-zinc-400 mt-1">
            Real-time data from your ACC session
          </p>
        </div>
        
        <div className={`flex items-center space-x-2 px-4 py-2 rounded-full ${
          connected ? 'bg-green-900/30 text-green-500' : 'bg-zinc-800 text-zinc-400'
        }`}>
          {connected ? (
            <>
              <Wifi className="w-5 h-5" />
              <span className="font-medium">Connected</span>
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            </>
          ) : (
            <>
              <WifiOff className="w-5 h-5" />
              <span className="font-medium">Disconnected</span>
            </>
          )}
        </div>
      </div>

      {!connected ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <Radio className="w-16 h-16 mx-auto mb-4 text-zinc-600" />
              <h3 className="text-xl font-semibold text-zinc-100 mb-2">
                Waiting for connection...
              </h3>
              <p className="text-zinc-400 max-w-md mx-auto">
                Start the collector app on your Windows PC while running ACC.
                Live telemetry will appear here automatically.
              </p>
              
              <div className="mt-8 p-4 bg-zinc-800/50 rounded-lg max-w-md mx-auto text-left">
                <h4 className="font-medium text-zinc-100 mb-2">Quick Setup:</h4>
                <ol className="text-sm text-zinc-400 space-y-2">
                  <li>1. Download the collector from Settings</li>
                  <li>2. Run <code className="bg-zinc-700 px-1 rounded">python collector.py</code></li>
                  <li>3. Start ACC and enter a session</li>
                  <li>4. Data will stream here automatically</li>
                </ol>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <LiveTelemetryDisplay 
          telemetry={latestTelemetry} 
          history={telemetryHistory}
        />
      )}
    </div>
  )
}

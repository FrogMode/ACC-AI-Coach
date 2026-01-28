import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { createServerSupabaseClient, formatLapTime, Session, Lap } from '@/lib/supabase'
import { getTrackDisplayName, getCarDisplayName, formatDate } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { ArrowLeft, CheckCircle, XCircle } from 'lucide-react'
import { TelemetryCharts } from '@/components/charts/telemetry-charts'
import { notFound } from 'next/navigation'

async function getSession(sessionId: string, userId: string): Promise<Session | null> {
  const supabase = createServerSupabaseClient()
  
  const { data, error } = await supabase
    .from('sessions')
    .select('*')
    .eq('id', sessionId)
    .eq('user_id', userId)
    .single()

  if (error) {
    console.error('Error fetching session:', error)
    return null
  }

  return data
}

async function getLaps(sessionId: string): Promise<Lap[]> {
  const supabase = createServerSupabaseClient()
  
  const { data, error } = await supabase
    .from('laps')
    .select('*')
    .eq('session_id', sessionId)
    .order('lap_number', { ascending: true })

  if (error) {
    console.error('Error fetching laps:', error)
    return []
  }

  return data || []
}

export default async function SessionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const authSession = await getServerSession(authOptions)
  
  if (!authSession?.user?.id) {
    return null
  }

  const session = await getSession(id, authSession.user.id)
  
  if (!session) {
    notFound()
  }

  const laps = await getLaps(id)
  const validLaps = laps.filter(l => l.is_valid && l.lap_time_ms && l.lap_time_ms > 0)
  const bestLap = validLaps.length > 0 
    ? validLaps.reduce((best, lap) => 
        (lap.lap_time_ms || Infinity) < (best.lap_time_ms || Infinity) ? lap : best
      )
    : null

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link href="/dashboard/sessions">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="w-5 h-5" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-zinc-100">
              {getTrackDisplayName(session.track)}
            </h1>
            <p className="text-zinc-400">
              {getCarDisplayName(session.car)} • {formatDate(session.created_at)}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <Link href={`/dashboard/track-guide?session=${id}`}>
            <Button variant="outline">View Track Guide</Button>
          </Link>
          <Link href={`/dashboard/analysis?session=${id}`}>
            <Button>Analyze Session</Button>
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-zinc-400">Total Laps</p>
            <p className="text-2xl font-bold text-zinc-100">{laps.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-zinc-400">Valid Laps</p>
            <p className="text-2xl font-bold text-green-500">{validLaps.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-zinc-400">Best Lap</p>
            <p className="text-2xl font-bold text-green-500">
              {formatLapTime(bestLap?.lap_time_ms || null)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-zinc-400">Session Type</p>
            <p className="text-2xl font-bold text-zinc-100 capitalize">
              {session.session_type || 'Practice'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Lap times table */}
      <Card>
        <CardHeader>
          <CardTitle>Lap Times</CardTitle>
        </CardHeader>
        <CardContent>
          {laps.length === 0 ? (
            <p className="text-center text-zinc-500 py-8">No laps recorded</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-zinc-800">
                    <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">Lap</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">Time</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">S1</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">S2</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">S3</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">Delta</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-zinc-400">Valid</th>
                  </tr>
                </thead>
                <tbody>
                  {laps.map((lap) => {
                    const delta = bestLap && lap.lap_time_ms && bestLap.lap_time_ms
                      ? lap.lap_time_ms - bestLap.lap_time_ms
                      : null
                    const isBest = bestLap?.id === lap.id

                    return (
                      <tr 
                        key={lap.id} 
                        className={`border-b border-zinc-800/50 ${isBest ? 'bg-green-900/10' : ''}`}
                      >
                        <td className="py-3 px-4 text-zinc-100">{lap.lap_number}</td>
                        <td className={`py-3 px-4 font-mono ${isBest ? 'text-green-500 font-bold' : 'text-zinc-100'}`}>
                          {formatLapTime(lap.lap_time_ms)}
                        </td>
                        <td className="py-3 px-4 font-mono text-zinc-400">
                          {lap.sector1_ms ? `${(lap.sector1_ms / 1000).toFixed(3)}` : '--'}
                        </td>
                        <td className="py-3 px-4 font-mono text-zinc-400">
                          {lap.sector2_ms ? `${(lap.sector2_ms / 1000).toFixed(3)}` : '--'}
                        </td>
                        <td className="py-3 px-4 font-mono text-zinc-400">
                          {lap.sector3_ms ? `${(lap.sector3_ms / 1000).toFixed(3)}` : '--'}
                        </td>
                        <td className={`py-3 px-4 font-mono ${
                          delta === null ? 'text-zinc-500' :
                          delta === 0 ? 'text-green-500' :
                          delta > 0 ? 'text-red-400' : 'text-green-400'
                        }`}>
                          {delta === null ? '--' : 
                           delta === 0 ? '±0.000' :
                           `${delta > 0 ? '+' : ''}${(delta / 1000).toFixed(3)}`}
                        </td>
                        <td className="py-3 px-4">
                          {lap.is_valid ? (
                            <CheckCircle className="w-5 h-5 text-green-500" />
                          ) : (
                            <XCircle className="w-5 h-5 text-red-500" />
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Telemetry charts placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Telemetry</CardTitle>
        </CardHeader>
        <CardContent>
          <TelemetryCharts sessionId={id} />
        </CardContent>
      </Card>
    </div>
  )
}

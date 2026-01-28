import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { createServerSupabaseClient, formatLapTime } from '@/lib/supabase'
import { getTrackDisplayName, getCarDisplayName, formatDate } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import Link from 'next/link'
import { Clock, Flag, Gauge } from 'lucide-react'

async function getSessions(userId: string) {
  const supabase = createServerSupabaseClient()
  
  const { data, error } = await supabase
    .from('sessions')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(50)

  if (error) {
    console.error('Error fetching sessions:', error)
    return []
  }

  return data || []
}

export default async function SessionsPage() {
  const session = await getServerSession(authOptions)
  
  if (!session?.user?.id) {
    return null
  }

  const sessions = await getSessions(session.user.id)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-zinc-100">Sessions</h1>
          <p className="text-zinc-400 mt-1">
            View and analyze your recorded sessions
          </p>
        </div>
      </div>

      {sessions.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-zinc-500">
              <Flag className="w-12 h-12 mx-auto mb-4 text-zinc-600" />
              <p className="text-lg">No sessions recorded yet</p>
              <p className="text-sm mt-2">
                Start the collector app while playing ACC to record your sessions.
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {sessions.map((s) => (
            <Link key={s.id} href={`/dashboard/sessions/${s.id}`}>
              <Card className="hover:border-zinc-700 transition-colors cursor-pointer">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <h3 className="text-lg font-semibold text-zinc-100">
                        {getTrackDisplayName(s.track)}
                      </h3>
                      <p className="text-sm text-zinc-400">
                        {getCarDisplayName(s.car)}
                      </p>
                      <p className="text-xs text-zinc-500">
                        {formatDate(s.created_at)}
                      </p>
                    </div>
                    
                    <div className="flex items-center space-x-8">
                      <div className="text-center">
                        <div className="flex items-center text-zinc-400 mb-1">
                          <Flag className="w-4 h-4 mr-1" />
                          <span className="text-xs">Laps</span>
                        </div>
                        <p className="text-xl font-bold text-zinc-100">
                          {s.total_laps || 0}
                        </p>
                      </div>
                      
                      <div className="text-center">
                        <div className="flex items-center text-zinc-400 mb-1">
                          <Gauge className="w-4 h-4 mr-1" />
                          <span className="text-xs">Best Lap</span>
                        </div>
                        <p className="text-xl font-bold text-green-500">
                          {formatLapTime(s.best_lap_ms)}
                        </p>
                      </div>
                      
                      <div className="text-center">
                        <div className="flex items-center text-zinc-400 mb-1">
                          <Clock className="w-4 h-4 mr-1" />
                          <span className="text-xs">Type</span>
                        </div>
                        <p className="text-sm font-medium text-zinc-300 capitalize">
                          {s.session_type || 'Practice'}
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

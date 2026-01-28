import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { StatsCard } from '@/components/dashboard/stats-card'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Clock, Flag, Gauge, TrendingUp } from 'lucide-react'
import Link from 'next/link'

export default async function DashboardPage() {
  const session = await getServerSession(authOptions)

  return (
    <div className="space-y-6">
      {/* Welcome section */}
      <div>
        <h1 className="text-3xl font-bold text-zinc-100">
          Welcome back, {session?.user?.name?.split(' ')[0] || 'Driver'}
        </h1>
        <p className="text-zinc-400 mt-1">
          Here&apos;s an overview of your racing performance
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Total Sessions"
          value="0"
          subtitle="All time"
          icon={Flag}
        />
        <StatsCard
          title="Total Laps"
          value="0"
          subtitle="Across all tracks"
          icon={TrendingUp}
        />
        <StatsCard
          title="Time Driven"
          value="0h"
          subtitle="This month"
          icon={Clock}
        />
        <StatsCard
          title="Best Lap"
          value="--:--.---"
          subtitle="Personal best"
          icon={Gauge}
        />
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Sessions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-zinc-500">
              <p>No sessions recorded yet.</p>
              <p className="text-sm mt-2">
                Download the collector app to start recording your sessions.
              </p>
              <Link
                href="/dashboard/settings"
                className="inline-block mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
              >
                Get Started
              </Link>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Live Telemetry</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-zinc-500">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-zinc-800 flex items-center justify-center">
                <div className="w-4 h-4 rounded-full bg-zinc-600" />
              </div>
              <p>Not connected</p>
              <p className="text-sm mt-2">
                Start the collector app on your PC to see live data.
              </p>
              <Link
                href="/dashboard/live"
                className="inline-block mt-4 px-4 py-2 border border-zinc-700 text-zinc-300 rounded-md hover:bg-zinc-800 transition-colors"
              >
                View Live Dashboard
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Getting started guide */}
      <Card>
        <CardHeader>
          <CardTitle>Getting Started</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-full bg-red-600/20 text-red-500 flex items-center justify-center font-bold">
                1
              </div>
              <h3 className="font-semibold text-zinc-100">Download Collector</h3>
              <p className="text-sm text-zinc-400">
                Get the lightweight collector app for your Windows PC.
              </p>
            </div>
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-full bg-red-600/20 text-red-500 flex items-center justify-center font-bold">
                2
              </div>
              <h3 className="font-semibold text-zinc-100">Connect & Drive</h3>
              <p className="text-sm text-zinc-400">
                Run the collector while playing ACC. Your data syncs automatically.
              </p>
            </div>
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-full bg-red-600/20 text-red-500 flex items-center justify-center font-bold">
                3
              </div>
              <h3 className="font-semibold text-zinc-100">Analyze & Improve</h3>
              <p className="text-sm text-zinc-400">
                Review your sessions, compare laps, and get AI coaching tips.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

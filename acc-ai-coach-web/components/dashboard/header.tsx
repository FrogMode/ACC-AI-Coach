'use client'

import { useSession } from 'next-auth/react'
import { Bell, User } from 'lucide-react'

export function Header() {
  const { data: session } = useSession()

  return (
    <header className="h-16 border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm">
      <div className="flex items-center justify-between h-full px-6">
        <div>
          {/* Breadcrumb or page title could go here */}
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Live status indicator */}
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-zinc-800">
            <div className="w-2 h-2 rounded-full bg-zinc-500" />
            <span className="text-sm text-zinc-400">Offline</span>
          </div>

          {/* Notifications */}
          <button className="p-2 rounded-md hover:bg-zinc-800 text-zinc-400">
            <Bell size={20} />
          </button>

          {/* User menu */}
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center">
              <User size={16} className="text-zinc-400" />
            </div>
            <div className="hidden sm:block">
              <p className="text-sm font-medium text-zinc-100">
                {session?.user?.name || 'Driver'}
              </p>
              <p className="text-xs text-zinc-500">
                {session?.user?.email}
              </p>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

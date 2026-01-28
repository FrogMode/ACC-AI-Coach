'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { signOut } from 'next-auth/react'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  FolderOpen,
  Radio,
  BarChart3,
  Map,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { useState } from 'react'

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/dashboard/sessions', label: 'Sessions', icon: FolderOpen },
  { href: '/dashboard/live', label: 'Live', icon: Radio },
  { href: '/dashboard/analysis', label: 'Analysis', icon: BarChart3 },
  { href: '/dashboard/track-guide', label: 'Track Guide', icon: Map },
]

export function Sidebar() {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={cn(
        'flex flex-col h-screen bg-zinc-900 border-r border-zinc-800 transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-zinc-800">
        {!collapsed && (
          <Link href="/dashboard" className="flex items-center space-x-2">
            <span className="text-2xl">🏎️</span>
            <span className="font-bold text-lg text-zinc-100">ACC Coach</span>
          </Link>
        )}
        {collapsed && (
          <Link href="/dashboard" className="mx-auto">
            <span className="text-2xl">🏎️</span>
          </Link>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            'p-1 rounded hover:bg-zinc-800 text-zinc-400',
            collapsed && 'mx-auto'
          )}
        >
          {collapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        <ul className="space-y-1 px-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href || 
              (item.href !== '/dashboard' && pathname.startsWith(item.href))
            const Icon = item.icon

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    'flex items-center px-3 py-2 rounded-md transition-colors',
                    isActive
                      ? 'bg-red-600/20 text-red-500'
                      : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100'
                  )}
                >
                  <Icon size={20} />
                  {!collapsed && <span className="ml-3">{item.label}</span>}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Bottom section */}
      <div className="border-t border-zinc-800 p-2">
        <Link
          href="/dashboard/settings"
          className="flex items-center px-3 py-2 rounded-md text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
        >
          <Settings size={20} />
          {!collapsed && <span className="ml-3">Settings</span>}
        </Link>
        <button
          onClick={() => signOut({ callbackUrl: '/' })}
          className="flex items-center w-full px-3 py-2 rounded-md text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
        >
          <LogOut size={20} />
          {!collapsed && <span className="ml-3">Sign out</span>}
        </button>
      </div>
    </aside>
  )
}

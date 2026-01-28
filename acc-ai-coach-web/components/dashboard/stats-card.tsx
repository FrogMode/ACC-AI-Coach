import { cn } from '@/lib/utils'
import { LucideIcon } from 'lucide-react'

interface StatsCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon?: LucideIcon
  trend?: {
    value: number
    label: string
  }
  className?: string
}

export function StatsCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  className,
}: StatsCardProps) {
  return (
    <div
      className={cn(
        'p-6 rounded-lg border border-zinc-800 bg-zinc-900/50',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-zinc-400">{title}</p>
          <p className="mt-2 text-3xl font-bold text-zinc-100">{value}</p>
          {subtitle && (
            <p className="mt-1 text-sm text-zinc-500">{subtitle}</p>
          )}
          {trend && (
            <p
              className={cn(
                'mt-2 text-sm',
                trend.value >= 0 ? 'text-green-500' : 'text-red-500'
              )}
            >
              {trend.value >= 0 ? '+' : ''}
              {trend.value}% {trend.label}
            </p>
          )}
        </div>
        {Icon && (
          <div className="p-3 rounded-lg bg-zinc-800">
            <Icon size={24} className="text-red-500" />
          </div>
        )}
      </div>
    </div>
  )
}

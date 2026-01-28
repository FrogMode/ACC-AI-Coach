import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'ACC AI Coach - Your Personal Racing Engineer',
  description: 'AI-powered telemetry analysis and coaching for Assetto Corsa Competizione. Capture sessions, analyze driving, and improve lap times.',
  keywords: ['ACC', 'Assetto Corsa Competizione', 'telemetry', 'racing', 'coaching', 'AI', 'sim racing'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-zinc-950 text-zinc-100 antialiased`}>
        {children}
      </body>
    </html>
  )
}

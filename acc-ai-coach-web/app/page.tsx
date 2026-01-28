import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { 
  Gauge, 
  BarChart3, 
  Brain, 
  Radio, 
  Map, 
  Download,
  ChevronRight,
  Github
} from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-zinc-950">
      {/* Navigation */}
      <nav className="border-b border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-2">
              <span className="text-2xl">🏎️</span>
              <span className="font-bold text-xl text-zinc-100">ACC AI Coach</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/login">
                <Button variant="ghost">Sign in</Button>
              </Link>
              <Link href="/register">
                <Button>Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <h1 className="text-5xl md:text-7xl font-bold text-zinc-100 mb-6">
              Your Personal
              <span className="text-red-500"> Racing Engineer</span>
            </h1>
            <p className="text-xl text-zinc-400 max-w-2xl mx-auto mb-8">
              AI-powered telemetry analysis for Assetto Corsa Competizione. 
              Capture your sessions, analyze your driving, and get personalized 
              coaching to shave seconds off your lap times.
            </p>
            <div className="flex items-center justify-center space-x-4">
              <Link href="/register">
                <Button size="lg" className="text-lg px-8">
                  Start Free
                  <ChevronRight className="ml-2 w-5 h-5" />
                </Button>
              </Link>
              <Link href="https://github.com/FrogMode/ACC-AI-Coach" target="_blank">
                <Button variant="outline" size="lg" className="text-lg px-8">
                  <Github className="mr-2 w-5 h-5" />
                  View on GitHub
                </Button>
              </Link>
            </div>
          </div>
        </div>
        
        {/* Background gradient */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-gradient-to-b from-red-900/20 to-transparent" />
          <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-red-500/50 to-transparent" />
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-24 border-t border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-zinc-100 mb-4">
              Everything you need to improve
            </h2>
            <p className="text-zinc-400 max-w-xl mx-auto">
              From real-time telemetry capture to AI-powered coaching, 
              we&apos;ve got you covered.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="p-6 rounded-lg border border-zinc-800 bg-zinc-900/50">
              <div className="w-12 h-12 rounded-lg bg-red-600/20 flex items-center justify-center mb-4">
                <Radio className="w-6 h-6 text-red-500" />
              </div>
              <h3 className="text-xl font-semibold text-zinc-100 mb-2">
                Live Telemetry
              </h3>
              <p className="text-zinc-400">
                Stream your telemetry in real-time while you drive. 
                See speed, inputs, tire temps, and more as it happens.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-6 rounded-lg border border-zinc-800 bg-zinc-900/50">
              <div className="w-12 h-12 rounded-lg bg-red-600/20 flex items-center justify-center mb-4">
                <BarChart3 className="w-6 h-6 text-red-500" />
              </div>
              <h3 className="text-xl font-semibold text-zinc-100 mb-2">
                Deep Analysis
              </h3>
              <p className="text-zinc-400">
                Compare laps, analyze corners, and identify exactly 
                where you&apos;re losing time with detailed telemetry charts.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-6 rounded-lg border border-zinc-800 bg-zinc-900/50">
              <div className="w-12 h-12 rounded-lg bg-red-600/20 flex items-center justify-center mb-4">
                <Brain className="w-6 h-6 text-red-500" />
              </div>
              <h3 className="text-xl font-semibold text-zinc-100 mb-2">
                AI Coaching
              </h3>
              <p className="text-zinc-400">
                Get personalized feedback from our AI coach. 
                Natural language tips for every corner and situation.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="p-6 rounded-lg border border-zinc-800 bg-zinc-900/50">
              <div className="w-12 h-12 rounded-lg bg-red-600/20 flex items-center justify-center mb-4">
                <Map className="w-6 h-6 text-red-500" />
              </div>
              <h3 className="text-xl font-semibold text-zinc-100 mb-2">
                Track Guides
              </h3>
              <p className="text-zinc-400">
                Animated racing line comparisons. See exactly where 
                your line differs from the ideal with ghost overlays.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="p-6 rounded-lg border border-zinc-800 bg-zinc-900/50">
              <div className="w-12 h-12 rounded-lg bg-red-600/20 flex items-center justify-center mb-4">
                <Gauge className="w-6 h-6 text-red-500" />
              </div>
              <h3 className="text-xl font-semibold text-zinc-100 mb-2">
                Performance Metrics
              </h3>
              <p className="text-zinc-400">
                Track your smoothness, consistency, and improvement 
                over time with detailed performance scoring.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="p-6 rounded-lg border border-zinc-800 bg-zinc-900/50">
              <div className="w-12 h-12 rounded-lg bg-red-600/20 flex items-center justify-center mb-4">
                <Download className="w-6 h-6 text-red-500" />
              </div>
              <h3 className="text-xl font-semibold text-zinc-100 mb-2">
                Easy Setup
              </h3>
              <p className="text-zinc-400">
                Lightweight collector app runs on your PC. 
                Just start it and drive - data syncs automatically.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 border-t border-zinc-800 bg-zinc-900/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-zinc-100 mb-4">
              How It Works
            </h2>
            <p className="text-zinc-400 max-w-xl mx-auto">
              Get started in minutes with our simple setup process.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-red-600/20 text-red-500 flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                1
              </div>
              <h3 className="text-xl font-semibold text-zinc-100 mb-2">
                Create Account
              </h3>
              <p className="text-zinc-400">
                Sign up for free and get your API key for the collector app.
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-red-600/20 text-red-500 flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                2
              </div>
              <h3 className="text-xl font-semibold text-zinc-100 mb-2">
                Install Collector
              </h3>
              <p className="text-zinc-400">
                Download and run the lightweight Python collector on your gaming PC.
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-red-600/20 text-red-500 flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                3
              </div>
              <h3 className="text-xl font-semibold text-zinc-100 mb-2">
                Drive & Improve
              </h3>
              <p className="text-zinc-400">
                Your telemetry syncs automatically. Analyze and get coaching tips.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 border-t border-zinc-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-bold text-zinc-100 mb-4">
            Ready to get faster?
          </h2>
          <p className="text-xl text-zinc-400 mb-8">
            Join thousands of sim racers improving their lap times with AI-powered coaching.
          </p>
          <Link href="/register">
            <Button size="lg" className="text-lg px-12">
              Get Started Free
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-800 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-xl">🏎️</span>
              <span className="font-semibold text-zinc-400">ACC AI Coach</span>
            </div>
            <div className="flex items-center space-x-6 text-sm text-zinc-500">
              <Link href="https://github.com/FrogMode/ACC-AI-Coach" className="hover:text-zinc-300">
                GitHub
              </Link>
              <span>© 2026 ACC AI Coach</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

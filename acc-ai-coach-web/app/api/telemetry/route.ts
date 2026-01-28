import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { createServerSupabaseClient } from '@/lib/supabase'

// POST /api/telemetry - Stream telemetry data
export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const body = await request.json()
    const { data, session_id } = body

    if (!data) {
      return NextResponse.json({ error: 'Telemetry data is required' }, { status: 400 })
    }

    const supabase = createServerSupabaseClient()

    // Insert live telemetry
    const { error } = await supabase
      .from('live_telemetry')
      .insert({
        user_id: session.user.id,
        data,
      })

    if (error) {
      console.error('Error inserting telemetry:', error)
      return NextResponse.json({ error: 'Failed to save telemetry' }, { status: 500 })
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Telemetry API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

// GET /api/telemetry - Get telemetry for a session/lap
export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const { searchParams } = new URL(request.url)
    const sessionId = searchParams.get('session_id')
    const lapNumber = searchParams.get('lap')

    if (!sessionId) {
      return NextResponse.json({ error: 'Session ID is required' }, { status: 400 })
    }

    const supabase = createServerSupabaseClient()

    // Verify user owns this session
    const { data: sessionData, error: sessionError } = await supabase
      .from('sessions')
      .select('id')
      .eq('id', sessionId)
      .eq('user_id', session.user.id)
      .single()

    if (sessionError || !sessionData) {
      return NextResponse.json({ error: 'Session not found' }, { status: 404 })
    }

    // Get telemetry (this would come from stored files in production)
    // For now, return empty array - telemetry would be stored in Supabase Storage
    return NextResponse.json({ telemetry: [] })
  } catch (error) {
    console.error('Telemetry API error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

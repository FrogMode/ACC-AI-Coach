import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import Anthropic from '@anthropic-ai/sdk'

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
})

export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const body = await request.json()
    const { prompt, trackName, carName } = body

    if (!prompt) {
      return NextResponse.json({ error: 'Prompt is required' }, { status: 400 })
    }

    const systemPrompt = `You are an expert sim racing coach specializing in GT3 racing in Assetto Corsa Competizione. 
You analyze telemetry data and provide clear, actionable feedback to help drivers improve.
Be specific and technical, but explain concepts clearly.
Focus on the most impactful improvements first.
Be encouraging but honest about areas needing work.
Keep responses concise - aim for 2-3 paragraphs maximum.`

    const userPrompt = `${trackName ? `Track: ${trackName}` : ''}
${carName ? `Car: ${carName}` : ''}

${prompt}`

    const message = await anthropic.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 500,
      system: systemPrompt,
      messages: [
        { role: 'user', content: userPrompt },
      ],
    })

    const response = message.content[0].type === 'text' 
      ? message.content[0].text 
      : 'Unable to generate coaching feedback.'

    return NextResponse.json({ feedback: response })
  } catch (error) {
    console.error('Coach API error:', error)
    return NextResponse.json(
      { error: 'Failed to generate coaching feedback' },
      { status: 500 }
    )
  }
}

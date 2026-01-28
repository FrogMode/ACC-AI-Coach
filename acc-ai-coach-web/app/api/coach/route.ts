import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import OpenAI from 'openai'

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
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

    const completion = await openai.chat.completions.create({
      model: 'gpt-4-turbo-preview',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt },
      ],
      temperature: 0.7,
      max_tokens: 500,
    })

    const response = completion.choices[0]?.message?.content || 'Unable to generate coaching feedback.'

    return NextResponse.json({ feedback: response })
  } catch (error) {
    console.error('Coach API error:', error)
    return NextResponse.json(
      { error: 'Failed to generate coaching feedback' },
      { status: 500 }
    )
  }
}

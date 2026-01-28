# ACC AI Coach - Web Application

A Next.js web application for ACC AI Coach with real-time telemetry sync, analysis dashboard, and AI-powered coaching.

## Features

- **User Authentication** - Email/password signup with NextAuth.js + Supabase
- **Live Telemetry** - Real-time data streaming from your PC
- **Session Management** - View and analyze recorded sessions
- **Telemetry Charts** - Speed, inputs, tire temps visualization
- **Lap Comparison** - Compare laps with delta trace
- **Track Animation** - Animated racing line with ghost comparison
- **AI Coaching** - LLM-powered feedback via OpenAI

## Tech Stack

- **Frontend**: Next.js 14 (App Router), React, TypeScript
- **Styling**: Tailwind CSS
- **Auth**: NextAuth.js + Supabase
- **Database**: Supabase (PostgreSQL)
- **Charts**: Recharts
- **Deployment**: Vercel

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Supabase account (free tier)
- OpenAI API key (optional, for AI coaching)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/FrogMode/ACC-AI-Coach-Web.git
   cd acc-ai-coach-web
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env.local
   ```
   
   Edit `.env.local` with your credentials:
   ```
   NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   NEXTAUTH_URL=http://localhost:3000
   NEXTAUTH_SECRET=generate-with-openssl-rand-base64-32
   OPENAI_API_KEY=sk-your-openai-key
   ```

4. **Set up Supabase database**:
   - Create a new Supabase project
   - Run the SQL from `supabase-schema.sql` in the SQL Editor

5. **Run the development server**:
   ```bash
   npm run dev
   ```

6. **Open** http://localhost:3000

## Project Structure

```
acc-ai-coach-web/
├── app/
│   ├── (auth)/           # Login/register pages
│   ├── (dashboard)/      # Dashboard pages
│   ├── api/              # API routes
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Landing page
├── components/
│   ├── ui/               # Reusable UI components
│   ├── charts/           # Telemetry charts
│   ├── track/            # Track animation
│   └── dashboard/        # Dashboard components
├── lib/
│   ├── supabase.ts       # Supabase client
│   ├── auth.ts           # Auth configuration
│   ├── telemetry.ts      # Telemetry processing
│   └── utils.ts          # Utility functions
├── collector/            # Python collector app
└── public/               # Static assets
```

## Deployment

### Deploy to Vercel

1. Push to GitHub
2. Import project in Vercel
3. Add environment variables in Vercel dashboard
4. Deploy!

### Environment Variables for Production

```
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx
NEXTAUTH_URL=https://your-domain.vercel.app
NEXTAUTH_SECRET=xxx
OPENAI_API_KEY=sk-xxx
```

## Collector App

The collector app runs on your Windows PC to stream telemetry from ACC.

See [collector/README.md](collector/README.md) for setup instructions.

## License

Business Source License 1.1 - See LICENSE for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines first.

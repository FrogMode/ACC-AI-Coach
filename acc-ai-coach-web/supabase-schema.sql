-- ACC AI Coach Database Schema
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  track TEXT NOT NULL,
  car TEXT NOT NULL,
  session_type TEXT,
  started_at TIMESTAMP WITH TIME ZONE,
  ended_at TIMESTAMP WITH TIME ZONE,
  best_lap_ms INTEGER,
  total_laps INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Laps table
CREATE TABLE IF NOT EXISTS laps (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  lap_number INTEGER NOT NULL,
  lap_time_ms INTEGER,
  sector1_ms INTEGER,
  sector2_ms INTEGER,
  sector3_ms INTEGER,
  is_valid BOOLEAN DEFAULT true,
  telemetry_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Live telemetry table (for real-time streaming)
CREATE TABLE IF NOT EXISTS live_telemetry (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  data JSONB NOT NULL
);

-- User profiles (extends auth.users)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT UNIQUE,
  display_name TEXT,
  avatar_url TEXT,
  total_laps INTEGER DEFAULT 0,
  total_time_ms BIGINT DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API keys for collector authentication
CREATE TABLE IF NOT EXISTS api_keys (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  key_hash TEXT NOT NULL,
  name TEXT,
  last_used_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_laps_session_id ON laps(session_id);
CREATE INDEX IF NOT EXISTS idx_live_telemetry_user_id ON live_telemetry(user_id);
CREATE INDEX IF NOT EXISTS idx_live_telemetry_timestamp ON live_telemetry(timestamp DESC);

-- Row Level Security (RLS) policies
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE laps ENABLE ROW LEVEL SECURITY;
ALTER TABLE live_telemetry ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- Sessions policies
CREATE POLICY "Users can view their own sessions"
  ON sessions FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own sessions"
  ON sessions FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own sessions"
  ON sessions FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own sessions"
  ON sessions FOR DELETE
  USING (auth.uid() = user_id);

-- Laps policies
CREATE POLICY "Users can view laps from their sessions"
  ON laps FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM sessions 
      WHERE sessions.id = laps.session_id 
      AND sessions.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert laps to their sessions"
  ON laps FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM sessions 
      WHERE sessions.id = laps.session_id 
      AND sessions.user_id = auth.uid()
    )
  );

-- Live telemetry policies
CREATE POLICY "Users can view their own live telemetry"
  ON live_telemetry FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own live telemetry"
  ON live_telemetry FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Profiles policies
CREATE POLICY "Profiles are viewable by everyone"
  ON profiles FOR SELECT
  USING (true);

CREATE POLICY "Users can update their own profile"
  ON profiles FOR UPDATE
  USING (auth.uid() = id);

-- API keys policies
CREATE POLICY "Users can view their own API keys"
  ON api_keys FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own API keys"
  ON api_keys FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own API keys"
  ON api_keys FOR DELETE
  USING (auth.uid() = user_id);

-- Function to auto-create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, username, display_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1))
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile on signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to clean up old live telemetry (keep last 5 minutes)
CREATE OR REPLACE FUNCTION clean_old_telemetry()
RETURNS void AS $$
BEGIN
  DELETE FROM live_telemetry
  WHERE timestamp < NOW() - INTERVAL '5 minutes';
END;
$$ LANGUAGE plpgsql;

-- Enable realtime for live_telemetry
ALTER PUBLICATION supabase_realtime ADD TABLE live_telemetry;

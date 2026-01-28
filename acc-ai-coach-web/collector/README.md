# ACC AI Coach - Telemetry Collector

Lightweight Python script that runs on your Windows PC to stream telemetry from Assetto Corsa Competizione to the cloud.

## Requirements

- Windows 10/11
- Python 3.9+
- ACC installed and running

## Installation

1. **Install Python** (if not already installed):
   - Download from https://python.org
   - Make sure to check "Add Python to PATH" during installation

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Get your API key**:
   - Log in to https://acc-ai-coach.vercel.app
   - Go to Settings
   - Copy your API key

## Usage

1. **Start ACC** and enter a session (practice, race, etc.)

2. **Run the collector**:
   ```bash
   python collector.py --api-key YOUR_API_KEY
   ```

3. **Drive!** Your telemetry will stream to the cloud automatically.

4. **View your data** at https://acc-ai-coach.vercel.app/dashboard

## Options

```
--api-key KEY    Your API key from the web app (required)
--hz NUMBER      Updates per second (default: 20)
--mock           Use mock data for testing without ACC
```

## Testing Without ACC

You can test the collector without ACC running:

```bash
python collector.py --api-key YOUR_API_KEY --mock
```

This will generate simulated telemetry data.

## Troubleshooting

### "Could not connect to ACC"
- Make sure ACC is running
- Make sure you're in a session (not in menus)
- Try restarting ACC

### "Authentication failed"
- Check that your API key is correct
- Make sure you're logged in to the web app

### High CPU usage
- Lower the update rate: `--hz 10`

## How It Works

1. ACC exposes telemetry via Windows shared memory
2. The collector reads this data at the specified rate
3. Data is streamed to Supabase in real-time
4. The web app displays your live telemetry

## Privacy

- Only telemetry data is uploaded (speed, inputs, etc.)
- No personal information is collected
- You can delete your data at any time from the web app

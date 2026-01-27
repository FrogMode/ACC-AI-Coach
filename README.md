# ACC AI Coach 🏎️

An AI-powered coaching system for Assetto Corsa Competizione (ACC). Capture telemetry, analyze your driving, compare against reference laps, and get personalized coaching feedback.

## Features

### Phase 1 (Current) - Telemetry Foundation
- ✅ Real-time telemetry capture from ACC shared memory
- ✅ Session recording to SQLite + Parquet
- ✅ Interactive Streamlit dashboard
- ✅ Speed/throttle/brake/steering visualization
- ✅ Tire temperature monitoring
- ✅ Lap time tracking

### Phase 2 - Analysis Engine
- ✅ Automatic corner detection
- ✅ Lap comparison with delta trace
- ✅ Performance metrics (smoothness, consistency)
- ✅ G-G diagram (friction circle)
- 🚧 Reference lap database

### Phase 3 - AI Coaching
- ✅ LLM integration (OpenAI/Anthropic/Ollama)
- ✅ Natural language coaching feedback
- ✅ Voice synthesis for callouts
- 🚧 Real-time voice coaching

## Quick Start

### Prerequisites
- Python 3.11+
- Windows (for ACC shared memory) or any OS for mock/demo mode
- ACC running in a session (for live telemetry)

### Installation

```bash
# Clone/navigate to the project
cd acc-ai-coach

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
```

### Usage

#### 1. Record a Session

With ACC running and in a session:
```bash
python main.py record
```

Or with mock data for testing:
```bash
python main.py record --mock
```

#### 2. Launch Dashboard

```bash
python main.py dashboard
```

Open http://localhost:8501 in your browser.

#### 3. Run Demo

```bash
python main.py demo
```

This generates mock telemetry and runs through the analysis pipeline.

## Project Structure

```
acc-ai-coach/
├── telemetry/
│   ├── models.py      # ACC data structures
│   ├── collector.py   # Shared memory reader
│   └── recorder.py    # Session recording
├── analysis/
│   ├── segmenter.py   # Corner detection
│   ├── comparator.py  # Lap comparison
│   └── metrics.py     # Performance metrics
├── coach/
│   ├── llm_coach.py   # LLM integration
│   └── voice.py       # Voice synthesis
├── dashboard/
│   └── app.py         # Streamlit dashboard
├── data/
│   ├── sessions/      # Recorded sessions
│   └── references/    # Reference lap database
├── main.py            # CLI entry point
└── requirements.txt
```

## Configuration

### LLM Coach

Set your API key as an environment variable:

```bash
# OpenAI
export OPENAI_API_KEY=sk-...

# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Or use local Ollama (no API key needed)
ollama pull llama2
```

### Voice Coach

The voice coach uses Microsoft Edge TTS by default (free, no API key).

Available voices:
```python
from coach.voice import VoiceCoach
print(VoiceCoach.list_voices())
```

## Data Storage

Sessions are stored in `data/sessions/`:
- `session.db` - SQLite with metadata and lap times
- `telemetry.parquet` - High-frequency telemetry data
- `static.json` - Car and track info

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Tracks

Corner data for tracks is in `analysis/segmenter.py`:

```python
TRACK_CORNERS = {
    "your_track": [
        {"name": "T1 - Corner Name", "position": 0.05},
        # ...
    ],
}
```

## Roadmap

- [ ] Real-time voice coaching during sessions
- [ ] Reference lap download from leaderboards
- [ ] Setup optimization suggestions
- [ ] Multi-lap stint analysis
- [ ] Fuel and tire strategy recommendations
- [ ] Integration with SimHub/CrewChief

## Technical Details

### ACC Shared Memory

ACC exposes telemetry via Windows shared memory:
- `acpmf_physics` - Real-time physics (~60Hz)
- `acpmf_graphics` - Timing and session info
- `acpmf_static` - Car and track info (read once)

### Data Flow

```
ACC Game → Shared Memory → Collector → Recorder → Parquet/SQLite
                                           ↓
                              Dashboard ← Analysis ← Loader
                                           ↓
                                       LLM Coach → Voice
```

## License

This project is licensed under the **Business Source License 1.1** (BSL).

**What this means:**
- **Personal/non-commercial use**: Allowed
- **Education and research**: Allowed  
- **Commercial use**: Requires a separate license - contact the author
- **After 4 years**: Converts to Apache 2.0 (fully open source)

See [LICENSE](LICENSE) for full details.

## Acknowledgments

- Kunos Simulazioni for ACC and its shared memory API
- The sim racing community for telemetry documentation

# Realtime LTX Video Generation Demo

A real-time AI video generation system that creates dynamic content by listening to Twitch chat and streaming live AI-generated videos to RTMP endpoints. Built with LTX Video model, FAL serverless infrastructure, and a modern React dashboard.

## Features

- **Real-time AI Video Generation**: Uses LTX Video model for high-quality video synthesis
- **Twitch Chat Integration**: Listens to chat messages and generates contextual video content
- **Live RTMP Streaming**: Streams generated videos directly to Twitch or other RTMP endpoints
- **Real-time Dashboard**: Monitor generation metrics, queue status, and performance
- **Text Overlays**: Dynamic text overlays on generated videos
- **Serverless Deployment**: Runs on FAL's GPU infrastructure with auto-scaling
- **Continuous Generation**: Seamless video loops with context preservation

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Twitch Chat   │───▶│  Prompt Generator │───▶│  LTX Video Gen  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  RTMP Stream    │◀───│   Text Overlay   │◀───│  Frame Processor │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│     Twitch      │    │    Dashboard     │───▶│   Monitoring    │
│   (Live Stream) │    │   (React App)    │    │   (WebSocket)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Components

- **`streaming_pipeline/`**: Main Python package with all video generation logic
- **`dashboard/`**: Next.js React dashboard for monitoring and control
- **`FAL App`**: Serverless deployment configuration

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- FFmpeg installed
- FAL account and API key
- OpenAI API key
- Twitch account and stream key

### 1. Clone and Setup

```bash
git clone <repository-url>
cd realtime-ltx-video-generation-demo

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -e .
```

### 2. Environment Configuration

Create `.env` in the root directory:

```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here  # Optional, for faster inference

# Twitch Configuration
TWITCH_CHANNEL=shroud  # Channel to monitor (without #)
TWITCH_STREAM_KEY=your_twitch_stream_key_here

# FAL Configuration
FAL_KEY=your_fal_api_key_here
```

### 3. Deploy to FAL

```bash
# Deploy the streaming pipeline
fal deploy realtime-streaming
```

This will output various endpoints. Use the **Synchronous Endpoints** base URL for the dashboard.

### 4. Dashboard Setup

```bash
cd dashboard

# Install dependencies
npm install

# Create dashboard .env.local with the synchronous endpoint base URL
# Example: https://fal.run/alex-w67ic4anktp1/realtime-streaming
echo "NEXT_PUBLIC_FAL_API_URL=https://fal.run/your-username/realtime-streaming" > .env.local

# Start development server
npm run dev
```

## Usage Guide

### Starting a Stream

1. **Deploy to FAL**: `fal deploy realtime-streaming`
2. **Start Dashboard**: `cd dashboard && npm run dev`
3. **Configure Stream**: Use the dashboard to set generation parameters
4. **Start Streaming**: Click "Start Stream" in the dashboard

### API Endpoints

The FAL app exposes these endpoints:

- `POST /start_stream` - Start video generation and streaming
- `POST /stop_stream` - Stop the streaming pipeline
- `GET /metrics` - Get current performance metrics
- `WebSocket /metrics/ws` - Real-time metrics stream

### Request Format

```json
{
  "initial_prompt": "A peaceful digital landscape",
  "initial_image_url": "https://example.com/image.jpg",
  "num_frames": 240,
  "width": 640,
  "height": 480,
  "guidance_scale": 3.0,
  "target_fps": 9.0,
  "mode": "regular"
}
```

## Configuration

### Video Generation Parameters

- **`num_frames`**: Number of frames to generate (default: 240)
- **`width/height`**: Video resolution (default: 640x480)
- **`guidance_scale`**: How closely to follow prompts (default: 3.0)
- **`strength`**: Image-to-video influence (default: 1.0)
- **`target_fps`**: Streaming frame rate (default: 9.0)

### Streaming Configuration

- **`TWITCH_CHANNEL`**: Twitch channel to monitor for chat
- **`TWITCH_STREAM_KEY`**: Your Twitch stream key for RTMP output

### Generation Modes

- **`regular`**: Standard generation with chat influence
- **`nightmare`**: More chaotic, experimental generation

## Project Structure

```
realtime-ltx-video-generation-demo/
├── streaming_pipeline/           # Main Python package
│   ├── app.py                   # FAL app entry point
│   ├── streaming_service.py     # Core streaming logic
│   ├── models.py                # Pydantic models and types
│   ├── core/
│   │   └── streaming_engine.py  # Main generation loop
│   ├── video_generation/
│   │   └── video_generator.py   # LTX model wrapper
│   ├── input/
│   │   └── twitch_listener.py   # Twitch chat integration
│   ├── output/
│   │   └── rtmp_streamer.py     # RTMP streaming via FFmpeg
│   ├── prompt_generation/
│   │   └── prompt_generator.py  # AI prompt generation
│   ├── postprocessing/
│   │   └── text_overlay.py     # Video text overlays
│   ├── utils/
│   │   ├── logger_config.py    # Logging configuration
│   │   └── monitoring.py       # Performance monitoring
│   └── prompts/
│       ├── system_prompt.txt   # Base system prompt
│       └── system_prompt_visual.txt  # Visual mode prompt
├── dashboard/                   # React monitoring dashboard
│   ├── app/                    # Next.js app directory
│   ├── components/             # React components
│   ├── hooks/                  # Custom React hooks
│   └── utils/                  # Utility functions
├── logs/                       # Application logs
├── pyproject.toml             # Python package configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Monitoring & Debugging

### Logs

The system creates separate log files in `logs/`:

- **`server.log`**: API startup, configuration, health checks
- **`generation.log`**: Video generation pipeline events
- **`queue.log`**: RTMP streaming and queue monitoring

### Dashboard Metrics

The React dashboard shows:

- **Generation Performance**: FPS, latency, success rates
- **Queue Status**: Frame buffer levels, processing rates
- **System Health**: Memory usage, error rates
- **Chat Activity**: Recent messages and processing status

### WebSocket Monitoring

Real-time metrics are available via WebSocket at `/metrics/ws`:

```javascript
const ws = new WebSocket('wss://your-fal-url/metrics/ws');
ws.onmessage = (event) => {
  const metrics = JSON.parse(event.data);
  console.log('Current metrics:', metrics);
};
```

## Development

### Local Development

```bash
# Install in development mode
pip install -e .

# Run the streaming pipeline for development
fal run realtime-streaming
```

This will output various endpoints. For development, copy the **Synchronous Endpoints** base URL and update your dashboard's `.env.local`:

```bash
# Update dashboard with the development URL (copy the unique ID from terminal output)
cd dashboard
echo "NEXT_PUBLIC_FAL_API_URL=https://fal.run/unique-id-from-terminal/realtime-streaming" > .env.local
```

**Note**: The URL from `fal run` is temporary and will change each time you run the command. For persistent deployment, use `fal deploy realtime-streaming` instead.

### Adding New Features

1. **Video Effects**: Extend `postprocessing/text_overlay.py`
2. **Chat Sources**: Add new input sources in `input/`
3. **Generation Models**: Extend `video_generation/video_generator.py`
4. **Streaming Outputs**: Add new outputs in `output/`

### Code Structure Guidelines

- **Models**: Define all data structures in `models.py`
- **Logging**: Use the configured loggers from `utils/logger_config.py`
- **Monitoring**: Implement `Monitorable` interface for new components
- **Error Handling**: Use structured logging and graceful degradation

## Troubleshooting

### Common Issues

**Dashboard Can't Connect to FAL App**
- Check that `NEXT_PUBLIC_FAL_API_URL` in `dashboard/.env.local` matches your current FAL app URL
- The FAL URL changes with each deployment - update it after running `fal run realtime-streaming`
- Ensure the FAL app is running before starting the dashboard

**Import Errors**
```bash
# Reinstall in editable mode
pip install -e .
```

**FFmpeg Not Found**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

**RTMP Connection Failed**
- Verify `TWITCH_STREAM_KEY` is correct
- Check firewall settings
- Ensure FFmpeg has network permissions

**Generation Timeouts**
- Reduce `target_fps` for more manageable streaming rates
- Check GPU availability in FAL logs
- Monitor memory usage

### Performance Optimization

- **Reduce Resolution**: Lower `width`/`height` for faster processing
- **Optimize Frame Rate**: Lower `target_fps` to reduce processing load
- **Use Groq**: Add `GROQ_API_KEY` for faster prompt generation
- **Monitor Queues**: Watch dashboard for bottlenecks

## License

This project is licensed under the MIT License - see the LICENSE file for details.



## Acknowledgments

- **LTX Video Model**: Advanced video generation capabilities
- **FAL**: Serverless GPU infrastructure
- **Diffusers**: Hugging Face diffusion models library
- **FFmpeg**: Video processing and streaming




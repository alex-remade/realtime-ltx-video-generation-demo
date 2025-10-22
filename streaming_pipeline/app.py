import fal
from fastapi import WebSocket

from streaming_pipeline.streaming_service import StreamingService
from streaming_pipeline.models import StartStreamRequest
from dotenv import load_dotenv

#load_dotenv()

# Python requirements (FFmpeg is pre-installed in fal base images)
requirements = [
    "torch>=2.1.0",
    "diffusers>=0.28.2",
    "transformers>=4.47.2,<4.52.0",
    "sentencepiece>=0.1.96",
    "huggingface-hub~=0.30",
    "einops",
    "timm",
    "accelerate==1.4.0",
    "opencv-python>=4.9.0.80",
    "imageio[ffmpeg]>=2.25.0",
    "numpy>=1.21.0",
    "ffmpeg-python",
    "python-dotenv",
    "openai",
    "fastapi",
    "uvicorn",
    "pydantic",
    "av",
    "torchvision",
    "fal_client>=0.5.0",  # For ltxv2-preview API calls
    "requests>=2.28.0",   # For downloading generated videos
]

class RealtimeStreamingApp(
    fal.App,
    min_concurrency=0,
    max_concurrency=1,
    max_multiplexing=2,
    keep_alive=1000
):
    machine_type = "GPU-H100"
    requirements=requirements
    

    
    
    def setup(self):
        """Setup with monitoring"""
        print(" Setting up complete streaming pipeline...")
        
        # Initialize the shared streaming service
        self.streaming_service = StreamingService()
        self.streaming_service.setup()
        
        print("✅ Complete streaming pipeline setup complete!")
    
    @fal.endpoint("/start_stream")
    def start_streaming(self, request: StartStreamRequest):
        """Start the complete Twitch streaming pipeline with full LTX configuration"""
        return self.streaming_service.start_streaming(request)
    
    @fal.endpoint("/stop_stream")
    def stop_streaming(self):
        """Stop the streaming pipeline"""
        return self.streaming_service.stop_streaming()
    
    @fal.endpoint("/metrics")
    def get_metrics(self):
        """Get simplified real-time streaming metrics for dashboard"""
        return self.streaming_service.get_metrics()
    
    @fal.endpoint("/metrics/ws", is_websocket=True)
    async def metrics_websocket(self, websocket: WebSocket) -> None:
        """Real-time metrics streaming via WebSocket"""
        await self.streaming_service.handle_metrics_websocket(websocket)
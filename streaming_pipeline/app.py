import fal
from fal.container import ContainerImage
from fastapi import WebSocket

from streaming_service import StreamingService
from models import StartStreamRequest
from dotenv import load_dotenv

load_dotenv()

# Define custom container with FFmpeg
dockerfile_str = """

FROM python:3.11

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Install Python dependencies (quote the version strings)
RUN pip install "torch>=2.1.0" "diffusers>=0.28.2" "transformers>=4.47.2,<4.52.0"
RUN pip install "sentencepiece>=0.1.96" "huggingface-hub~=0.30" einops timm
RUN pip install "accelerate==1.4.0" "opencv-python>=4.9.0.80"
RUN pip install "imageio[ffmpeg]>=2.25.0" "numpy>=1.21.0"
RUN pip install ffmpeg-python python-dotenv openai
RUN pip install fastapi uvicorn pydantic
RUN pip install av torchvision  # Add missing av dependency and torchvision
"""

custom_image = ContainerImage.from_dockerfile_str(dockerfile_str)

class RealtimeStreamingApp(
    fal.App,
    kind="container",
    image=custom_image,
    name='realtime_streaming_app',
    min_concurrency=0,
    max_concurrency=1,
    keep_alive=300
):
    machine_type = "GPU-H100"
    

    
    
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
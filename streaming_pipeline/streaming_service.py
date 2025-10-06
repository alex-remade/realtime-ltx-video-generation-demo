import os
import time
# Removed unused typing imports
from streaming_pipeline.video_generation.video_generator import RealtimeGenerator
from streaming_pipeline.utils.monitoring import ComponentMonitor
from streaming_pipeline.output.rtmp_streamer import FFmpegRTMPStreamer
from streaming_pipeline.core.streaming_engine import RealtimeVideoStreamer
from streaming_pipeline.input.twitch_listener import TwitchChatListener
from streaming_pipeline.prompt_generation.prompt_generator import PromptGenerator
from streaming_pipeline.postprocessing.text_overlay import TextOverlay
#from dotenv import load_dotenv

#load_dotenv()

class StreamingService:
    """Shared streaming service with core logic (no FAL decorators)"""
    
    def __init__(self):
        self.video_generator = None
        self.video_streamer = None
        self.monitor = None
        self._initialized = False
    
    def setup(self):
        """Setup the streaming components"""
        if self._initialized:
            return
            
    
        
        # Initialize the video generator
        self.video_generator = RealtimeGenerator()
        self.video_generator.setup()
        
        # Get environment variables
        twitch_channel = os.getenv("TWITCH_CHANNEL", "shroud")
        openai_key = os.getenv("OPENAI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        stream_key = os.getenv("TWITCH_STREAM_KEY")
        
        if not openai_key:
            raise ValueError("OPENAI_API_KEY environment variable required")
        if not stream_key:
            raise ValueError("TWITCH_STREAM_KEY environment variable required")
        
        # Create all dependencies independently (Dependency Injection pattern)
        self.twitch_listener = TwitchChatListener(twitch_channel)
        self.prompt_generator = PromptGenerator(openai_key, groq_key)
        self.rtmp_streamer = FFmpegRTMPStreamer(
            stream_key=stream_key,
            fps=9,  # 233 frames ÷ 9 FPS = 25.9 seconds (safe buffer)
            width=640,
            height=480
        )
        self.text_overlay = TextOverlay(width=640, height=480)
        
        # Inject all dependencies into video streamer
        self.video_streamer = RealtimeVideoStreamer(
            twitch_listener=self.twitch_listener,
            prompt_generator=self.prompt_generator,
            realtime_generator=self.video_generator,
            rtmp_streamer=self.rtmp_streamer,
            text_overlay=self.text_overlay
        )
        
        # Create generic component monitor
        self.monitor = ComponentMonitor({
            "rtmp": self.rtmp_streamer,
            "video": self.video_streamer,
            "prompt": self.prompt_generator,
            "generator": self.video_generator,
            "overlay": self.text_overlay,
            "twitch": self.twitch_listener
        })
        
        # Start monitoring all components
        self.monitor.start_monitoring()
        
        self._initialized = True
        print("✅ Complete streaming pipeline setup complete!")
    
    def start_streaming(self, request):
        """Start the complete Twitch streaming pipeline with full LTX configuration"""
        if not self._initialized:
            self.setup()
            
        try:

            # Update LTX configuration cleanly using the base model
            ltx_updates = {}
            
            if request.num_frames:
                ltx_updates['num_frames'] = request.num_frames
            if request.timesteps:
                ltx_updates['timesteps'] = request.timesteps
            if request.guidance_scale is not None:
                ltx_updates['guidance_scale'] = request.guidance_scale
            if request.strength is not None:
                ltx_updates['strength'] = request.strength
            if request.negative_prompt:
                ltx_updates['negative_prompt'] = request.negative_prompt
            if request.width:
                ltx_updates['width'] = request.width
            if request.height:
                ltx_updates['height'] = request.height
            
            # Apply all updates at once
            if ltx_updates:
                self.video_streamer.update_ltx_config(**ltx_updates)
            
            # Update streaming configuration (direct access to RTMP streamer)
            if request.target_fps:
                self.rtmp_streamer.fps = request.target_fps
                print(f"   🎛️ Set target_fps: {request.target_fps}")
            
            if request.width and request.height:
                self.rtmp_streamer.width = request.width
                self.rtmp_streamer.height = request.height
                print(f"   🎛️ Set resolution: {request.width}x{request.height}")
            
            # Set custom initial state if provided
            if request.initial_prompt or request.initial_image_url:
                print(f"🎨 Using custom initial state:")
                if request.initial_prompt:
                    print(f"   📝 Custom prompt: {request.initial_prompt}")
                    self.video_streamer.initial_prompt = request.initial_prompt
                if request.initial_image_url:
                    print(f"   🖼️ Custom image: {request.initial_image_url}")
                    self.video_streamer.initial_image_url = request.initial_image_url
            else:
                print(f"�� Using default initial state:")
                print(f"   📝 Default prompt: {self.video_streamer.initial_prompt}")
                print(f"   🖼️ Default image: {self.video_streamer.initial_image_url}")
            
            # Set generation mode in streaming state
            if hasattr(request, 'mode') and request.mode:
                self.video_streamer.state.mode = request.mode
                print(f"   🎭 Mode: {request.mode}")
            else:
                self.video_streamer.state.mode = "regular"
                print(f"   🎭 Mode: regular (default)")
            
            # Restart monitoring if it was stopped
            if self.monitor and not self.monitor.monitoring:
                self.monitor.start_monitoring()
            
            # Start video generation and streaming (RTMP is started internally)
            self.video_streamer.start_streaming()
            
            return {
                "status": "started",
                "message": "Now live on Twitch! AI-generated content streaming with chat reactivity.",
                "twitch_channel_input": self.video_streamer.twitch_listener.channel_name,
                "rtmp_url": self.rtmp_streamer.rtmp_url,
                "initial_prompt": self.video_streamer.initial_prompt,
                "initial_image_url": self.video_streamer.initial_image_url,
                "configuration": {
                    "num_frames": self.video_streamer.ltx_config.num_frames,
                    "timesteps": self.video_streamer.ltx_config.timesteps,
                    "target_fps": self.rtmp_streamer.fps,
                    "resolution": f"{self.video_streamer.ltx_config.width}x{self.video_streamer.ltx_config.height}",
                    "guidance_scale": self.video_streamer.ltx_config.guidance_scale,
                    "strength": self.video_streamer.ltx_config.strength,
                    "negative_prompt": self.video_streamer.ltx_config.negative_prompt
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to start streaming: {e}"
            }
    
    def stop_streaming(self):
        """Stop the streaming pipeline"""
        try:
            print("🛑 Stopping streaming pipeline...")
            print(f"   video_streamer: {self.video_streamer}")
            print(f"   monitor: {self.monitor}")
            
            # Stop components in the right order and return immediately
            # Don't wait for threads to finish to avoid blocking the response
            
            # Keep monitor running to show "stopped" state
            # Monitor will continue showing metrics with is_streaming=False
            
            if self.video_streamer:
                print("   Stopping video streamer (includes internal RTMP)...")
                self.video_streamer.stop_streaming()
            
            result = {
                "status": "stopped",
                "message": "Streaming pipeline stopped successfully"
            }
            print(f"   Stop result: {result}")
            return result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "message": f"Error stopping stream: {e}"
            }
            print(f"   Stop error: {error_result}")
            return error_result
    
    def get_metrics(self):
        """Get latest streaming metrics - clean and simple"""
        try:
            # Get latest metrics if monitor exists and is monitoring
            if self.monitor and self.monitor.monitoring:
                latest_metrics = self.monitor.get_latest_metrics()
                
                if latest_metrics is None:
                    return {"error": "No metrics available yet"}
                
                # Return metrics directly (ComponentMonitor returns dict)
                return latest_metrics
            else:
                # Return minimal state when not monitoring
                return {
                    "error": "Monitoring not active",
                    "timestamp": time.time()
                }
            
        except Exception as e:
            return {
                "error": f"Failed to get metrics: {e}",
                "timestamp": time.time()
            }
    
    async def handle_metrics_websocket(self, websocket, logger=None):
        """Handle WebSocket connection for real-time metrics streaming
        
        This method can be used by both gpu_server.py and FAL app
        """
        import asyncio
        
        await websocket.accept()
        
        try:
            if logger:
                logger.info("📡 WebSocket client connected for metrics streaming")
            else:
                print("📡 WebSocket client connected for metrics streaming")
            
            while True:
                try:
                    # Get current metrics
                    metrics = self.get_metrics()
                    
                    # Send metrics to client
                    await websocket.send_json({
                        "type": "metrics",
                        "data": metrics,
                        "timestamp": time.time()
                    })
                    
                    # Wait 1 second before next update
                    await asyncio.sleep(1.0)
                    
                except Exception as e:
                    if logger:
                        logger.error(f"❌ Error sending metrics: {e}")
                    else:
                        print(f"❌ Error sending metrics: {e}")
                    
                    # Send error message to client
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                        "timestamp": time.time()
                    })
                    await asyncio.sleep(1.0)
                    
        except Exception as e:
            if logger:
                logger.error(f"❌ WebSocket connection error: {e}")
            else:
                print(f"❌ WebSocket connection error: {e}")
        finally:
            if logger:
                logger.info("📡 WebSocket client disconnected")
            else:
                print("📡 WebSocket client disconnected")
            try:
                await websocket.close()
            except:
                pass
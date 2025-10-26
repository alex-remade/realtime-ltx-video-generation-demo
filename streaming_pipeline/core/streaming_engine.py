import asyncio
import base64
from typing import Dict, Any
from io import BytesIO
from PIL import Image
import requests

from streaming_pipeline.utils.logger_config import generation_log


from streaming_pipeline.models import LTXVideoRequestI2V, StreamingState, Monitorable, UserCommentParams



class RealtimeVideoStreamer(Monitorable):

    def __init__(self, 
                 twitch_listener,       
                 prompt_generator,     
                 realtime_generator,  
                 rtmp_streamer,        
                 text_overlay,
                 tts_generator=None,  # Optional TTS generator for narration          
                 comments_lookback: int = 5,
                 initial_prompt: str = None,
                 initial_image_url: str = None):
        
       
        self.twitch_listener = twitch_listener
        self.prompt_generator = prompt_generator
        self.realtime_generator = realtime_generator
        self.rtmp_streamer = rtmp_streamer
        self.text_overlay = text_overlay
        self.tts_generator = tts_generator  # TTS for character voices
        self.comments_lookback = comments_lookback
        

        self.state = StreamingState()
  
        
        # Use provided values or defaults
        self.initial_prompt = initial_prompt
        self.initial_image_url = initial_image_url
        self.next_prompt_ready = None  # Pre-generated prompt
        self.prompt_generation_task = None
        
        # Track generation parameters history (for metrics)
        self.generation_params_history = []
        
        # Track narration history (for monitoring)
        self.narration_history = []
        
        # Current LTX configuration (starts with defaults, updated from start request)
        self.ltx_config = LTXVideoRequestI2V(
            prompt="",  # Will be set per generation
            image_base64=""  # Will be set per generation
        )
        

    

    
    def update_ltx_config(self, **kwargs):
        """Update LTX configuration with new parameters"""
        # Create new config with updated values
        current_dict = self.ltx_config.dict()
        current_dict.update(kwargs)
        self.ltx_config = LTXVideoRequestI2V(**current_dict)
        print(f"Updated LTX config: {', '.join(f'{k}={v}' for k, v in kwargs.items())}")
    
    def start_rtmp_stream(self):
        """Start the injected RTMP stream"""
        if self.rtmp_streamer and not self.rtmp_streamer.is_streaming:
            self.rtmp_streamer.start_stream()
            generation_log.info("✅ RTMP stream started")
    
    def stop_rtmp_stream(self):
        """Stop the injected RTMP stream"""
        if self.rtmp_streamer and self.rtmp_streamer.is_streaming:
            self.rtmp_streamer.stop_stream()
            generation_log.info("✅ RTMP stream stopped")
    
    def _url_to_base64(self, image_url: str) -> str:
        """Convert image URL to base64 (or return as-is if already base64)"""
        try:
            # Check if input is already base64 data URL
            if image_url.startswith('data:image'):
                print("🎯 Input is already base64 data URL, extracting base64 part...")
                # Extract base64 part after the comma
                base64_part = image_url.split(',')[1] if ',' in image_url else image_url
                
                # Validate and resize the base64 image
                try:
                    image_data = base64.b64decode(base64_part)
                    img = Image.open(BytesIO(image_data)).convert("RGB")
                    
                    # Get default dimensions from the Pydantic model
                    temp_request = LTXVideoRequestI2V(prompt="temp", image_base64="temp")
                    width, height = temp_request.width, temp_request.height
                    
                    # Resize to match generation dimensions
                    img = img.resize((width, height))
                    
                    # Re-encode to ensure consistent format
                    buffer = BytesIO()
                    img.save(buffer, format='JPEG', quality=95)
                    buffer.seek(0)
                    
                    return base64.b64encode(buffer.read()).decode('utf-8')
                    
                except Exception as e:
                    print(f"❌ Failed to process base64 image: {e}")
                    raise ValueError(f"Invalid base64 image data: {e}")
            
            # Check if input is raw base64 (without data URL prefix)
            elif self._is_base64_string(image_url):
                print("🎯 Input appears to be raw base64, processing...")
                try:
                    image_data = base64.b64decode(image_url)
                    img = Image.open(BytesIO(image_data)).convert("RGB")
                    
                    # Get default dimensions and resize
                    temp_request = LTXVideoRequestI2V(prompt="temp", image_base64="temp")
                    width, height = temp_request.width, temp_request.height
                    img = img.resize((width, height))
                    
                    # Re-encode
                    buffer = BytesIO()
                    img.save(buffer, format='JPEG', quality=95)
                    buffer.seek(0)
                    
                    return base64.b64encode(buffer.read()).decode('utf-8')
                    
                except Exception as e:
                    print(f"❌ Failed to process raw base64: {e}")
                    # Fall back to treating as URL
            
            # Regular URL - download and convert
            print(f"🌐 Downloading image from URL: {image_url[:100]}...")
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Get default dimensions from the Pydantic model
            temp_request = LTXVideoRequestI2V(prompt="temp", image_base64="temp")
            width, height = temp_request.width, temp_request.height
            
            # Open image and resize to match generation dimensions
            img = Image.open(BytesIO(response.content)).convert("RGB")
            img = img.resize((width, height))
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=95)
            buffer.seek(0)
            
            return base64.b64encode(buffer.read()).decode('utf-8')
            
        except Exception as e:
            raise ValueError(f"Failed to load initial image from {image_url}: {e}")
    
    def _is_base64_string(self, s: str) -> bool:
        """Check if a string is valid base64"""
        try:
            # Basic checks
            if len(s) < 100:  # Too short to be a meaningful image
                return False
            if not s.replace('+', '').replace('/', '').replace('=', '').isalnum():
                return False
            
            # Try to decode
            decoded = base64.b64decode(s, validate=True)
            
            # Check if it starts with common image file signatures
            image_signatures = [
                b'\xff\xd8\xff',  # JPEG
                b'\x89PNG\r\n\x1a\n',  # PNG
                b'GIF87a',  # GIF87a
                b'GIF89a',  # GIF89a
                b'RIFF',  # WEBP (starts with RIFF)
            ]
            
            return any(decoded.startswith(sig) for sig in image_signatures)
            
        except Exception:
            return False
    
    def _frame_to_base64(self, frame: Image.Image) -> str:
        """Convert PIL Image frame to base64"""
        buffer = BytesIO()
        frame.save(buffer, format='JPEG', quality=95)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')
    
    def start_streaming(self):
        """Start the realtime streaming process"""
        if self.state.is_running:
            print("⚠️ Already running")
            return
        
        # Auto-set initial state if not already set
        if not self.state.current_frame_base64:
            print(f"🖼️ Loading initial image from: {self.initial_image_url}")
            initial_image_base64 = self._url_to_base64(self.initial_image_url)
            self.state.current_frame_base64 = initial_image_base64
            self.state.current_prompt = self.initial_prompt
            self.state.previous_prompts = [self.initial_prompt]
        
        generation_log.info(f"🎬 Starting realtime video streaming...")
        generation_log.info(f"📺 Twitch channel: #{self.twitch_listener.channel_name}")
        
        # Start RTMP stream first
        self.start_rtmp_stream()
        
        self.state.is_running = True
        self.twitch_listener.start_listening()
        
        # Start the generation loop in a separate thread
        import threading
        self.generation_thread = threading.Thread(target=self._run_generation_loop)  # Change back to this
        self.generation_thread.daemon = True
        self.generation_thread.start()

    def stop_streaming(self):
        """Stop the realtime streaming process"""
        if not self.state.is_running:
            print("⚠️ Already stopped")
            return
        
        print("🛑 Stopping realtime video streaming...")
        
        # Stop the streaming state
        self.state.is_running = False
        
        # Stop Twitch listener
        if self.twitch_listener:
            self.twitch_listener.stop_listening()
        
        # Stop RTMP stream
        self.stop_rtmp_stream()
        
        # Wait for generation thread to finish (with timeout)
        if hasattr(self, 'generation_thread') and self.generation_thread.is_alive():
            print("⏳ Waiting for generation thread to finish...")
            self.generation_thread.join(timeout=2.0)  # Shorter timeout to avoid blocking
            if self.generation_thread.is_alive():
                print("⚠️ Generation thread did not stop gracefully")
        
        # Clear all context and state for fresh restart
        print("🧹 Clearing context and state...")
        self.state.current_frame_base64 = ""
        self.state.current_prompt = ""
        self.state.generation_count = 0
        self.state.previous_prompts = []
        self.next_prompt_ready = None
        self.prompt_generation_task = None
        
        # Reset metrics on all components
        if hasattr(self.prompt_generator, 'reset_metrics'):
            self.prompt_generator.reset_metrics()
        if hasattr(self.realtime_generator, 'reset_metrics'):
            self.realtime_generator.reset_metrics()
        if hasattr(self.text_overlay, 'reset_metrics'):
            self.text_overlay.reset_metrics()
        # Note: RTMP streamer resets itself in stop_stream()
        
        generation_log.info("✅ Realtime video streaming stopped and context cleared")

    def _run_generation_loop(self):
        """Run the async generation loop in a new event loop"""
        import asyncio
        asyncio.run(self._generation_loop())  # This properly runs the async function
    
    async def _generation_loop(self):
        """Continuous generation loop with no gaps"""
        # Flag to track if this is the first generation
        first_generation = True
        
        while self.state.is_running:
            try:
                # For first generation, don't start prompt generation task
                if not first_generation:
                    # Start prompt generation for NEXT video (in parallel)
                    if not self.prompt_generation_task:
                        self.prompt_generation_task = asyncio.create_task(
                            self._prepare_next_prompt()
                        )
                
                # Generate current video
                await self._generate_next_video(use_initial_prompt=first_generation)
                
                first_generation = False  # After first generation, use normal flow
                
                # No sleep! Immediately continue to next generation
                
            except Exception as e:
                generation_log.error(f"❌ Generation error: {e}")
                generation_log.info(f"🔄 Continuing with next generation attempt...")
                
                # Important: Still mark first_generation as False even if it failed
                # This prevents getting stuck in initial prompt mode
                first_generation = False
                
                # Cancel any pending prompt generation task to start fresh
                if self.prompt_generation_task:
                    self.prompt_generation_task.cancel()
                    self.prompt_generation_task = None
                
                await asyncio.sleep(1)  # Brief pause on error only
    
    async def _prepare_next_prompt(self):
        """Generate the next prompt while current video is generating - WITH VISUAL CONTEXT"""
        # Get recent comments
        comments = self.twitch_listener.get_recent_comments(self.comments_lookback)
        
        # Get available characters from TTS generator if available
        available_characters = {}
        if self.tts_generator:
            available_characters = self.tts_generator.get_available_characters()
        
        # Log LLM input details
        print(f"\n🤖 LLM INPUT for next generation:")
        print(f"   📝 Previous prompts: {len(self.state.previous_prompts)}")
        if self.state.previous_prompts:
            print(f"   📝 Last prompt: {self.state.previous_prompts[-1]}")
        print(f"   🖼️ Visual context: {'✅ Available' if self.state.current_frame_base64 else '❌ None'}")
        print(f"   💬 Recent comments: {len(comments)}")
        for i, comment in enumerate(comments):
            print(f"   💬 [{comment.username}]: {comment.message}")
        print(f"   🎭 Available characters: {len(available_characters)}")
        print(f"   🎤 Recent narrations: {len(self.narration_history)}")
        if self.narration_history:
            last_narration = self.narration_history[-1]
            print(f"   🎤 Last: {last_narration['character']} said \"{last_narration['dialogue']}\"")
        
        # Generate prompt with visual context, narration history, and available characters
        prompt_result = await asyncio.to_thread(
            self.prompt_generator.generate_prompt, 
            comments, 
            self.state,  # Pass unified state instead of separate context
            self.narration_history,  # Pass narration history for context
            available_characters  # Pass available character voices
        )
        
        # Log LLM output details
        print(f"🤖 LLM OUTPUT:")
        if prompt_result.selected_comment:
            print(f"   ✅ Selected comment: [{prompt_result.selected_comment.username}] {prompt_result.selected_comment.message}")
        else:
            print(f"   🌱 Evolution mode (no suitable comments)")
        print(f"   🧠 LLM Reasoning: {prompt_result.reasoning}")
        print(f"   📝 Generated Prompt: {prompt_result.prompt}")
        
        self.next_prompt_ready = prompt_result
        return prompt_result
    
    async def _generate_next_video(self, use_initial_prompt=False):
        """Generate video using pre-prepared prompt or initial prompt for first generation"""
        
        # Track whether a user comment was used for dynamic parameter adjustment
        used_comment = False
        
        if use_initial_prompt:
            # For the FIRST generation, use the initial prompt directly
            generation_log.info(f"🎬 Generation #1 (INITIAL)")
            generation_log.info(f"📝 Using initial prompt: {self.state.current_prompt}")
            
            prompt_to_use = self.state.current_prompt
            selected_comment = None
            used_comment = False  # Initial prompt is not a user comment
            
            # Show initial prompt on overlay
            self.text_overlay.set_prompt(prompt_to_use)
        
        else:
            # For subsequent generations, use the normal prompt generation process
            # Wait for prompt to be ready (should already be done)
            if self.prompt_generation_task:
                prompt_result = await self.prompt_generation_task
                self.prompt_generation_task = None  # Reset for next iteration
            else:
                # Fallback if no pre-generated prompt
                comments = self.twitch_listener.get_recent_comments(self.comments_lookback)
                
                # Get available characters
                available_characters = {}
                if self.tts_generator:
                    available_characters = self.tts_generator.get_available_characters()
                
                # Log fallback LLM input
                print(f"\n🤖 FALLBACK LLM INPUT:")
                print(f"   💬 Recent comments: {len(comments)}")
                for comment in comments:
                    print(f"   💬 [{comment.username}]: {comment.message}")
                print(f"   🎭 Available characters: {len(available_characters)}")
                print(f"   🎤 Recent narrations: {len(self.narration_history)}")
                
                prompt_result = self.prompt_generator.generate_prompt(
                    comments, 
                    self.state,
                    self.narration_history,
                    available_characters
                )
                
                # Log fallback LLM output
                print(f"🤖 FALLBACK LLM OUTPUT:")
                print(f"   🧠 LLM Reasoning: {prompt_result.reasoning}")
                print(f"   📝 Generated Prompt: {prompt_result.prompt}")
            
            generation_log.info(f"🎬 Generation #{self.state.generation_count + 1}")
            if prompt_result.selected_comment:
                generation_log.info(f"💬 Selected: [{prompt_result.selected_comment.username}] {prompt_result.selected_comment.message}")
            else:
                generation_log.info(f"🌱 Evolution: {prompt_result.reasoning}")
            generation_log.info(f"📝 Prompt: {prompt_result.prompt}")
            
            # Log narration if available
            if prompt_result.character and prompt_result.dialogue:
                generation_log.info(f"🎤 Character: {prompt_result.character}")
                generation_log.info(f"💬 Dialogue: {prompt_result.dialogue}")
            
            prompt_to_use = prompt_result.prompt
            selected_comment = prompt_result.selected_comment
            used_comment = selected_comment is not None  # Track if comment was used
            
            # Set the overlay text (RealtimeVideoStreamer controls presentation)
            if selected_comment:
                # Show the selected comment
                self.text_overlay.set_comment(
                    selected_comment.message,
                    selected_comment.username
                )
            else:
                # Show the AI-generated prompt when no comment is selected
                self.text_overlay.set_prompt(prompt_to_use)
        
        # Generate TTS audio if narration is available (parallel with video generation)
        audio_generation_task = None
        if self.tts_generator and prompt_result.character and prompt_result.dialogue:
            generation_log.info(f"🎤 Starting TTS generation in parallel...")
            audio_generation_task = asyncio.create_task(
                self._generate_narration_audio(
                    prompt_result.dialogue,
                    prompt_result.character
                )
            )
        
        # Generate video (same for both initial and subsequent generations)
        try:
            current_frame_preview = self.state.current_frame_base64[:50] + "..." if self.state.current_frame_base64 else "None"
            print(f"🎬 Using input frame: {current_frame_preview}")
            
            # Create base request from current configuration
            request_dict = self.ltx_config.dict()
            request_dict.update({
                "prompt": prompt_to_use,
                "image_base64": self.state.current_frame_base64
            })
            
            # Apply user comment parameter overrides if using a comment
            if used_comment:
                comment_params = UserCommentParams()
                request_dict.update({
                    "guidance_scale": comment_params.guidance_scale,
                    "strength": comment_params.strength
                })
                print(f"🎯 Using COMMENT mode: guidance={comment_params.guidance_scale}, strength={comment_params.strength}")
            else:
                print(f"🌱 Using EVOLUTION mode: guidance={request_dict['guidance_scale']}, strength={request_dict['strength']}")
            
            request = LTXVideoRequestI2V(**request_dict)
            
            # Log all LTX parameters being used
            print(f"🎛️ LTX Request Parameters:")
            print(f"   📝 prompt: {request.prompt}")
            print(f"   📝 negative_prompt: {request.negative_prompt}")
            print(f"   📏 dimensions: {request.width}x{request.height}")
            print(f"   🎞️ num_frames: {request.num_frames}")
            print(f"   💪 strength: {request.strength}")
            print(f"   🎯 guidance_scale: {request.guidance_scale}")
            print(f"   ⏱️ timesteps: {request.timesteps}")
            
            # Store generation parameters in history (last 10)
            import time
            generation_params = {
                "timestamp": time.time(),
                "generation_id": self.state.generation_count + 1,
                "prompt": request.prompt,
                "negative_prompt": request.negative_prompt,
                "width": request.width,
                "height": request.height,
                "num_frames": request.num_frames,
                "strength": request.strength,
                "guidance_scale": request.guidance_scale,
                "timesteps": request.timesteps
            }
            self.generation_params_history.append(generation_params)
            # Keep only last 10 generations
            self.generation_params_history = self.generation_params_history[-10:]
            
            # Get video result with frames for RTMP streaming
            video_result = await asyncio.to_thread(
                self.realtime_generator.generate_video_from_image, 
                request
            )
            
            # Stream frames to external streamer if available - USE BATCH PROCESSING
            # Check if still running before sending frames
            if not self.state.is_running:
                generation_log.info("🛑 Stopping detected - skipping frame streaming")
                return
                
            if self.rtmp_streamer and video_result.frames:
                generation_log.info(f"📺 PROCESSING {len(video_result.frames)} frames with overlay...")
                
                # Apply text overlay to all frames using batch processing
                overlaid_frames = self.text_overlay.apply_overlay_batch(video_result.frames)
                
                generation_log.info(f"📺 SENDING {len(overlaid_frames)} frames to RTMP streamer...")
                processed_count = self.rtmp_streamer.add_frame_batch(overlaid_frames)
                generation_log.info(f"📺 RTMP processed: {processed_count}/{len(overlaid_frames)} frames")
          
            elif not self.rtmp_streamer:
                generation_log.error("❌ NO FRAME STREAMER SET!")
            elif not video_result.frames:
                generation_log.error("❌ NO FRAMES IN VIDEO RESULT!")
            else:
                generation_log.error("❌ Unknown frame streaming issue")
            
            # Update state with last frame (extract from frames on-demand)
            # Check if still running before updating state
            if not self.state.is_running:
                generation_log.info("🛑 Stopping detected - skipping state update")
                return
                
            # Extract last frame as base64 only when needed
            if video_result.frames:
                last_frame_base64 = self._frame_to_base64(video_result.frames[-1])
            else:
                generation_log.error("❌ No frames in video result for state update")
                return
                
            print(f"🔄 Updating state with new frame from generation #{self.state.generation_count + 1}")
            old_frame_preview = self.state.current_frame_base64[:50] + "..." if self.state.current_frame_base64 else "None"
            new_frame_preview = last_frame_base64[:50] + "..."
            print(f"   Old frame: {old_frame_preview}")
            print(f"   New frame: {new_frame_preview}")
            
            self.state.current_frame_base64 = last_frame_base64
            self.state.current_prompt = prompt_to_use
            self.state.generation_count += 1
            self.state.previous_prompts.append(prompt_to_use)
            
            # Wait for TTS audio if it was generating
            audio_url = None
            if audio_generation_task:
                try:
                    audio_url = await audio_generation_task
                    generation_log.info(f"🎤 TTS audio ready: {audio_url}")
                    
                    # Send audio to RTMP streamer for playback
                    if self.rtmp_streamer and audio_url:
                        generation_log.info(f"🎵 Sending audio to RTMP streamer...")
                        success = self.rtmp_streamer.add_audio(audio_url)
                        if success:
                            generation_log.info(f"🎵 Audio queued for streaming!")
                        else:
                            generation_log.warning(f"🎵 Failed to queue audio for streaming")
                    
                    # Store in narration history
                    import time
                    self.narration_history.append({
                        "timestamp": time.time(),
                        "generation_id": self.state.generation_count,
                        "character": prompt_result.character,
                        "dialogue": prompt_result.dialogue,
                        "audio_url": audio_url
                    })
                    # Keep only last 10
                    self.narration_history = self.narration_history[-10:]
                    
                except Exception as e:
                    generation_log.error(f"🎤 TTS generation failed: {e}")
            
            generation_log.info(f"✅ Generated video #{self.state.generation_count}")
            # No delay - immediately ready for next generation!
            
        except Exception as e:
            generation_log.error(f"❌ Video generation failed: {e}")
            raise
    
    async def _generate_narration_audio(self, dialogue: str, character: str) -> str:
        """Generate TTS audio for character dialogue"""
        try:
            audio_url = await self.tts_generator.generate_speech(
                text=dialogue,
                character_key=character
            )
            return audio_url
        except Exception as e:
            generation_log.error(f"Failed to generate narration: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get video generation orchestration status"""
        return {
            "is_running": self.state.is_running,
            "generation_count": self.state.generation_count,
            "current_prompt": self.state.current_prompt[:50] + "..." if len(self.state.current_prompt) > 50 else self.state.current_prompt,
            "generation_params_history": self.generation_params_history,
            "narration_history": self.narration_history
        }





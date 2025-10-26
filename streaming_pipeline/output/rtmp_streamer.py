import threading
import time
import numpy as np
from queue import Queue, Empty
from PIL import Image
import cv2
import subprocess
import tempfile
import os
import requests
from streaming_pipeline.utils.logger_config import queue_log
from streaming_pipeline.models import Monitorable

class FFmpegRTMPStreamer(Monitorable):
    def __init__(self, stream_key: str, fps: int = 24, width: int = 640, height: int = 480):
        self.stream_key = stream_key
        self.fps = fps
        self.width = width
        self.height = height
        # Fix: Use correct Twitch RTMP path
        self.rtmp_url = f"rtmp://live.twitch.tv/app/{stream_key}"
        
        # Stream state
        self.is_streaming = False
        self.ffmpeg_process = None
        self.stream_thread = None
        self.audio_thread = None
        self.monitor_thread = None
        
        # Frame management - Optimized buffer size
        self.frame_queue = Queue(maxsize=1000)  # ~9 seconds at 16fps
        
        # Audio management
        self.audio_queue = Queue(maxsize=50)  # Queue for audio file paths
        self.audio_pipe_path = None  # Named pipe for audio
        self.current_audio = None
        self.audio_position = 0  # Position in current audio (in samples)
        self.sample_rate = 44100
        self.audio_channels = 2
        
        # Statistics - ADD MISSING VARIABLES
        self.frames_sent = 0
        self.frames_dropped = 0
        self.frames_added_total = 0
        self.frames_added_last_second = 0
        self.frames_dropped_last_second = 0
        self.audio_clips_played = 0
        self.start_time = None

    def start_stream(self):
        """Start FFmpeg RTMP stream to Twitch with dynamic audio support"""
        if self.is_streaming:
            print("⚠️ Stream already running")
            return
        
        try:
            print(f"🔗 Starting FFmpeg RTMP stream to Twitch with audio support...")
            print(f"   Resolution: {self.width}x{self.height}")
            print(f"   FPS: {self.fps}")
            print(f"   RTMP URL: {self.rtmp_url[:50]}...")
            
            # Create named pipe for audio (FIFO)
            import uuid
            self.audio_pipe_path = f"/tmp/audio_pipe_{uuid.uuid4().hex}.fifo"
            if os.path.exists(self.audio_pipe_path):
                os.remove(self.audio_pipe_path)
            os.mkfifo(self.audio_pipe_path)
            queue_log.info(f"🎵 Created audio pipe: {self.audio_pipe_path}")
            
            # Build FFmpeg command manually for more control
            # We need two input streams: video (stdin) and audio (named pipe)
            ffmpeg_cmd = [
                'ffmpeg',
                '-loglevel', 'warning',
                # Video input from stdin
                '-f', 'rawvideo',
                '-pix_fmt', 'rgb24',
                '-s', f'{self.width}x{self.height}',
                '-r', str(self.fps),
                '-i', 'pipe:0',
                # Audio input from named pipe
                '-f', 's16le',
                '-ar', str(self.sample_rate),
                '-ac', str(self.audio_channels),
                '-i', self.audio_pipe_path,
                # Video encoding
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', 'faster',
                '-tune', 'zerolatency',
                '-g', str(self.fps),
                '-maxrate', '1500k',
                '-bufsize', '3000k',
                '-b:v', '1500k',
                # Audio encoding
                '-c:a', 'aac',
                '-b:a', '128k',
                '-ar', '44100',
                '-ac', '2',
                # Output format
                '-f', 'flv',
                '-flvflags', 'no_duration_filesize',
                self.rtmp_url
            ]
            
            # Start FFmpeg process
            self.ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=10**8
            )
            
            self.is_streaming = True
            self.start_time = time.time()
            
            # Start the video streaming loop
            queue_log.info("📺 Starting continuous frame streaming loop...")
            self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
            self.stream_thread.start()
            
            # Start the audio streaming loop
            queue_log.info("🎵 Starting audio streaming loop...")
            self.audio_thread = threading.Thread(target=self._audio_loop, daemon=True)
            self.audio_thread.start()
            
            queue_log.info(f"✅ FFmpeg RTMP stream started - NOW LIVE ON TWITCH!")
            queue_log.info(f"🔗 RTMP URL: {self.rtmp_url}")
            queue_log.info(f"📐 Resolution: {self.width}x{self.height} @ {self.fps}fps")
            queue_log.info(f"🎵 Audio: {self.sample_rate}Hz stereo")
            
        except Exception as e:
            queue_log.error(f"❌ Failed to start FFmpeg RTMP stream: {e}")
            self.is_streaming = False
            # Cleanup pipe if created
            if self.audio_pipe_path and os.path.exists(self.audio_pipe_path):
                os.remove(self.audio_pipe_path)

    def stop_stream(self):
        """Stop FFmpeg RTMP stream"""
        if not self.is_streaming:
            return
        
        print("🛑 Stopping FFmpeg RTMP stream...")
        self.is_streaming = False
        
        # Wait for threads to finish
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2.0)
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=2.0)
        
        # Close FFmpeg process
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.stdin.close()
                self.ffmpeg_process.wait(timeout=5)
            except:
                self.ffmpeg_process.kill()
            self.ffmpeg_process = None
        
        # Clean up audio pipe
        if self.audio_pipe_path and os.path.exists(self.audio_pipe_path):
            try:
                os.remove(self.audio_pipe_path)
                queue_log.info(f"🧹 Cleaned up audio pipe: {self.audio_pipe_path}")
            except:
                pass
            self.audio_pipe_path = None
        
        # Clear queue and reset metrics when stopped
        self._reset_metrics()
        print("✅ FFmpeg RTMP stream stopped")

    def _reset_metrics(self):
        """Reset all metrics and clear queue when stream stops"""
        # Clear the frame queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except:
                break
        
        # Clear the audio queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except:
                break
        
        # Reset counters
        self.frames_sent = 0
        self.frames_dropped = 0
        self.frames_added_total = 0
        self.frames_added_last_second = 0
        self.frames_dropped_last_second = 0
        self.audio_clips_played = 0
        self.current_audio = None
        self.audio_position = 0
        self.start_time = None
        print("🧹 RTMP metrics and queues cleared")

    

    def add_frame(self, pil_frame):
        """Add PIL Image frame to stream queue"""
        if not self.is_streaming:
            return
        
        try:
            # Convert PIL frame to numpy array for FFmpeg
            frame_array = np.array(pil_frame.convert('RGB'))
            if frame_array.shape[:2] != (self.height, self.width):
                frame_array = cv2.resize(frame_array, (self.width, self.height))
            
            # Add to queue with non-blocking put
            try:
                self.frame_queue.put_nowait(frame_array)
            except:
                # Queue full - drop oldest frame and add new one
                try:
                    self.frame_queue.get_nowait()
                    self.frames_dropped += 1
                    self.frame_queue.put_nowait(frame_array)
                except Empty:
                    pass
            
        except Exception as e:
            print(f"❌ Error processing frame: {e}")

    def add_frame_batch(self, pil_frames):
        """Add multiple frames efficiently using batch processing"""
        if not self.is_streaming:
            queue_log.warning(f"❌ RTMP not streaming - rejecting {len(pil_frames) if pil_frames else 0} frames")
            return 0
            
        if not pil_frames:
            queue_log.warning("❌ No frames provided to add_frame_batch")
            return 0
        
        queue_log.info(f"📺 BATCH START: Processing {len(pil_frames)} frames...")
        queue_log.info(f"📊 Current queue size: {self.frame_queue.qsize()}/{self.frame_queue.maxsize}")
        
        batch_start_time = time.time()
        processed_count = 0
        
        # Simply loop through frames and reuse existing add_frame logic
        for pil_frame in pil_frames:
            try:
                self.add_frame(pil_frame)  # Reuse existing optimized logic
                processed_count += 1
            except Exception as e:
                print(f"❌ Error processing frame in batch: {e}")
                continue
        
        batch_duration = time.time() - batch_start_time
        batch_fps = processed_count / batch_duration if batch_duration > 0 else 0
        
        queue_log.info(f"📺 BATCH COMPLETE: {processed_count}/{len(pil_frames)} frames in {batch_duration:.2f}s ({batch_fps:.1f} fps)")
        queue_log.info(f"📊 Final queue size: {self.frame_queue.qsize()}/{self.frame_queue.maxsize}")
        
        return processed_count

    def add_audio(self, audio_url: str, save_debug_copy: bool = True):
        """
        Add audio URL to queue for streaming
        Downloads and converts audio, then queues it for playback
        
        Args:
            audio_url: URL of the audio file to download
            save_debug_copy: If True, save a copy of the audio file locally for debugging
        """
        if not self.is_streaming:
            queue_log.warning("❌ RTMP not streaming - rejecting audio")
            return False
        
        try:
            queue_log.info(f"🎵 ========== AUDIO PROCESSING START ==========")
            queue_log.info(f"🎵 Audio URL: {audio_url}")
            queue_log.info(f"🎵 Current queue size: {self.audio_queue.qsize()}")
            queue_log.info(f"🎵 Clips played so far: {self.audio_clips_played}")
            
            # Download and convert audio in background thread to avoid blocking
            def download_and_queue():
                try:
                    audio_data = self._download_and_convert_audio(audio_url, save_debug_copy)
                    if audio_data:
                        self.audio_queue.put(audio_data)
                        queue_log.info(f"🎵 ✅ Audio queued successfully ({len(audio_data)} bytes)")
                        queue_log.info(f"🎵 Queue size after adding: {self.audio_queue.qsize()}")
                    else:
                        queue_log.error(f"🎵 ❌ No audio data returned from conversion")
                except Exception as e:
                    queue_log.error(f"🎵 ❌ Failed to process audio: {e}")
                    import traceback
                    queue_log.error(f"🎵 Traceback: {traceback.format_exc()}")
                finally:
                    queue_log.info(f"🎵 ========== AUDIO PROCESSING END ==========")
            
            threading.Thread(target=download_and_queue, daemon=True).start()
            return True
            
        except Exception as e:
            queue_log.error(f"🎵 ❌ Error adding audio: {e}")
            return False
    
    def _download_and_convert_audio(self, audio_url: str, save_debug_copy: bool = True) -> bytes:
        """Download audio from URL and convert to raw PCM format for FFmpeg"""
        try:
            # Import pydub dynamically to avoid serialization issues
            from pydub import AudioSegment
            
            # Download audio file
            queue_log.info(f"🎵 Downloading audio from {audio_url[:80]}...")
            response = requests.get(audio_url, timeout=30)
            response.raise_for_status()
            queue_log.info(f"🎵 Downloaded {len(response.content)} bytes (Status: {response.status_code})")
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_audio:
                tmp_audio.write(response.content)
                tmp_path = tmp_audio.name
            
            queue_log.info(f"🎵 Saved to temporary file: {tmp_path}")
            
            try:
                # Load with pydub and convert to raw PCM
                queue_log.info(f"🎵 Loading audio with pydub...")
                audio = AudioSegment.from_file(tmp_path)
                queue_log.info(f"🎵 Original audio: {len(audio)}ms, {audio.channels} channels, {audio.frame_rate}Hz")
                
                # Convert to stereo 44.1kHz if needed
                audio = audio.set_channels(self.audio_channels)
                audio = audio.set_frame_rate(self.sample_rate)
                queue_log.info(f"🎵 Converted to: {len(audio)}ms, {audio.channels} channels, {audio.frame_rate}Hz")
                
                # Save a debug copy if requested
                if save_debug_copy:
                    debug_dir = "/tmp/tts_audio_debug"
                    os.makedirs(debug_dir, exist_ok=True)
                    import time
                    timestamp = int(time.time())
                    debug_mp3_path = f"{debug_dir}/audio_{timestamp}.mp3"
                    debug_wav_path = f"{debug_dir}/audio_{timestamp}.wav"
                    
                    # Save as MP3 (original format)
                    audio.export(debug_mp3_path, format="mp3")
                    # Save as WAV (uncompressed for verification)
                    audio.export(debug_wav_path, format="wav")
                    
                    queue_log.info(f"🎵 📁 DEBUG COPY SAVED:")
                    queue_log.info(f"🎵    MP3: {debug_mp3_path}")
                    queue_log.info(f"🎵    WAV: {debug_wav_path}")
                
                # Export as raw PCM (16-bit signed little-endian)
                raw_data = audio.raw_data
                
                duration = len(audio) / 1000.0  # Duration in seconds
                queue_log.info(f"🎵 ✅ Audio converted successfully:")
                queue_log.info(f"🎵    Duration: {duration:.2f}s")
                queue_log.info(f"🎵    Raw PCM size: {len(raw_data)} bytes")
                queue_log.info(f"🎵    Expected playback time: {len(raw_data) / (self.sample_rate * self.audio_channels * 2):.2f}s")
                
                return raw_data
                
            finally:
                # Clean up temp file
                os.remove(tmp_path)
                queue_log.info(f"🎵 Cleaned up temporary file: {tmp_path}")
                
        except Exception as e:
            queue_log.error(f"🎵 ❌ Failed to download/convert audio: {e}")
            import traceback
            queue_log.error(f"🎵 Traceback: {traceback.format_exc()}")
            raise
    
    def _audio_loop(self):
        """
        Continuously stream audio to FFmpeg at correct sample rate
        Handles queued audio clips and fills gaps with silence
        """
        queue_log.info("🎵 ========================================")
        queue_log.info("🎵 Audio streaming loop STARTING")
        queue_log.info("🎵 ========================================")
        
        # Calculate bytes per second for timing
        bytes_per_sample = 2  # 16-bit = 2 bytes
        bytes_per_frame = self.audio_channels * bytes_per_sample
        bytes_per_second = self.sample_rate * bytes_per_frame
        
        queue_log.info(f"🎵 Audio config:")
        queue_log.info(f"🎵   Sample rate: {self.sample_rate}Hz")
        queue_log.info(f"🎵   Channels: {self.audio_channels}")
        queue_log.info(f"🎵   Bytes per second: {bytes_per_second}")
        
        # Open the named pipe for writing
        try:
            queue_log.info(f"🎵 Opening audio pipe for writing: {self.audio_pipe_path}")
            audio_pipe = open(self.audio_pipe_path, 'wb', buffering=0)
            queue_log.info(f"🎵 ✅ Audio pipe opened successfully!")
        except Exception as e:
            queue_log.error(f"🎵 ❌ Failed to open audio pipe: {e}")
            import traceback
            queue_log.error(f"🎵 Traceback: {traceback.format_exc()}")
            return
        
        try:
            last_log_time = time.time()
            silence_duration = 0
            chunks_written = 0
            audio_chunks_written = 0
            silence_chunks_written = 0
            
            queue_log.info(f"🎵 Starting main audio loop...")
            
            while self.is_streaming:
                loop_start = time.time()
                
                # Try to get next audio clip from queue
                if self.current_audio is None or self.audio_position >= len(self.current_audio):
                    try:
                        # Try to get new audio clip (non-blocking)
                        self.current_audio = self.audio_queue.get(timeout=0.1)
                        self.audio_position = 0
                        self.audio_clips_played += 1
                        queue_log.info(f"🎵 ▶️ Playing audio clip #{self.audio_clips_played} ({len(self.current_audio)} bytes)")
                        silence_duration = 0
                    except Empty:
                        # No audio available - send silence
                        self.current_audio = None
                        silence_duration += 0.1
                        
                        # Log silence periodically
                        if time.time() - last_log_time > 10:
                            if silence_duration > 0:
                                queue_log.info(f"🎵 🔇 Streaming silence ({silence_duration:.1f}s, no audio in queue)")
                            last_log_time = time.time()
                
                # Determine how much audio to send (100ms chunks)
                chunk_duration = 0.1  # seconds
                chunk_size = int(bytes_per_second * chunk_duration)
                
                if self.current_audio and self.audio_position < len(self.current_audio):
                    # Send real audio
                    end_pos = min(self.audio_position + chunk_size, len(self.current_audio))
                    audio_chunk = self.current_audio[self.audio_position:end_pos]
                    
                    # Pad with silence if chunk is too short
                    if len(audio_chunk) < chunk_size:
                        silence = b'\x00' * (chunk_size - len(audio_chunk))
                        audio_chunk += silence
                    
                    self.audio_position = end_pos
                    audio_chunks_written += 1
                    
                    # Log progress for real audio
                    if audio_chunks_written % 10 == 0:  # Every 1 second
                        progress = (self.audio_position / len(self.current_audio)) * 100
                        queue_log.info(f"🎵 📊 Audio playback: {progress:.1f}% ({self.audio_position}/{len(self.current_audio)} bytes)")
                else:
                    # Send silence
                    audio_chunk = b'\x00' * chunk_size
                    silence_chunks_written += 1
                
                # Write to pipe
                try:
                    audio_pipe.write(audio_chunk)
                    audio_pipe.flush()
                    chunks_written += 1
                    
                    # Periodic stats
                    if chunks_written % 100 == 0:  # Every 10 seconds
                        queue_log.info(f"🎵 Stats: {chunks_written} total chunks, {audio_chunks_written} audio, {silence_chunks_written} silence")
                        
                except (BrokenPipeError, OSError) as e:
                    queue_log.error(f"🎵 ❌ Audio pipe broken: {e}")
                    break
                
                # Maintain timing
                elapsed = time.time() - loop_start
                sleep_time = max(0, chunk_duration - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        finally:
            audio_pipe.close()
            queue_log.info("🎵 ========================================")
            queue_log.info(f"🎵 Audio streaming loop ENDED")
            queue_log.info(f"🎵 Total chunks written: {chunks_written}")
            queue_log.info(f"🎵 Audio chunks: {audio_chunks_written}")
            queue_log.info(f"🎵 Silence chunks: {silence_chunks_written}")
            queue_log.info("🎵 ========================================")

    def _stream_loop(self):
        """Send frames to FFmpeg at consistent FPS - REDUCED LOGGING"""
        frame_duration = 1.0 / self.fps
        last_real_frame = None
        frame_repeat_count = 0
        last_queue_size = 0
        
        queue_log.info("📺 Starting continuous frame streaming loop...")
        queue_log.info(f"📺 Target FPS: {self.fps}, Frame duration: {frame_duration:.3f}s")
        
        loop_count = 0
        while self.is_streaming and self.ffmpeg_process:
            loop_count += 1
            
            # Fix: Check if ffmpeg already exited
            if self.ffmpeg_process.poll() is not None:
                queue_log.error("❌ FFmpeg process ended; stopping stream loop.")
                self.is_streaming = False
                break
                
            # Debug logging every 30 seconds
            if loop_count % (self.fps * 30) == 0:
                queue_log.info(f"🔄 Stream loop alive: {loop_count} iterations, queue: {self.frame_queue.qsize()}")

            loop_start = time.time()
            
            try:
                # Try to get a real frame from the queue
                current_queue_size = self.frame_queue.qsize()
                
              
                
                try:
                    # Use shorter timeout for better responsiveness
                    timeout = 0.1 if current_queue_size == 0 else 0.001
                    frame = self.frame_queue.get(timeout=timeout)
                    last_real_frame = frame
                    frame_repeat_count = 0
                    
                    # Only log significant queue changes
                    if last_queue_size == 0 and current_queue_size > 5:
                        print(f"📺 Queue building up: {current_queue_size} frames")
                        
                except Empty:
                    # Use last frame with subtle variation
                    if last_real_frame is not None:
                        frame = self._create_varied_frame(last_real_frame, frame_repeat_count)
                        frame_repeat_count += 1
                        
                        # Only log queue empty occasionally
                        if frame_repeat_count % (self.fps * 5) == 0:  # Every 5 seconds
                            print(f"⚠️ Queue empty for {frame_repeat_count/self.fps:.1f}s - repeating frames")
                    else:
                        frame = self._create_placeholder_frame(self.frames_sent)
                        if self.frames_sent % (self.fps * 5) == 0:  # Every 5 seconds
                            print(f"⚠️ No frames available - using placeholder")

                last_queue_size = current_queue_size

                # Fix: Check if stdin is still available
                if not self.ffmpeg_process or not self.ffmpeg_process.stdin:
                    print("❌ FFmpeg stdin unavailable.")
                    self.is_streaming = False
                    break

                # Send frame to FFmpeg
                self.ffmpeg_process.stdin.write(frame.tobytes())
                self.ffmpeg_process.stdin.flush()
                self.frames_sent += 1

            except (BrokenPipeError, ValueError) as e:
                print(f"❌ Streaming error (pipe closed): {e}")
                self.is_streaming = False
                break
            except Exception as e:
                print(f"❌ Streaming error: {e}")
                time.sleep(0.1)
                continue
            
            # Maintain precise FPS timing
            elapsed = time.time() - loop_start
            sleep_time = max(0, frame_duration - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                # Only log performance issues occasionally
                if elapsed > frame_duration * 2 and self.frames_sent % (self.fps * 2) == 0:  # Every 2 seconds, only if 2x slower
                    print(f"⚠️ Frame processing slow: {elapsed:.3f}s (target: {frame_duration:.3f}s)")
        
        print("📺 Frame streaming loop ended")

    def _create_placeholder_frame(self, frame_count):
        """Create a black placeholder frame when no content is available"""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Optional: Add subtle visual indicator
        if frame_count % (self.fps * 4) < (self.fps * 2):  # Blink every 4 seconds
            frame[10:20, 10:20] = [30, 30, 30]  # Small dark gray square
        
        return frame

    def _create_varied_frame(self, base_frame, variation_count):
        """Create subtle variation of the last frame to avoid static appearance"""
        # Make a copy to avoid modifying the original
        frame = base_frame.copy()
        
        # Add very subtle brightness variation (±1-2 levels)
        variation = (variation_count % 3) - 1  # -1, 0, or 1
        if variation != 0:
            frame = np.clip(frame.astype(np.int16) + variation, 0, 255).astype(np.uint8)
        
        return frame


    def get_status(self) -> dict:
        """Get current streaming status and performance metrics"""
        return {
            "is_streaming": self.is_streaming,
            "frames_sent": self.frames_sent,
            "frames_dropped": self.frames_dropped,
            "queue_size": self.frame_queue.qsize(),
            "current_fps": round(self.frames_sent / max(1, time.time() - (self.start_time or time.time())), 1),
            "target_fps": self.fps,
            "audio_clips_played": self.audio_clips_played,
            "audio_queue_size": self.audio_queue.qsize()
        }


from fal.toolkit import optimize
from diffusers import LTXConditionPipeline
from PIL import Image
from io import BytesIO
import base64
import os


from streaming_pipeline.models import LTXVideoRequestI2V, LTXVideoResponseWithFrames, Monitorable
from typing import Dict, Any, List

def safe_snapshot_download(
    repo_id: str,
    revision: str,
    **kwargs: Any,
):
    from huggingface_hub import snapshot_download

    try:
        print("Loading local repo...")
        repo_path = snapshot_download(
            repo_id=repo_id,
            revision=revision,
            local_files_only=True,
            **kwargs,
        )
    except:
        print("Failed to load local repo, downloading from Hugging Face Hub...")
        repo_path = snapshot_download(
            repo_id=repo_id,
            revision=revision,
            local_files_only=False,
            **kwargs,
        )
    return repo_path


MODEL_ID = "Lightricks/LTX-Video-0.9.8-13B-distilled"
REVISION = "main"  # pin to a specific tag/commit for stability
WEIGHTS_DIR = "/data/models/ltx-video-0.9.8-13b"  # persistent on fal


# Regular Python class for local use (non-fal.App)
class RealtimeGenerator(Monitorable):
    

    def __init__(self):
        self.pipeline = None
        
        # Performance tracking for video generation
        self.total_videos = 0
        self.total_generation_time = 0.0
        self.last_generation_time = 0.0
        
        # Configure fal client
        fal_key = os.getenv("FAL_KEY")
        if fal_key:
            os.environ["FAL_KEY"] = fal_key


    def setup(self):
        print("✅ Video generator setup complete (HuggingFace pipeline disabled - using fal API)")
        
        # COMMENTED OUT: HuggingFace local pipeline setup
        # Uncomment this if you want to use LTX v1 with local pipeline
        
        # import os
        # import torch

        # os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
        
        # # Enable memory optimizations
        # torch.backends.cuda.matmul.allow_tf32 = True  # Faster matmul
        # torch.backends.cudnn.allow_tf32 = True       # Faster convolutions
        
        # print("🚀 Loading main pipeline (image-to-video only)...")
        # checkpoint_dir = safe_snapshot_download(
        #     repo_id=MODEL_ID,
        #     revision=REVISION,
        #     local_dir=WEIGHTS_DIR,
        #     local_dir_use_symlinks=True,
        # )
        # self.pipeline = LTXConditionPipeline.from_pretrained(
        #     checkpoint_dir, 
        #     torch_dtype=torch.bfloat16,
        #     use_safetensors=True,
        # )
        # self.pipeline.to("cuda")
        

        # # Enable optimizations
        # self.pipeline.vae.enable_tiling()

        # if hasattr(self.pipeline, "transformer"):
        #     self.pipeline.transformer = optimize(self.pipeline.transformer)
        # elif hasattr(self.pipeline, "denoiser"):
        #     self.pipeline.denoiser = optimize(self.pipeline.denoiser)
        # elif hasattr(self.pipeline, "unet"):
        #     self.pipeline.unet = optimize(self.pipeline.unet)
        # elif hasattr(self.pipeline, "vae"):
        #     self.pipeline.vae = optimize(self.pipeline.vae)
        # else:
        #     print("No model to optimize")
        
        # print("✅ Pipeline setup complete!")
    

    def decode_base64_image(self, base64_string: str) -> Image.Image:
        """Decode base64 string to PIL Image"""
        # Remove data URL prefix if present
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',')[1]
        
        image_data = base64.b64decode(base64_string)
        return Image.open(BytesIO(image_data)).convert("RGB")
    
    
    
    def frame_to_base64(self, frame: Image.Image) -> str:
        """Convert PIL Image frame to base64"""
        buffer = BytesIO()
        frame.save(buffer, format='JPEG', quality=95)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')
    
    def download_video_frames(self, video_url: str, target_width: int = None, target_height: int = None) -> List[Image.Image]:
        """Download video from URL and extract frames
        
        Args:
            video_url: URL of the video to download
            target_width: If set, resize frames to this width
            target_height: If set, resize frames to this height
        """
        import requests
        import tempfile
        import cv2
        
        print(f"📥 Downloading video from: {video_url}")
        
        # Download video to temp file
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            tmp_path = tmp_file.name
        
        try:
            # Extract frames using OpenCV
            frames = []
            cap = cv2.VideoCapture(tmp_path)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Convert to PIL Image
                pil_frame = Image.fromarray(frame_rgb)
                
                # Resize if target dimensions are specified
                if target_width and target_height:
                    pil_frame = pil_frame.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                frames.append(pil_frame)
            
            cap.release()
            print(f"✅ Extracted {len(frames)} frames from video")
            if target_width and target_height:
                print(f"📐 Resized frames to {target_width}x{target_height}")
            return frames
            
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
    
    def generate_video_with_fal_api(self, request: LTXVideoRequestI2V) -> LTXVideoResponseWithFrames:
        """Generate video using fal.ai ltxv2-preview API"""
        import time
        import traceback
        import fal_client
        
        print(f"🎬 Starting fal.ai ltxv2-preview generation")
        print(f"   Prompt: {request.prompt}")
        print(f"   Duration: {request.duration}s")
        print(f"   Resolution: {request.resolution}")
        print(f"   Aspect Ratio: {request.aspect_ratio}")
        
        start_time = time.time()
        
        try:
            # Ensure we have a proper image URL or data URI
            image_data = request.image_base64
            if not image_data.startswith('data:image'):
                # Add data URI prefix if it's just base64
                image_data = f"data:image/jpeg;base64,{image_data}"
            
            # Prepare fal API request - match exact API schema
            fal_input = {
                "image_url": image_data,
                "prompt": request.prompt,
            }
            
            # Add optional parameters only if they're set
            if request.duration:
                fal_input["duration"] = int(request.duration)  # Must be int, not string
            if request.resolution:
                fal_input["resolution"] = request.resolution  # String: "720p", "1080p", "1440p"
            if request.aspect_ratio:
                fal_input["aspect_ratio"] = request.aspect_ratio  # String: "9:16", "16:9"
            if request.enable_prompt_expansion is not None:
                fal_input["enable_prompt_expansion"] = request.enable_prompt_expansion  # Boolean
            
            print(f"🚀 Calling fal.ai API...")
            print(f"🔑 FAL_KEY set: {bool(os.getenv('FAL_KEY'))}")
            print(f"📦 Input parameters:")
            print(f"   - prompt: {fal_input['prompt'][:50]}...")
            print(f"   - duration: {fal_input.get('duration', 6)}")
            print(f"   - resolution: {fal_input.get('resolution', '720p')}")
            print(f"   - aspect_ratio: {fal_input.get('aspect_ratio', '16:9')}")
            print(f"   - image_url length: {len(image_data)}")
            
            # Call fal API with subscribe (waits for completion)
            print(f"⏳ Waiting for fal.ai to complete generation...")
            result = fal_client.subscribe(
                "fal-ai/ltxv-2-preview/image-to-video/fast",
                arguments=fal_input,
                with_logs=True,
            )
            
            print(f"✅ fal.ai API completed!")
            print(f"📊 Result keys: {list(result.keys())}")
            
            # Get video URL from result
            video_url = result["video"]["url"]
            print(f"📹 Video URL: {video_url}")
            
            # Download and extract frames, resizing to match target resolution
            # This ensures text overlay and RTMP streaming work correctly
            frames = self.download_video_frames(video_url, request.width, request.height)
            
            # Track generation performance
            self.last_generation_time = time.time() - start_time
            self.total_generation_time += self.last_generation_time
            self.total_videos += 1
            
            print(f"✅ Complete generation in {self.last_generation_time:.2f}s!")
            
            return LTXVideoResponseWithFrames(
                frames=frames
            )
            
        except Exception as e:
            print(f"❌ fal.ai API generation failed: {e}")
            print(f"❌ Exception type: {type(e).__name__}")
            print(f"❌ Traceback:")
            traceback.print_exc()
            raise
    

    
    def generate_video_from_image(self, request: LTXVideoRequestI2V) -> LTXVideoResponseWithFrames:
        """Main entry point - routes to appropriate backend based on model_type"""
        
        # Route to fal API for ltxv2-preview
        if request.model_type == "ltxv2-preview":
            return self.generate_video_with_fal_api(request)
        
        # Otherwise use local HuggingFace pipeline
        return self.generate_video_with_local_pipeline(request)
    
    def generate_video_with_local_pipeline(self, request: LTXVideoRequestI2V) -> LTXVideoResponseWithFrames:
        """Generate video using local HuggingFace LTX pipeline (ltxv1)"""
        import torch
        
        if self.pipeline is None:
            raise RuntimeError("Pipeline not loaded. Make sure setup() was called successfully.")
        
        print(f"🎬 Starting local pipeline generation - {request.num_frames} frames")
        
        # Decode Base64 input image
        print("📷 Decoding input image...")
        input_image = self.decode_base64_image(request.image_base64)
        
        # Resize image to match video dimensions
        print(f"📏 Resizing image to {request.width}x{request.height}")
        input_image = input_image.resize((request.width, request.height))
        
        # Generate video using image parameter
        print("🚀 Calling pipeline for video generation...")

        
        import time
        start_time = time.time()
        
        try:
            video = self.pipeline(
                image=input_image,
                prompt=request.prompt,
                negative_prompt=request.negative_prompt,
                width=request.width,
                height=request.height,
                num_frames=request.num_frames,
                timesteps=request.timesteps,
                strength=request.strength,
                guidance_scale=request.guidance_scale,
                generator=torch.Generator().manual_seed(0),
                output_type="pil",
            ).frames[0]
            
            # Track generation performance
            self.last_generation_time = time.time() - start_time
            self.total_generation_time += self.last_generation_time
            self.total_videos += 1
            
            print(f"✅ Pipeline generation completed in {self.last_generation_time:.2f}s!")
        except Exception as e:
            print(f"❌ Pipeline generation failed: {e}")
            raise
        

        # Return only frames - last frame will be extracted when needed
        return LTXVideoResponseWithFrames(
            frames=video  # All frames for RTMP streaming, last frame extracted on-demand
        )
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.total_videos = 0
        self.total_generation_time = 0.0
        self.last_generation_time = 0.0
        print("🧹 Video generation metrics reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get component status for monitoring - video generation performance!"""
        avg_generation_time = self.total_generation_time / max(1, self.total_videos)
        return {
            "videos_generated": self.total_videos,
            "avg_generation_time": round(avg_generation_time, 2),
            "last_generation_time": round(self.last_generation_time, 2),
            "ready": self.pipeline is not None
        }





        


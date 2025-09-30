from fal.toolkit import optimize
from diffusers import LTXConditionPipeline
from PIL import Image
from io import BytesIO
import base64


from streaming_pipeline.models import LTXVideoRequestI2V, LTXVideoResponseWithFrames, Monitorable
from typing import Dict, Any

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


    def setup(self):
        import os
        import torch

        os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
        
        # Enable memory optimizations
        torch.backends.cuda.matmul.allow_tf32 = True  # Faster matmul
        torch.backends.cudnn.allow_tf32 = True       # Faster convolutions
        
        print("🚀 Loading main pipeline (image-to-video only)...")
        checkpoint_dir = safe_snapshot_download(
            repo_id=MODEL_ID,
            revision=REVISION,
            local_dir=WEIGHTS_DIR,
            local_dir_use_symlinks=True,
        )
        self.pipeline = LTXConditionPipeline.from_pretrained(
            checkpoint_dir, 
            torch_dtype=torch.bfloat16,
            use_safetensors=True,
        )
        self.pipeline.to("cuda")
        

        # Enable optimizations
        self.pipeline.vae.enable_tiling()

        if hasattr(self.pipeline, "transformer"):
            self.pipeline.transformer = optimize(self.pipeline.transformer)
        elif hasattr(self.pipeline, "denoiser"):
            self.pipeline.denoiser = optimize(self.pipeline.denoiser)
        elif hasattr(self.pipeline, "unet"):
            self.pipeline.unet = optimize(self.pipeline.unet)
        elif hasattr(self.pipeline, "vae"):
            self.pipeline.vae = optimize(self.pipeline.vae)
        else:
            print("No model to optimize")
        
        print("✅ Pipeline setup complete!")
    

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
    

    
    def generate_video_from_image(self, request: LTXVideoRequestI2V) -> LTXVideoResponseWithFrames:
        import torch
        
        if self.pipeline is None:
            raise RuntimeError("Pipeline not loaded. Make sure setup() was called successfully.")
        
        print(f"🎬 Starting video generation - {request.num_frames} frames")
        
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





        


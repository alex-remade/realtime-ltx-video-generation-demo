from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class StartStreamRequest(BaseModel):
    # Model Selection
    model: Optional[Literal["ltxv1", "ltxv2-preview"]] = Field(default="ltxv1", description="Which model to use for generation")
    
    # Basic stream configuration
    initial_prompt: Optional[str] = Field(default=None, description="Custom initial prompt for the stream")
    initial_image_url: Optional[str] = Field(default=None, description="Custom initial image URL for the stream")
    
    # LTX Model Parameters (matching LTXVideoRequestI2V)
    negative_prompt: Optional[str] = Field(default="worst quality, inconsistent motion, blurry, jittery, distorted", description="The negative prompt")
    height: Optional[int] = Field(default=480, description="The height of the video")
    width: Optional[int] = Field(default=640, description="The width of the video")
    num_frames: Optional[int] = Field(default=240, description="The number of frames to generate")
    strength: Optional[float] = Field(default=1.0, description="How much to follow the input image")
    guidance_scale: Optional[float] = Field(default=3.0, description="The guidance scale")
    timesteps: Optional[List[float]] = Field(default=[1000, 981, 909, 725, 0.03], description="The timesteps to use")
    
    # LTXv2-specific parameters
    duration: Optional[Literal[6, 8]] = Field(default=None, description="Duration for ltxv2 (6 or 8 seconds)")
    resolution: Optional[Literal["720p", "1080p", "1440p"]] = Field(default=None, description="Resolution for ltxv2")
    aspect_ratio: Optional[Literal["9:16", "16:9"]] = Field(default=None, description="Aspect ratio for ltxv2")
    enable_prompt_expansion: Optional[bool] = Field(default=True, description="Enable prompt expansion for ltxv2")
    
    # Streaming Configuration
    target_fps: Optional[float] = Field(default=9.0, description="Target streaming FPS")
    mode: Optional[str] = Field(default="regular", description="Generation mode: 'regular' or 'nightmare'")

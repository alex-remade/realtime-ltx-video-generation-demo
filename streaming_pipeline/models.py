
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Deque
from collections import deque
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from PIL import Image
from fal.toolkit.file import File

# Parameter overrides for specific generation modes
class UserCommentParams(BaseModel):
    """Parameter overrides when using user comments"""
    guidance_scale: float = Field(default=5.0, description="Higher guidance to follow user comment closely")
    strength: float = Field(default=1.0, description="Lower strength for visual creativity")


@dataclass
class TwitchComment:
    username: str
    message: str
    timestamp: float
    user_id: Optional[str] = None
    badges: Optional[List[str]] = None
    emotes: Optional[Dict] = None


@dataclass
class PromptContext:
    """Maintains context for coherent video generation"""
    current_scene: str
    previous_prompts: Deque[str]
    narrative_direction: str
    visual_elements: List[str]
    last_frame: Optional[Image.Image] = None

@dataclass
class GenerationRequest:
    prompt: str
    context: PromptContext
    source_comments: List[TwitchComment]
    priority: float = 1.0

@dataclass
class StreamFrame:
    frame_base64: str
    timestamp: float
    metadata: Dict[str, Any]

    



class LTXVideoRequestI2V(BaseModel):
    prompt: str = Field(description="The prompt to generate the video")
    image_base64: str = Field(description="Base64 encoded input image")
    negative_prompt: str = Field(default="worst quality, inconsistent motion, blurry, jittery, distorted", description="The negative prompt")
    height: int = Field(default=480, description="The height of the video")
    width: int = Field(default=640, description="The width of the video")
    num_frames: int = Field(default=161, description="The number of frames to generate")
    strength: float = Field(default=1.0, description="How much to follow the input image")
    guidance_scale: float = Field(default=3.0, description="The guidance scale")
    timesteps: list[float] = Field(default=[1000, 993, 987, 981, 975, 909, 725, 0.03], description="The timesteps to use")

class LTXVideoResponseT2V(BaseModel):
    video: File = Field(description="The video url")

class LTXVideoResponseBase64(BaseModel):
    video_base64: str = Field(description="Base64 encoded video data")
    mime_type: str = Field(default="video/mp4", description="MIME type of the video")

class LTXVideoResponseWithLastFrame(BaseModel):
    video_base64: str = Field(description="Base64 encoded video data")
    last_frame_base64: str = Field(description="Base64 encoded last frame")
    mime_type: str = Field(default="video/mp4", description="MIME type of the video")

# Add the shared StartStreamRequest model
class StartStreamRequest(BaseModel):
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
    
    # Streaming Configuration
    target_fps: Optional[float] = Field(default=9.0, description="Target streaming FPS")
    mode: Optional[str] = Field(default="regular", description="Generation mode: 'regular' or 'nightmare'")

@dataclass 
class StreamingState:
    """Unified state for video streaming and generation context"""
    # Runtime state
    is_running: bool = False
    generation_count: int = 0
    
    # Current generation data
    current_frame_base64: str = ""
    current_prompt: str = ""
    
    # Generation mode and context
    mode: str = "regular"
    
    # Generation history and context
    previous_prompts: List[str] = None
    
    def __post_init__(self):
        if self.previous_prompts is None:
            self.previous_prompts = []
    
    @property
    def current_scene(self) -> str:
        """Current scene is just the last prompt, or default if none"""
        return self.previous_prompts[-1] if self.previous_prompts else "peaceful digital landscape"

@dataclass
class GenerationResult:
    video_base64: str
    last_frame_base64: str
    prompt_used: str
    selected_comment: Optional[TwitchComment]
    generation_time: float




class LTXVideoResponseWithFrames(BaseModel):
    frames: Optional[List] = Field(default=None, description="PIL frames (when streaming)")


# Simple monitoring interface
class Monitorable(ABC):
    """Simple interface for components that can be monitored"""
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Return component status for monitoring"""
        ...

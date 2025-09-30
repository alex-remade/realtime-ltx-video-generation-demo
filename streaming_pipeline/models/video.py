from typing import List, Optional
from pydantic import BaseModel, Field
from fal.toolkit.file import File


class LTXVideoRequestI2V(BaseModel):
    prompt: str = Field(description="The prompt to generate the video")
    image_base64: str = Field(description="Base64 encoded input image")
    negative_prompt: str = Field(default="worst quality, inconsistent motion, blurry, jittery, distorted", description="The negative prompt")
    height: int = Field(default=480, description="The height of the video")
    width: int = Field(default=640, description="The width of the video")
    num_frames: int = Field(default=161, description="The number of frames to generate")
    strength: float = Field(default=1.0, description="How much to follow the input image")
    guidance_scale: float = Field(default=3.0, description="The guidance scale")
    timesteps: List[float] = Field(default=[1000, 993, 987, 981, 975, 909, 725, 0.03], description="The timesteps to use")

class LTXVideoResponseBase64(BaseModel):
    video_base64: str = Field(description="Base64 encoded video data")
    mime_type: str = Field(default="video/mp4", description="MIME type of the video")


class LTXVideoResponseWithLastFrame(BaseModel):
    video_base64: str = Field(description="Base64 encoded video data")
    last_frame_base64: str = Field(description="Base64 encoded last frame")
    mime_type: str = Field(default="video/mp4", description="MIME type of the video")


class LTXVideoResponseWithFrames(BaseModel):
    frames: Optional[List] = Field(default=None, description="PIL frames (when streaming)")

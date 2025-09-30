from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Deque
from PIL import Image
from .twitch import TwitchComment


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

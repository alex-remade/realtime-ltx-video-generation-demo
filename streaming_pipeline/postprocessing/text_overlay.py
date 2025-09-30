from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Dict, Any, List
import time
from streaming_pipeline.models import Monitorable


class TextOverlay(Monitorable):
    """
    Handles text overlay rendering for video frames.
    
    Separated from streaming logic for better separation of concerns.
    For docs example - shows how to extract specialized functionality.
    """
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        
        # Current overlay state
        self.current_text = None
        
        # Cached rendering components
        self.cached_font = None
        self._initialize_font()  # Cache font once at startup
        
        # Performance tracking for monitoring
        self.total_frames_processed = 0
        self.total_processing_time = 0.0
        self.last_batch_size = 0
        self.last_batch_time = 0.0
    
    def set_comment(self, comment_text: str, username: str = None):
        """Set comment to overlay on frames"""
        if comment_text:
            self.current_text = f"@{username}: {comment_text}" if username else comment_text
        else:
            self.current_text = None
    
    def set_prompt(self, prompt_text: str):
        """Set AI prompt to overlay on frames"""
        if prompt_text:
            self.current_text = f"AI: {prompt_text}"
        else:
            self.current_text = None
    
    def _initialize_font(self):
        """Initialize and cache font once for performance"""
        if self.cached_font is not None:
            return self.cached_font
        
        font_size = max(24, self.width // 25)
        try:
            self.cached_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
        except:
            try:
                self.cached_font = ImageFont.load_default()
            except:
                self.cached_font = None
        return self.cached_font
    
    def apply_overlay(self, frame: Image.Image) -> Image.Image:
        """Apply text overlay to frame - optimized with cached font"""
        if not self.current_text:
            return frame
        
        # Create copy to avoid modifying original
        overlay_frame = frame.copy()
        draw = ImageDraw.Draw(overlay_frame)
        
        # Use cached font for performance
        font = self.cached_font
        
        # Position at bottom of frame
        text_y = self.height - 60
        text_x = 20
        
        # Draw text with simple black border
        for adj_x in [-1, 0, 1]:
            for adj_y in [-1, 0, 1]:
                if adj_x != 0 or adj_y != 0:
                    draw.text((text_x + adj_x, text_y + adj_y), self.current_text, font=font, fill=(0, 0, 0))
        
        # Draw white text on top
        draw.text((text_x, text_y), self.current_text, font=font, fill=(255, 255, 255))
        
        return overlay_frame
    
    def apply_overlay_batch(self, frames: List[Image.Image]) -> List[Image.Image]:
        """Apply overlay to multiple frames with performance tracking"""
        if not frames:
            return frames
        
        start_time = time.time()
        
        overlaid_frames = []
        for frame in frames:
            overlaid_frame = self.apply_overlay(frame)
            overlaid_frames.append(overlaid_frame)
        
        # Track performance
        self.last_batch_time = time.time() - start_time
        self.last_batch_size = len(frames)
        self.total_frames_processed += len(frames)
        self.total_processing_time += self.last_batch_time
        
        return overlaid_frames
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.total_frames_processed = 0
        self.total_processing_time = 0.0
        self.last_batch_size = 0
        self.last_batch_time = 0.0
        self.current_text = None  # Clear overlay text too
        # Keep cached_font - no need to reload it
        print("🧹 Text overlay metrics reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get text overlay performance metrics"""
        avg_time_per_frame = self.total_processing_time / max(1, self.total_frames_processed)
        # Calculate average time per frame for last batch
        last_avg_time = self.last_batch_time / max(1, self.last_batch_size) if self.last_batch_size > 0 else 0
        
        return {
            "frames_processed": self.total_frames_processed,
            "avg_time_per_frame": round(avg_time_per_frame, 4),
            "last_batch_size": self.last_batch_size,
            "last_batch_time": round(self.last_batch_time, 3),
            "last_batch_avg_per_frame": round(last_avg_time, 4),
            "has_overlay": self.current_text is not None
        }

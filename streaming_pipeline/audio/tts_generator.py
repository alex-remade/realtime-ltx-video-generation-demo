"""
Text-to-Speech Generator for Character Voices

Uses Chatterbox TTS (same as speech-to-text demo) to generate character voices
for video narration.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


from streaming_pipeline.models.base import Monitorable
from streaming_pipeline.utils.logger_config import generation_log


@dataclass
class CharacterVoice:
    """Configuration for a character voice"""
    name: str
    reference_audio_url: str
    exaggeration: float = 0.25
    temperature: float = 0.7
    cfg: float = 0.5
    description: str = ""


# Predefined character voices (similar to speech-to-text demo)
CHARACTER_VOICES = {
    "spongebob": CharacterVoice(
        name="SpongeBob",
        reference_audio_url="https://storage.googleapis.com/remade-v2/tests/Spongebob%20Squarepants%20-%20They're%20Using%20Actors.mp3",
        exaggeration=0.35,
        temperature=0.8,
        cfg=0.6,
        description="Energetic, optimistic, high-pitched fry cook"
    ),
    "squidward": CharacterVoice(
        name="Squidward",
        reference_audio_url="https://storage.googleapis.com/remade-v2/tests/All%20Squidward%20Voice%20Clips%20%20SpongeBob%20SquarePants_%20Battle%20for%20Bikini%20Bottom%20%20(Rodger%20Bumpass).mp3",
        exaggeration=0.30,
        temperature=0.7,
        cfg=0.65,
        description="Sarcastic, monotone, cynical clarinet player"
    ),
    "narrator": CharacterVoice(
        name="Narrator",
        reference_audio_url="https://storage.googleapis.com/falserverless/chatterbox/narrator_voice.mp3",
        exaggeration=0.15,
        temperature=0.5,
        cfg=0.7,
        description="Professional, clear narrator voice"
    ),
    "mysterious": CharacterVoice(
        name="Mysterious",
        reference_audio_url="https://storage.googleapis.com/falserverless/chatterbox/mysterious_voice.mp3",
        exaggeration=0.20,
        temperature=0.6,
        cfg=0.65,
        description="Deep, mysterious storyteller"
    ),
}


class TTSGenerator(Monitorable):
    """
    Text-to-Speech generator for character voices in video narration.
    Uses fal.ai Chatterbox TTS API for voice cloning.
    """
   
    
    def __init__(self, fal_key: str, default_character: str = "spongebob"):
        import os
        self.fal_key = fal_key
        self.default_character = default_character
        self.characters = CHARACTER_VOICES.copy()
        
        # Configure fal client via environment variable (Python client reads from FAL_KEY)
        os.environ["FAL_KEY"] = fal_key
        
        # Performance tracking
        self.total_generations = 0
        self.total_generation_time = 0.0
        self.last_generation_time = 0.0
        self.last_text_length = 0
        
        generation_log.info(f"🎤 TTS Generator initialized with {len(self.characters)} character voices")
    
    def add_character_voice(self, key: str, voice: CharacterVoice):
        """Add a custom character voice"""
        self.characters[key] = voice
        generation_log.info(f"🎤 Added character voice: {voice.name}")
    
    async def generate_speech(
        self, 
        text: str, 
        character_key: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate speech audio from text using character voice.
        
        Args:
            text: The text to convert to speech
            character_key: Key for the character voice to use (defaults to default_character)
            output_path: Optional path to save audio file locally
            
        Returns:
            URL of the generated audio file
        """
        import time
        import httpx
        import fal_client
        start_time = time.time()
        
        # Get character voice configuration
        character_key = character_key or self.default_character
        if character_key not in self.characters:
            generation_log.warning(f"Character '{character_key}' not found, using default")
            character_key = self.default_character
        
        character = self.characters[character_key]
        
        # Track input
        self.last_text_length = len(text)
        
        generation_log.info(f"🎤 TTS: Generating speech for '{character.name}'")
        generation_log.info(f"🎤 TTS: Text length: {len(text)} characters")
        generation_log.info(f"🎤 TTS: Text preview: {text[:100]}...")
        
        try:
            # Call fal.ai Chatterbox TTS API using official client
            def on_queue_update(update):
                """Callback for queue status updates"""
                # Use isinstance to check update type (not .status attribute)
                if isinstance(update, fal_client.Queued):
                    position = getattr(update, 'position', '?')
                    generation_log.info(f"🎤 TTS: In queue, position: {position}")
                elif isinstance(update, fal_client.InProgress):
                    generation_log.info("🎤 TTS: Generation in progress...")
                    # Log any messages if available
                    if hasattr(update, 'logs') and update.logs:
                        for log in update.logs:
                            if isinstance(log, dict) and 'message' in log:
                                generation_log.info(f"🎤 TTS: {log['message']}")
            
            # Submit request and wait for result
            result = await fal_client.subscribe_async(
                "fal-ai/chatterbox/text-to-speech",
                arguments={
                    "text": text,
                    "audio_url": character.reference_audio_url,
                    "exaggeration": character.exaggeration,
                    "temperature": character.temperature,
                    "cfg": character.cfg
                },
                with_logs=True,
                on_queue_update=on_queue_update
            )
            
            # Extract audio URL from result
            audio_url = result["audio"]["url"]
            
            # Track timing
            self.last_generation_time = time.time() - start_time
            self.total_generation_time += self.last_generation_time
            self.total_generations += 1
            
            generation_log.info(f"🎤 TTS: ✅ Speech generated in {self.last_generation_time:.2f}s")
            generation_log.info(f"🎤 TTS: Audio URL: {audio_url}")
            
            # Optionally download to local file
            if output_path:
                async with httpx.AsyncClient() as client:
                    download_response = await client.get(audio_url)
                    download_response.raise_for_status()
                    output_path.write_bytes(download_response.content)
                    generation_log.info(f"🎤 TTS: Saved to {output_path}")
            
            return audio_url
        
        except Exception as e:
            generation_log.error(f"🎤 TTS: ❌ Failed to generate speech: {e}")
            raise
    
    def get_available_characters(self) -> Dict[str, str]:
        """Get list of available character voices"""
        return {key: voice.description for key, voice in self.characters.items()}
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.total_generations = 0
        self.total_generation_time = 0.0
        self.last_generation_time = 0.0
        self.last_text_length = 0
        generation_log.info("🎤 TTS metrics reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get component status for monitoring"""
        avg_time = self.total_generation_time / max(1, self.total_generations)
        return {
            "total_generations": self.total_generations,
            "avg_generation_time": round(avg_time, 3),
            "last_generation_time": round(self.last_generation_time, 3),
            "last_text_length": self.last_text_length,
            "available_characters": len(self.characters)
        }


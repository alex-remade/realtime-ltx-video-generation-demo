import json
import openai
import requests
import base64
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path
from streaming_pipeline.models import TwitchComment
from streaming_pipeline.models import StreamingState, Monitorable

@dataclass
class PromptResult:
    selected_comment: Optional[TwitchComment]  # None for evolution
    prompt: str
    reasoning: str
    character: Optional[str] = None  # Character key for TTS voice
    dialogue: Optional[str] = None  # Dialogue to be narrated

VISUAL_MODE = True
NARRATION_MODE = True  # Enable character narration

# Get the directory of this file and construct path to prompts
current_dir = Path(__file__).parent.parent  # Go up to streaming_pipeline/
prompts_dir = current_dir / "prompts"

# Choose prompt file based on modes
if NARRATION_MODE:
    prompt_filename = "system_prompt_visual_narrated.txt"
elif VISUAL_MODE:
    prompt_filename = "system_prompt_visual.txt"
else:
    prompt_filename = "system_prompt.txt"

system_prompt = (prompts_dir / prompt_filename).read_text()


class PromptGenerator(Monitorable):
    # Class variables - configure these like DEV_MODE
    
    CONTEXT_WINDOW_SIZE = 10  # Number of previous prompts to include in context
    USE_GROQ = True  # Use Groq for both text and vision
    
    def __init__(self, openai_api_key: str, groq_api_key: str = None):
        # OpenAI client (always initialize as fallback)
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.system_prompt = system_prompt
        self.VISUAL_MODE = VISUAL_MODE
        self.NARRATION_MODE = NARRATION_MODE
        # Groq client (optional)
        if groq_api_key and self.USE_GROQ:
            self.groq_client = openai.OpenAI(
                api_key=groq_api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            print("🚀 Groq client initialized for fast inference")
        else:
            self.groq_client = None
            if self.USE_GROQ:
                print("⚠️ USE_GROQ=True but no GROQ_API_KEY provided, falling back to OpenAI")
            
        # Choose system prompt based on visual mode

   
        # Performance tracking for useful monitoring
        self.total_prompts = 0
        self.total_response_time = 0.0
        self.last_input_length = 0
        self.last_output_length = 0 
        self.last_generation_time = 0.0
    
    def _select_model_and_client(self, context):
        """Select optimal model and client based on requirements"""
        
        if self.USE_GROQ and self.groq_client:
            if self.VISUAL_MODE and context.current_frame_base64:
                # Use Groq's Llama 4 Scout for vision - fast and capable!
                print("🖼️ Using Groq Llama 4 Scout for FAST vision inference")
                return "meta-llama/llama-4-scout-17b-16e-instruct", self.groq_client
            else:
                # Use FASTEST text model for non-vision
                print("⚡ Using Groq llama-3.1-8b-instant for MAXIMUM SPEED")
                return "llama-3.1-8b-instant", self.groq_client
        
        # Fallback to OpenAI only if Groq not available
        elif self.VISUAL_MODE and context.current_frame_base64:
            print("🔄 Falling back to OpenAI GPT-4o for vision")
            return "gpt-4o", self.openai_client
        else:
            print("🔄 Falling back to OpenAI GPT-4o-mini")
            return "gpt-4o-mini", self.openai_client

    def generate_prompt(
        self, 
        comments: List[TwitchComment], 
        context: StreamingState,
        narration_history: List[Dict[str, Any]] = None,
        available_characters: Dict[str, str] = None
    ) -> PromptResult:
        """
        Generate prompt with Groq for both text and vision
        
        Args:
            comments: Recent Twitch comments
            context: Current streaming state
            narration_history: List of recent narrations with character and dialogue
            available_characters: Dict of character keys to descriptions
        """
        
        # Format comments for AI (or "None" if empty)
        if comments:
            comment_text = "\n".join([f"- {c.username}: {c.message}" for c in comments])
        else:
            comment_text = "None"
        
        # Format narration history
        if narration_history and len(narration_history) > 0:
            # Show last 5 narrations to create conversation context
            recent_narrations = narration_history[-5:]
            narration_text = "\n".join([
                f"- {n['character']}: \"{n['dialogue']}\""
                for n in recent_narrations
            ])
        else:
            narration_text = "None (This is the first narration)"
        
        # Format available characters
        if available_characters:
            characters_text = "\n".join([
                f"- {key}: {desc}"
                for key, desc in available_characters.items()
            ])
        else:
            characters_text = "- spongebob: Energetic, optimistic fry cook\n- narrator: Professional storyteller"
        
        # Create base system prompt
        formatted_prompt = self.system_prompt.format(
            previous_prompts=context.previous_prompts[-self.CONTEXT_WINDOW_SIZE:] if context.previous_prompts else ["None"],
            current_scene=context.current_scene,
            chat_comments=comment_text,
            mode=context.mode,
            narration_history=narration_text,
            available_characters=characters_text
        )
        
        # Select model and client
        model, client = self._select_model_and_client(context)
        
        print(f"🤖 Using {model} ({'Groq' if client == self.groq_client else 'OpenAI'}) for prompt generation")
        
        # Prepare messages
        messages = [{"role": "system", "content": formatted_prompt}]
        
        # Add visual context if enabled and available
        if self.VISUAL_MODE and context.current_frame_base64:
            try:
                user_message = {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text",
                            "text": "First, describe what you can see in this current frame in detail. Then generate the next video prompt following the system instructions."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{context.current_frame_base64}",
                                "detail": "high"  # Groq might handle high detail better
                            }
                        }
                    ]
                }
                messages.append(user_message)
                print(f"🖼️ Using {'Groq' if client == self.groq_client else 'OpenAI'} vision model")
            except Exception as e:
                print(f"⚠️ Failed to add visual context: {e}")
                # Fallback to text-only with same client
                model = "llama-3.1-70b-versatile" if client == self.groq_client else "gpt-4o-mini"
        
        # Track input size and start timing
        input_text = formatted_prompt + comment_text
        self.last_input_length = len(input_text)
        
        import time
        start_time = time.time()
        
        # Get AI response (same client selection)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=400,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # Track timing
            self.last_generation_time = time.time() - start_time
            self.total_response_time += self.last_generation_time
            self.total_prompts += 1
            
            # Parse response
            try:
                result = json.loads(response.choices[0].message.content)
                
                # Log the visual description ONLY if in visual mode
                if self.VISUAL_MODE and result.get('visual_description'):
                    print(f"👁️ AI VISUAL DESCRIPTION: {result['visual_description']}")
                
                # Log character narration if enabled
                if self.NARRATION_MODE and result.get('character') and result.get('dialogue'):
                    print(f"🎤 CHARACTER: {result['character']}")
                    print(f"💬 DIALOGUE: {result['dialogue']}")
                
                # Track output size
                self.last_output_length = len(result.get('prompt', '') + result.get('reasoning', ''))
                
                # Find the selected comment (if any)
                selected_comment = None
                if comments and result.get('selected_comment') != "null":
                    selected_comment = self._find_comment(comments, result['selected_comment'])
                
                # ENFORCE character variation - override if AI picks same character twice
                chosen_character = result.get('character') if self.NARRATION_MODE else None
                if chosen_character and narration_history and len(narration_history) > 0:
                    last_character = narration_history[-1].get('character')
                    if chosen_character == last_character:
                        # AI picked same character! Force variation
                        print(f"⚠️ AI picked same character '{chosen_character}' twice! Forcing variation...")
                        
                        # Get available characters and remove the last one
                        if available_characters:
                            available_keys = list(available_characters.keys())
                            if last_character in available_keys:
                                available_keys.remove(last_character)
                            
                            # Prefer spongebob<->squidward alternation
                            if last_character == 'spongebob' and 'squidward' in available_keys:
                                chosen_character = 'squidward'
                                print(f"   → Switched to Squidward (contrasting SpongeBob)")
                            elif last_character == 'squidward' and 'spongebob' in available_keys:
                                chosen_character = 'spongebob'
                                print(f"   → Switched to SpongeBob (contrasting Squidward)")
                            elif available_keys:
                                # Pick first available different character
                                chosen_character = available_keys[0]
                                print(f"   → Switched to {chosen_character}")
                            else:
                                print(f"   → No other characters available, keeping {chosen_character}")
                
                return PromptResult(
                    selected_comment=selected_comment,
                    prompt=result['prompt'],
                    reasoning=result['reasoning'],
                    character=chosen_character,
                    dialogue=result.get('dialogue') if self.NARRATION_MODE else None
                )
                
            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                print(f"AI parsing failed: {e}")
                # Simple fallback - EXACTLY like the original code
                if comments:
                    return PromptResult(
                        selected_comment=comments[0] if comments else None,
                        prompt=f"{context.current_scene}, {comments[0].message[:50] if comments[0] and comments[0].message else 'evolving'}, cinematic",
                        reasoning="AI parsing failed, used first comment",
                        character="narrator" if self.NARRATION_MODE else None,
                        dialogue="The adventure continues..." if self.NARRATION_MODE else None
                    )
                else:
                    return PromptResult(
                        selected_comment=None,
                        prompt=f"{context.current_scene}, slowly evolving, cinematic",
                        reasoning="AI parsing failed, simple evolution",
                        character="narrator" if self.NARRATION_MODE else None,
                        dialogue="The story unfolds..." if self.NARRATION_MODE else None
                    )
                    
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            # Fallback to simple evolution
            return PromptResult(
                selected_comment=None,
                prompt=f"{context.current_scene}, continuing naturally, cinematic",
                reasoning=f"API error: {e}",
                character="narrator" if self.NARRATION_MODE else None,
                dialogue="The journey continues..." if self.NARRATION_MODE else None
            )
    
    def _find_comment(self, comments: List[TwitchComment], selected_text: str) -> TwitchComment:
        """Find the comment that matches the AI selection"""
        if not selected_text:
            return comments[0] if comments else None
        
        selected_text_lower = selected_text.lower()
        
        for comment in comments:
            if not comment or not comment.message:
                continue
                
            comment_message_lower = comment.message.lower()
            if comment_message_lower in selected_text_lower or selected_text_lower in comment_message_lower:
                return comment
        
        return comments[0] if comments else None
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.total_prompts = 0
        self.total_response_time = 0.0
        self.last_input_length = 0
        self.last_output_length = 0
        self.last_generation_time = 0.0
        print("🧹 Prompt generation metrics reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get component status for monitoring - actual performance metrics!"""
        avg_response_time = self.total_response_time / max(1, self.total_prompts)
        return {
            "prompts_generated": self.total_prompts,
            "avg_response_time": round(avg_response_time, 3),
            "last_input_length": self.last_input_length,
            "last_output_length": self.last_output_length,
            "last_generation_time": round(self.last_generation_time, 3)
        }

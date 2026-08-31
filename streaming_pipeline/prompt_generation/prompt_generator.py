import json
import os
import openai
import requests
import base64
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from streaming_pipeline.models import TwitchComment
from streaming_pipeline.models import StreamingState, Monitorable

FAL_OPENROUTER_BASE_URL = "https://fal.run/openrouter/router/openai/v1"
# Defaults benchmarked on the fal proxy (Aug 2026): gemini-2.5-flash was the
# fastest and most consistent option (~1.25s per prompt-gen call, served by
# Google), with reliable JSON-mode + vision support. fal disallows per-request
# provider selection, so we can't force a Groq/Cerebras route through this
# proxy -- keep GROQ_API_KEY set if you need sub-second prompt latency.
FAL_OPENROUTER_DEFAULT_VISION_MODEL = "google/gemini-2.5-flash"
FAL_OPENROUTER_DEFAULT_TEXT_MODEL = "google/gemini-2.5-flash"

@dataclass
class PromptResult:
    selected_comment: Optional[TwitchComment]  # None for evolution
    prompt: str
    reasoning: str

VISUAL_MODE = True

# System prompts embedded as constants so they work on fal runners without
# filesystem access to the original .txt files.  The source-of-truth files
# still live in streaming_pipeline/prompts/ for readability.

PROMPT_CHAOTIC = """\
## 🔄 **Update Video Streamer to Pass Visual Context**

You are creating video prompts from Twitch chat for continuous video generation with VISUAL AWARENESS.

CONTEXT:
Recent story (last ~100 seconds): {previous_prompts}
Current scene: {current_scene}
Generation mode: {mode}

CHAT COMMENTS:
{chat_comments}

VISUAL ANALYSIS:
1. QUICKLY identify what's in the frame (characters, objects, environment)
2. Note any artifacts or quality issues
3. BUT DON'T GET STUCK - your job is to EVOLVE the story!

CRITICAL STORYTELLING RULES:
1. **NEVER REPEAT** - If recent prompts are similar, FORCE dramatic change
2. **ALWAYS PROGRESS** - Each prompt must ADD something new or CHANGE something significant
3. **BE BOLD** - Don't just describe what you see, TRANSFORM it
4. **FIX PROBLEMS** - If scene is messy/boring, use dramatic transitions (explosions, portals, sudden changes)

PROGRESSION TACTICS:
- Scene getting repetitive? → Add NEW character/object/event
- Character stuck in one action? → Make them DO something different
- Same location too long? → Transport to NEW location
- Too much flying/floating? → LAND somewhere interesting
- Too static? → Add CONFLICT or CHALLENGE
- Too peaceful? → Create URGENCY or DANGER

TASK:
If chat comments are provided:
1. Pick the most TRANSFORMATIVE comment
2. Use it to DRASTICALLY change the current scene
3. Don't worry about perfect continuity - video AI will handle transitions

If no comments:
1. Look at last 3 prompts - if similar, do something COMPLETELY DIFFERENT
2. Introduce NEW: location, character, object, or event
3. Create CONFLICT, DISCOVERY, or TRANSFORMATION
4. NEVER just continue the same action

STYLE:
- Action verbs (crashes, transforms, discovers, battles)
- Specific NEW elements each time
- Under 120 characters
- Focus on CHANGE not continuity

EXAMPLES OF GOOD PROGRESSION:
- Astronaut flying → Astronaut CRASHES into alien spaceship
- Robot walking → Robot TRANSFORMS into vehicle  
- Character exploring → Character DISCOVERS hidden portal
- Scene peaceful → EXPLOSION changes everything

MODE INSTRUCTIONS:
If mode is "nightmare": Make ALL prompts nightmarish/bizarre/outlandish. Transform normal actions into surreal/disturbing scenarios.

CRITICAL: You MUST respond with VALID JSON ONLY.

JSON Format (required):
{{"visual_description": "what you see", "selected_comment": "exact text or null", "prompt": "NEW action that CHANGES the story", "reasoning": "why this creates progression"}}"""

PROMPT_COHESIVE = """\
You are the writer and director of an ongoing animated story. The characters
on screen are PROTAGONISTS with personalities, goals, and emotions. Your job
is to write WHAT HAPPENS NEXT in their story.

STORY PREMISE: {story_premise}
CLIP NUMBER: {generation_count}

AVAILABLE CHARACTERS:
{character_cast}
These characters exist in your story world. Bring them in naturally when the
narrative calls for it -- not every character needs to be on screen at once.
A character can enter, exit, be heard off-screen, or be referenced.

CONTEXT:
Recent story (last ~100 seconds): {previous_prompts}
Current scene: {current_scene}
Generation mode: {mode}

CHAT COMMENTS:
{chat_comments}

VISUAL ANALYSIS:
Identify which characters are currently visible and what they are doing.
These are story characters with intentions and reactions, not just objects.

CHARACTER DIRECTION:
- Use character NAMES in your prompts when they appear
- Characters should WANT things, TRY things, REACT to things
- They have emotions: curiosity, surprise, frustration, determination, joy
- They interact with their environment and with EACH OTHER
- They notice changes and respond to them
- They make DECISIONS that drive the story forward
- New characters ENTER scenes naturally (walk in, appear, are discovered)

STORY RHYTHM (based on clip number):
- Clips 1-3: ESTABLISH the scene. Show the character in their environment,
  let the viewer understand who they are and where they are.
- Clips 4-6: INTRODUCE a situation. Something catches the character's attention.
  A sound, a light, an object, a change in the environment.
- Clips 7-10: DEVELOP tension. The character investigates, tries something,
  encounters a problem or discovery. Stakes should rise.
- Clips 11-15: ESCALATE. Things get more interesting -- the character must
  react to consequences, make a choice, or deal with something unexpected.
- Clips 16+: RESOLVE and RESET. The situation reaches a peak, then a new
  situation begins. New cycle starts.

CONTINUITY RULES:
1. Same characters, same location (unless transitioning naturally)
2. Each prompt flows from the previous one -- no teleportation
3. New elements enter NATURALLY (walk in, appear in background, are discovered)
4. Transitions through doors, corridors, camera movement -- not cuts

WHEN CHAT COMMENTS EXIST:
1. Pick the most interesting comment
2. Make it something the CHARACTER encounters or reacts to within the story
3. Don't break the scene -- WEAVE the comment into the narrative

WHEN NO COMMENTS:
1. Follow the STORY RHYTHM above based on the current clip number
2. Give the character something to DO, not just something to look at
3. Build toward the next beat in the rhythm

STYLE:
- Write what the CHARACTER DOES, not what the camera sees
- Action verbs: notices, reaches for, stumbles, discovers, recoils, grins
- Include character emotion/reaction when relevant
- Under 120 characters
- Present tense, active voice

MODE INSTRUCTIONS:
If mode is "nightmare": Gradually introduce unsettling elements. Objects subtly
wrong, shadows that move, familiar things becoming alien. The character starts
to notice something is off. Build dread through the character's growing unease.

CRITICAL: Respond with VALID JSON ONLY.
JSON Format:
{{"visual_description": "what you see", "selected_comment": "exact text or null", "prompt": "what the character DOES next in the story", "reasoning": "how this advances the story rhythm"}}"""

STYLE_PRESETS = {
    "cohesive": {
        "prompt": PROMPT_COHESIVE,
        "temperature": 0.55,
    },
    "chaotic": {
        "prompt": PROMPT_CHAOTIC,
        "temperature": 0.7,
    },
    "nightmare": {
        "prompt": PROMPT_CHAOTIC,
        "temperature": 0.9,
    },
}

# Default system prompt
system_prompt = PROMPT_CHAOTIC if VISUAL_MODE else PROMPT_CHAOTIC


class PromptGenerator(Monitorable):
    CONTEXT_WINDOW_SIZE = 10
    USE_GROQ = True
    # When FAL_KEY is available, route through fal's OpenRouter proxy first
    # so all LLM usage is billed via the fal account instead of requiring
    # separate OpenAI/Groq keys.
    USE_FAL_OPENROUTER = True

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        fal_key: Optional[str] = None,
    ):
        self.system_prompt = system_prompt
        self.temperature = 0.7
        self.VISUAL_MODE = VISUAL_MODE

        # None base_url → official OpenAI; set OPENAI_BASE_URL for any
        # OpenAI-compatible endpoint (Groq, a2agent, Ollama, etc.).
        self.openai_base_url = os.getenv("OPENAI_BASE_URL") or None
        openai_model = os.getenv("OPENAI_MODEL")
        self.openai_text_model = openai_model or "gpt-4o-mini"
        self.openai_vision_model = openai_model or "gpt-4o"

        self.openai_client = (
            openai.OpenAI(
                api_key=openai_api_key,
                base_url=self.openai_base_url,
            )
            if openai_api_key
            else None
        )

        if groq_api_key and self.USE_GROQ:
            self.groq_client = openai.OpenAI(
                api_key=groq_api_key,
                base_url="https://api.groq.com/openai/v1",
            )
            print("🚀 Groq client initialized for fast inference")
        else:
            self.groq_client = None

        if fal_key and self.USE_FAL_OPENROUTER:
            # fal expects `Authorization: Key <FAL_KEY>`, not the standard
            # `Bearer` header the openai SDK would send, so we override
            # default_headers instead of using api_key.
            self.fal_openrouter_client = openai.OpenAI(
                api_key="not-needed",
                base_url=FAL_OPENROUTER_BASE_URL,
                default_headers={"Authorization": f"Key {fal_key}"},
            )
            print("🛰️  fal→OpenRouter client initialized (billed via FAL_KEY)")
        else:
            self.fal_openrouter_client = None

        if not any([self.fal_openrouter_client, self.groq_client, self.openai_client]):
            raise ValueError(
                "PromptGenerator requires at least one of FAL_KEY, "
                "GROQ_API_KEY, or OPENAI_API_KEY to be set."
            )

        # Model slugs used against fal→OpenRouter. Override via env if you
        # want to swap in Claude, Gemini, Llama, etc. (any OpenRouter slug).
        self.fal_vision_model = os.getenv(
            "FAL_OPENROUTER_VISION_MODEL", FAL_OPENROUTER_DEFAULT_VISION_MODEL
        )
        self.fal_text_model = os.getenv(
            "FAL_OPENROUTER_TEXT_MODEL", FAL_OPENROUTER_DEFAULT_TEXT_MODEL
        )

        self.total_prompts = 0
        self.total_response_time = 0.0
        self.last_input_length = 0
        self.last_output_length = 0
        self.last_generation_time = 0.0

    def set_style_preset(self, name: str) -> None:
        """Apply a named style preset (system prompt + temperature)."""
        preset = STYLE_PRESETS.get(name)
        if preset is None:
            print(f"⚠️ Unknown style preset '{name}', keeping current settings")
            return
        self.system_prompt = preset["prompt"]
        self.temperature = preset["temperature"]
        print(f"🎨 Style preset '{name}': temperature={self.temperature}")
    
    def _select_model_and_client(self, context):
        """Select optimal model and client based on requirements.

        Preference order:
          1. Explicit OpenAI-compatible endpoint (OPENAI_BASE_URL)
          2. fal → OpenRouter (unified billing via FAL_KEY)
          3. Groq (fastest inference, when GROQ_API_KEY is set)
          4. OpenAI direct
        """
        needs_vision = self.VISUAL_MODE and context.current_frame_base64

        # Explicit OpenAI-compatible endpoint (OPENAI_BASE_URL) wins so
        # alternative providers are actually used even when FAL_KEY is set.
        if self.openai_client and self.openai_base_url:
            model = (
                self.openai_vision_model if needs_vision else self.openai_text_model
            )
            print(f"🔗 Using OpenAI-compatible endpoint: {model}")
            return model, self.openai_client

        if self.fal_openrouter_client:
            model = self.fal_vision_model if needs_vision else self.fal_text_model
            label = "vision" if needs_vision else "text"
            print(f"🛰️  Using fal→OpenRouter {label} model: {model}")
            return model, self.fal_openrouter_client

        if self.USE_GROQ and self.groq_client:
            if needs_vision:
                print("🖼️ Using Groq Llama 4 Scout for FAST vision inference")
                return "meta-llama/llama-4-scout-17b-16e-instruct", self.groq_client
            print("⚡ Using Groq llama-3.1-8b-instant for MAXIMUM SPEED")
            return "llama-3.1-8b-instant", self.groq_client

        if self.openai_client:
            if needs_vision:
                print(f"🔄 Falling back to OpenAI {self.openai_vision_model} for vision")
                return self.openai_vision_model, self.openai_client
            print(f"🔄 Falling back to OpenAI {self.openai_text_model}")
            return self.openai_text_model, self.openai_client

        raise RuntimeError("No LLM client available for prompt generation")

    def _provider_label(self, client) -> str:
        if client is self.fal_openrouter_client:
            return "fal→OpenRouter"
        if client is self.groq_client:
            return "Groq"
        return "OpenAI"

    def generate_prompt(self, comments: List[TwitchComment], context: StreamingState) -> PromptResult:
        """Generate prompt with Groq for both text and vision"""
        
        # Format comments for AI (or "None" if empty)
        if comments:
            comment_text = "\n".join([f"- {c.username}: {c.message}" for c in comments])
        else:
            comment_text = "None"
        
        # Build template variables.  story_premise and generation_count are
        # used by the cohesive prompt but ignored (via **kwargs-style) by the
        # chaotic prompt which doesn't have those placeholders.
        story_premise = context.previous_prompts[0] if context.previous_prompts else "an animated story"

        # Build character cast description for the LLM
        if context.character_names:
            character_cast = "\n".join(f"- {name}" for name in context.character_names)
        else:
            character_cast = "- (No specific characters defined -- use whatever characters appear in the scene)"

        template_vars = dict(
            previous_prompts=context.previous_prompts[-self.CONTEXT_WINDOW_SIZE:] if context.previous_prompts else ["None"],
            current_scene=context.current_scene,
            chat_comments=comment_text,
            mode=context.mode,
            story_premise=story_premise,
            generation_count=context.generation_count,
            character_cast=character_cast,
        )
        # Only pass vars that exist in the template to avoid KeyError on
        # prompts that don't use all variables.
        import re
        template_keys = set(re.findall(r'\{(\w+)\}', self.system_prompt))
        filtered_vars = {k: v for k, v in template_vars.items() if k in template_keys}
        formatted_prompt = self.system_prompt.format(**filtered_vars)
        
        # Select model and client
        model, client = self._select_model_and_client(context)
        provider_label = self._provider_label(client)

        print(f"🤖 Using {model} ({provider_label}) for prompt generation")
        
        # Prepare messages
        messages = [{"role": "system", "content": formatted_prompt}]
        
        # Add visual context if enabled and available
        # Use detail="low" to keep token usage well under Groq's 30k TPM limit.
        # "low" mode uses ~85 tokens per image regardless of resolution; "high"
        # uses 1k-3k tokens which causes 429 rate limit errors at our cadence.
        if self.VISUAL_MODE and context.current_frame_base64:
            try:
                user_message = {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "First, briefly describe what you can see in this current frame. Then generate the next video prompt following the system instructions."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{context.current_frame_base64}",
                                "detail": "low"
                            }
                        }
                    ]
                }
                messages.append(user_message)
                print(f"🖼️ Using {provider_label} vision model")
            except Exception as e:
                print(f"⚠️ Failed to add visual context: {e}")
                # Fallback to text-only with same client
                if client == self.fal_openrouter_client:
                    model = self.fal_text_model
                elif client == self.groq_client:
                    model = "llama-3.1-70b-versatile"
                else:
                    model = self.openai_text_model
        
        # Track input size and start timing
        input_text = formatted_prompt + comment_text
        self.last_input_length = len(input_text)
        
        import time
        start_time = time.time()
        
        # Get AI response (same client selection).
        # On 429 (rate limit), retry once without the image to keep the stream
        # alive instead of falling all the way back to a generic prompt.
        try:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=400,
                    temperature=self.temperature,
                    response_format={"type": "json_object"}
                )
            except Exception as e:
                err = str(e)
                is_rate_limit = "429" in err or "rate_limit" in err.lower() or "tokens per minute" in err.lower()
                if is_rate_limit and self.VISUAL_MODE and len(messages) > 1:
                    print(f"⚠️ Rate limit hit, retrying text-only without image...")
                    text_only_messages = [m for m in messages if m.get("role") == "system"]
                    text_only_messages.append({"role": "user", "content": comment_text or "Generate the next video prompt following the system instructions."})
                    if client == self.fal_openrouter_client:
                        text_only_model = self.fal_text_model
                    elif client == self.groq_client:
                        text_only_model = "llama-3.1-8b-instant"
                    else:
                        text_only_model = self.openai_text_model
                    response = client.chat.completions.create(
                        model=text_only_model,
                        messages=text_only_messages,
                        max_tokens=400,
                        temperature=self.temperature,
                        response_format={"type": "json_object"}
                    )
                    print(f"✅ Text-only fallback succeeded with {text_only_model}")
                else:
                    raise
            
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
                
                # Track output size
                self.last_output_length = len(result.get('prompt', '') + result.get('reasoning', ''))
                
                # Find the selected comment (if any)
                selected_comment = None
                if comments and result.get('selected_comment') != "null":
                    selected_comment = self._find_comment(comments, result['selected_comment'])
                
                return PromptResult(
                    selected_comment=selected_comment,
                    prompt=result['prompt'],
                    reasoning=result['reasoning']
                )
                
            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                print(f"AI parsing failed: {e}")
                # Simple fallback - EXACTLY like the original code
                if comments:
                    return PromptResult(
                        selected_comment=comments[0] if comments else None,
                        prompt=f"{context.current_scene}, {comments[0].message[:50] if comments[0] and comments[0].message else 'evolving'}, cinematic",
                        reasoning="AI parsing failed, used first comment"
                    )
                else:
                    return PromptResult(
                        selected_comment=None,
                        prompt=f"{context.current_scene}, slowly evolving, cinematic",
                        reasoning="AI parsing failed, simple evolution"
                    )
                    
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            # Fallback to simple evolution
            return PromptResult(
                selected_comment=None,
                prompt=f"{context.current_scene}, continuing naturally, cinematic",
                reasoning=f"API error: {e}"
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

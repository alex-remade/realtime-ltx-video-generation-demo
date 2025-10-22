// Shared types for the FAL Realtime Dashboard

// Model types
export type ModelType = 'ltxv1' | 'ltxv2-preview'

// Component-specific metrics types
export interface RTMPMetrics {
  queue_size: number
  frames_sent: number
  frames_dropped: number
  current_fps: number
  target_fps: number
  is_streaming: boolean
}

export interface VideoMetrics {
  is_running: boolean
  generation_count: number
  current_prompt: string
  generation_params_history: GenerationParams[]
}

export interface PromptMetrics {
  prompts_generated: number
  avg_response_time: number
  last_input_length: number
  last_output_length: number
  last_generation_time: number
}

export interface GeneratorMetrics {
  videos_generated: number
  avg_generation_time: number
  last_generation_time: number
}

export interface OverlayMetrics {
  frames_processed: number
  avg_time_per_frame: number
  has_overlay: boolean
  last_batch_size: number
  last_batch_time: number
  last_batch_avg_per_frame: number
}

export interface TwitchMetrics {
  channel: string
  is_listening: boolean
  queue_size: number
}

// Main metrics interface with nested component metrics
export interface ComponentMetrics {
  timestamp: number
  gpu_memory_allocated: number
  
  // Component-specific metrics
  rtmp: RTMPMetrics
  video: VideoMetrics
  prompt: PromptMetrics
  generator: GeneratorMetrics
  overlay: OverlayMetrics
  twitch: TwitchMetrics
}


export interface GenerationParams {
  timestamp: number
  generation_id: number
  prompt: string
  negative_prompt: string
  width: number
  height: number
  num_frames: number
  strength: number
  guidance_scale: number
  timesteps: number[]
}

export interface RealtimeData {
  metrics: ComponentMetrics | null
  history: Array<ComponentMetrics>
  isConnected: boolean
  error: string | null
}

export interface WebSocketMessage {
  type: 'metrics' | 'error'
  data?: ComponentMetrics
  message?: string
  timestamp: number
}

export interface GenerationHistoryProps {
  generationHistory?: GenerationParams[]
}

// LTXv2 Preview configuration types
export interface LTXv2Config {
  model: 'ltxv2-preview'
  image_url: string
  prompt: string
  duration?: 6 | 8
  resolution?: '720p' | '1080p' | '1440p'
  aspect_ratio?: '9:16' | '16:9'
  enable_prompt_expansion?: boolean
  // Streaming parameters (applied after generation)
  target_fps?: number
  width?: number
  height?: number
}

// LTXv1 configuration types (existing streaming model)
export interface LTXv1Config {
  model: 'ltxv1'
  initial_prompt: string
  initial_image_url: string
  negative_prompt: string
  height: number
  width: number
  num_frames: number
  strength: number
  guidance_scale: number
  timesteps: number[]
  target_fps: number
  mode: 'regular' | 'nightmare'
}

export type TestConfig = LTXv1Config | LTXv2Config

'use client'

import { useState, useRef } from 'react'
import { Play, Square, Upload, Settings, Sliders, Zap } from 'lucide-react'
import type { TestConfig, LTXv1Config, LTXv2Config, ModelType } from '../types'

interface TestControlPanelProps {
  onStartTest: (config: TestConfig) => void
  onStopTest: () => void
  isStreaming: boolean
}

export default function TestControlPanel({ onStartTest, onStopTest, isStreaming }: TestControlPanelProps) {
  const [selectedModel, setSelectedModel] = useState<ModelType>('ltxv1')
  
  const [ltxv1Config, setLtxv1Config] = useState<LTXv1Config>({
    model: 'ltxv1',
    initial_prompt: "Spongebob leaves the room through the door",
    initial_image_url: "https://storage.googleapis.com/remade-v2/uploads/a185f836a3e9ca84cc75f5c12bb10dd4.jpg",
    negative_prompt: "worst quality, inconsistent motion, blurry, jittery, distorted",
    height: 480,
    width: 640,
    num_frames: 240,
    strength: 1.2,
    guidance_scale: 5.0,
    timesteps: [1000, 981, 909, 725, 0.03],
    target_fps: 14.0,
    mode: 'regular'
  })

  const [ltxv2Config, setLtxv2Config] = useState<LTXv2Config>({
    model: 'ltxv2-preview',
    image_url: "https://storage.googleapis.com/remade-v2/uploads/a185f836a3e9ca84cc75f5c12bb10dd4.jpg",
    prompt: "A cinematic video with smooth camera movement and realistic motion",
    duration: 6,
    resolution: '720p',
    aspect_ratio: '16:9',
    enable_prompt_expansion: true,
    // Streaming parameters
    target_fps: 14.0,
    width: 640,
    height: 480,
  })

  const [showAdvanced, setShowAdvanced] = useState(false)
  const [uploadingImage, setUploadingImage] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // Get current config based on selected model
  const config = selectedModel === 'ltxv1' ? ltxv1Config : ltxv2Config
  
  // Computed prompt value that includes nightmare prefix when needed (LTXv1 only)
  const displayedPrompt = selectedModel === 'ltxv1' && ltxv1Config.mode === 'nightmare' && !ltxv1Config.initial_prompt.startsWith('(Nightmare Started)')
    ? `(Nightmare Started) ${ltxv1Config.initial_prompt}`
    : selectedModel === 'ltxv1' ? ltxv1Config.initial_prompt : ltxv2Config.prompt

  const handleImageUpload = async (file: File) => {
    // Simple validation
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }
    
    if (file.size > 10 * 1024 * 1024) {
      alert('Image must be smaller than 10MB')
      return
    }

    setUploadingImage(true)
    try {
      console.log('📄 Converting image:', file.name)
      
      // Convert to base64 data URL for now
      const reader = new FileReader()
      reader.onload = (e) => {
        const result = e.target?.result as string
        
        // Update the appropriate config based on selected model
        if (selectedModel === 'ltxv1') {
          setLtxv1Config(prev => ({ 
            ...prev, 
            initial_image_url: result
          }))
        } else {
          setLtxv2Config(prev => ({ 
            ...prev, 
            image_url: result
          }))
        }
        
        console.log('✅ Image converted successfully')
        setUploadingImage(false)
      }
      reader.onerror = () => {
        console.error('Failed to read file')
        alert('Failed to read image file')
        setUploadingImage(false)
      }
      reader.readAsDataURL(file)
      
    } catch (error) {
      console.error('Failed to process image:', error)
      alert('Failed to process image. Please try again.')
      setUploadingImage(false)
    }
  }



  return (
    <div className="fal-card">
      <div className="fal-card-header">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Settings className="w-5 h-5 text-fal-yellow-500" />
            <h3 className="text-lg font-semibold text-fal-gray-900">Video Generation</h3>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="btn-secondary text-sm"
            >
              <Sliders className="w-4 h-4 mr-2" />
              {showAdvanced ? 'Hide' : 'Show'} Advanced
            </button>
          </div>
        </div>
      </div>
      
      <div className="fal-card-content space-y-6">
        
        {/* Model Selector */}
        <div>
          <label className="metric-label mb-3 block">Select Model</label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setSelectedModel('ltxv1')}
              className={`px-4 py-3 rounded-lg text-sm font-medium transition-all border-2 ${
                selectedModel === 'ltxv1'
                  ? 'bg-fal-primary-500 text-white border-fal-primary-500 shadow-lg'
                  : 'bg-white text-fal-gray-700 hover:bg-fal-gray-50 border-fal-gray-300'
              }`}
            >
              <div className="flex items-center justify-center space-x-2">
                <Zap className="w-4 h-4" />
                <span>LTX v1 (Streaming)</span>
              </div>
              <p className="text-xs mt-1 opacity-75">Real-time streaming pipeline</p>
            </button>
            
            <button
              type="button"
              onClick={() => setSelectedModel('ltxv2-preview')}
              className={`px-4 py-3 rounded-lg text-sm font-medium transition-all border-2 ${
                selectedModel === 'ltxv2-preview'
                  ? 'bg-fal-primary-500 text-white border-fal-primary-500 shadow-lg'
                  : 'bg-white text-fal-gray-700 hover:bg-fal-gray-50 border-fal-gray-300'
              }`}
            >
              <div className="flex items-center justify-center space-x-2">
                <Zap className="w-4 h-4" />
                <span>LTX v2 Preview</span>
              </div>
              <p className="text-xs mt-1 opacity-75">New image-to-video model</p>
            </button>
          </div>
        </div>

        {/* Basic Configuration */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Prompt Configuration */}
          <div className="space-y-4">
            <div>
              <label className="metric-label mb-2 block">
                {selectedModel === 'ltxv1' ? 'Initial Prompt' : 'Prompt'}
              </label>
              <textarea
                value={displayedPrompt}
                onChange={(e) => {
                  let newPrompt = e.target.value
                  
                  if (selectedModel === 'ltxv1') {
                    // Remove nightmare prefix if user is editing and it exists
                    if (newPrompt.startsWith('(Nightmare Started) ')) {
                      newPrompt = newPrompt.replace('(Nightmare Started) ', '')
                    }
                    setLtxv1Config(prev => ({ ...prev, initial_prompt: newPrompt }))
                  } else {
                    setLtxv2Config(prev => ({ ...prev, prompt: newPrompt }))
                  }
                }}
                className="w-full bg-fal-gray-100 border border-fal-gray-300 rounded-lg p-3 text-fal-gray-900 text-sm"
                rows={3}
                placeholder={selectedModel === 'ltxv1' 
                  ? "Describe the initial video content..." 
                  : "Describe the video you want to generate..."}
              />
            </div>
            
            {/* Mode Selector - LTXv1 only */}
            {selectedModel === 'ltxv1' && (
              <div>
                <label className="metric-label mb-2 block">Generation Mode</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setLtxv1Config(prev => ({ 
                      ...prev, 
                      mode: 'regular',
                      strength: prev.strength === 1.4 ? 1.0 : prev.strength
                    }))}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      ltxv1Config.mode === 'regular'
                        ? 'bg-fal-primary-500 text-white'
                        : 'bg-fal-gray-100 text-fal-gray-700 hover:bg-fal-gray-200 border border-fal-gray-300'
                    }`}
                  >
                    🌟 Regular
                  </button>
                  <button
                    type="button"
                    onClick={() => setLtxv1Config(prev => ({ 
                      ...prev, 
                      mode: 'nightmare',
                      strength: 1.4
                    }))}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      ltxv1Config.mode === 'nightmare'
                        ? 'bg-fal-red-500 text-white'
                        : 'bg-fal-gray-100 text-fal-gray-700 hover:bg-fal-gray-200 border border-fal-gray-300'
                    }`}
                  >
                    😈 Nightmare
                  </button>
                </div>
                {ltxv1Config.mode === 'nightmare' && (
                  <div className="mt-2 p-2 bg-fal-red-50 border border-fal-red-200 rounded text-xs text-fal-red-700">
                    <strong>Nightmare Mode:</strong> Prompts will be enhanced to create nightmarish/outlandish content.
                    <br />Strength automatically set to 1.4 for more dramatic effects.
                  </div>
                )}
              </div>
            )}
            
            {/* LTXv2 Options */}
            {selectedModel === 'ltxv2-preview' && (
              <>
                <div>
                  <label className="metric-label mb-2 block">Duration</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setLtxv2Config(prev => ({ ...prev, duration: 6 }))}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        ltxv2Config.duration === 6
                          ? 'bg-fal-primary-500 text-white'
                          : 'bg-fal-gray-100 text-fal-gray-700 hover:bg-fal-gray-200 border border-fal-gray-300'
                      }`}
                    >
                      6 seconds
                    </button>
                    <button
                      type="button"
                      onClick={() => setLtxv2Config(prev => ({ ...prev, duration: 8 }))}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        ltxv2Config.duration === 8
                          ? 'bg-fal-primary-500 text-white'
                          : 'bg-fal-gray-100 text-fal-gray-700 hover:bg-fal-gray-200 border border-fal-gray-300'
                      }`}
                    >
                      8 seconds
                    </button>
                  </div>
                </div>
                
                <div>
                  <label className="metric-label mb-2 block">Resolution</label>
                  <select
                    value={ltxv2Config.resolution}
                    onChange={(e) => setLtxv2Config(prev => ({ 
                      ...prev, 
                      resolution: e.target.value as '720p' | '1080p' | '1440p' 
                    }))}
                    className="w-full bg-fal-gray-100 border border-fal-gray-300 rounded-lg p-3 text-fal-gray-900 text-sm"
                  >
                    <option value="720p">720p</option>
                    <option value="1080p">1080p</option>
                    <option value="1440p">1440p</option>
                  </select>
                </div>
                
                <div>
                  <label className="metric-label mb-2 block">Aspect Ratio</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setLtxv2Config(prev => ({ ...prev, aspect_ratio: '16:9' }))}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        ltxv2Config.aspect_ratio === '16:9'
                          ? 'bg-fal-primary-500 text-white'
                          : 'bg-fal-gray-100 text-fal-gray-700 hover:bg-fal-gray-200 border border-fal-gray-300'
                      }`}
                    >
                      16:9 Landscape
                    </button>
                    <button
                      type="button"
                      onClick={() => setLtxv2Config(prev => ({ ...prev, aspect_ratio: '9:16' }))}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        ltxv2Config.aspect_ratio === '9:16'
                          ? 'bg-fal-primary-500 text-white'
                          : 'bg-fal-gray-100 text-fal-gray-700 hover:bg-fal-gray-200 border border-fal-gray-300'
                      }`}
                    >
                      9:16 Portrait
                    </button>
                  </div>
                </div>
              </>
            )}
            
            {/* Negative Prompt - LTXv1 only */}
            {selectedModel === 'ltxv1' && (
              <div>
                <label className="metric-label mb-2 block">Negative Prompt</label>
                <textarea
                  value={ltxv1Config.negative_prompt}
                  onChange={(e) => setLtxv1Config(prev => ({ ...prev, negative_prompt: e.target.value }))}
                  className="w-full bg-fal-gray-100 border border-fal-gray-300 rounded-lg p-3 text-fal-gray-900 text-sm"
                  rows={2}
                  placeholder="What to avoid in the generation..."
                />
              </div>
            )}
          </div>

          {/* Image Upload */}
          <div className="space-y-4">
            <div>
              <label className="metric-label mb-2 block">
                {selectedModel === 'ltxv1' ? 'Initial Image' : 'Source Image'}
              </label>
              <div className="space-y-3">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={(e) => {
                    const file = e.target.files?.[0]
                    if (file) handleImageUpload(file)
                  }}
                  accept="image/*"
                  className="hidden"
                />
                
                {/* Unified Upload/Preview Area */}
                <div 
                  className={`relative border-2 border-dashed rounded-lg transition-all ${
                    uploadingImage 
                      ? 'border-fal-primary-400 bg-fal-primary-50' 
                      : (selectedModel === 'ltxv1' ? ltxv1Config.initial_image_url : ltxv2Config.image_url)
                        ? 'border-fal-gray-300 bg-fal-gray-50' 
                        : 'border-fal-gray-300 bg-fal-gray-100 hover:border-fal-primary-400 hover:bg-fal-primary-50 cursor-pointer'
                  }`}
                  onClick={() => !uploadingImage && fileInputRef.current?.click()}
                >
                  {(selectedModel === 'ltxv1' ? ltxv1Config.initial_image_url : ltxv2Config.image_url) ? (
                    // Image Preview State - Click to replace
                    <div className="relative group cursor-pointer">
                      <img
                        src={selectedModel === 'ltxv1' ? ltxv1Config.initial_image_url : ltxv2Config.image_url}
                        alt="Initial frame"
                        className="w-full max-h-48 object-contain rounded"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none'
                        }}
                      />
                      {/* Simple hover overlay */}
                      <div className="absolute inset-0 bg-fal-primary-600 bg-opacity-0 group-hover:bg-opacity-20 transition-all rounded flex items-center justify-center">
                        <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                          <Upload className="w-8 h-8 text-white drop-shadow-lg" />
                        </div>
                      </div>
                      {/* Clear button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          if (selectedModel === 'ltxv1') {
                            setLtxv1Config(prev => ({ ...prev, initial_image_url: '' }))
                          } else {
                            setLtxv2Config(prev => ({ ...prev, image_url: '' }))
                          }
                        }}
                        className="absolute top-2 right-2 w-6 h-6 bg-fal-red-500 hover:bg-fal-red-600 text-white rounded-full flex items-center justify-center text-sm font-bold transition-colors opacity-70 hover:opacity-100"
                        title="Remove image"
                      >
                        ×
                      </button>
                    </div>
                  ) : uploadingImage ? (
                    // Uploading State
                    <div className="flex flex-col items-center justify-center py-12">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-fal-primary-500 mb-3"></div>
                      <p className="text-fal-primary-600 font-medium">Uploading image...</p>
                    </div>
                  ) : (
                    // Empty State
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                      <Upload className="w-12 h-12 text-fal-gray-400 mb-3" />
                      <p className="text-fal-gray-600 font-medium mb-1">Click to upload an image</p>
                      <p className="text-fal-gray-500 text-sm">PNG, JPG, GIF up to 10MB</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Streaming Parameters - Both Models */}
        <div>
          <label className="metric-label mb-3 block">Streaming Parameters</label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <label className="metric-label mb-2 block text-xs">Target FPS</label>
              <input
                type="number"
                value={selectedModel === 'ltxv1' ? ltxv1Config.target_fps : ltxv2Config.target_fps}
                onChange={(e) => {
                  const value = parseFloat(e.target.value)
                  if (selectedModel === 'ltxv1') {
                    setLtxv1Config(prev => ({ ...prev, target_fps: value }))
                  } else {
                    setLtxv2Config(prev => ({ ...prev, target_fps: value }))
                  }
                }}
                className="w-full bg-fal-gray-100 border border-fal-gray-300 rounded-lg p-3 text-fal-gray-900 font-mono"
                min={1}
                max={30}
                step={0.5}
              />
            </div>
            
            <div>
              <label className="metric-label mb-2 block text-xs">Stream Width</label>
              <input
                type="number"
                value={selectedModel === 'ltxv1' ? ltxv1Config.width : ltxv2Config.width}
                onChange={(e) => {
                  const value = parseInt(e.target.value)
                  if (selectedModel === 'ltxv1') {
                    setLtxv1Config(prev => ({ ...prev, width: value }))
                  } else {
                    setLtxv2Config(prev => ({ ...prev, width: value }))
                  }
                }}
                className="w-full bg-fal-gray-100 border border-fal-gray-300 rounded-lg p-3 text-fal-gray-900 font-mono"
                min={256}
                max={1920}
                step={32}
              />
            </div>
            
            <div>
              <label className="metric-label mb-2 block text-xs">Stream Height</label>
              <input
                type="number"
                value={selectedModel === 'ltxv1' ? ltxv1Config.height : ltxv2Config.height}
                onChange={(e) => {
                  const value = parseInt(e.target.value)
                  if (selectedModel === 'ltxv1') {
                    setLtxv1Config(prev => ({ ...prev, height: value }))
                  } else {
                    setLtxv2Config(prev => ({ ...prev, height: value }))
                  }
                }}
                className="w-full bg-fal-gray-100 border border-fal-gray-300 rounded-lg p-3 text-fal-gray-900 font-mono"
                min={256}
                max={1080}
                step={32}
              />
            </div>
          </div>
          <p className="text-xs text-fal-gray-600 mt-2">
            {selectedModel === 'ltxv2-preview' 
              ? 'Stream resolution: Videos are resized from ltxv2 output to these dimensions for streaming'
              : 'Generation and streaming resolution'}
          </p>
        </div>

        {/* LTXv1-specific Parameters */}
        {selectedModel === 'ltxv1' && (
          <div className="grid grid-cols-2 md:grid-cols-2 gap-4">
            <div>
              <label className="metric-label mb-2 block">Frames</label>
              <input
                type="number"
                value={ltxv1Config.num_frames}
                onChange={(e) => setLtxv1Config(prev => ({ ...prev, num_frames: parseInt(e.target.value) }))}
                className="w-full bg-fal-gray-100 border border-fal-gray-300 rounded-lg p-3 text-fal-gray-900 font-mono"
                min={60}
                max={500}
                step={10}
              />
            </div>
            
            <div>
              <label className="metric-label mb-2 block">Guidance Scale</label>
              <input
                type="number"
                value={ltxv1Config.guidance_scale}
                onChange={(e) => setLtxv1Config(prev => ({ ...prev, guidance_scale: parseFloat(e.target.value) }))}
                className="w-full bg-fal-gray-100 border border-fal-gray-300 rounded-lg p-3 text-fal-gray-900 font-mono"
                min={1}
                max={10}
                step={0.1}
              />
            </div>
            
            <div>
              <label className="metric-label mb-2 block">Strength</label>
              <input
                type="number"
                value={ltxv1Config.strength}
                onChange={(e) => setLtxv1Config(prev => ({ ...prev, strength: parseFloat(e.target.value) }))}
                className="w-full bg-fal-gray-100 border border-fal-gray-300 rounded-lg p-3 text-fal-gray-900 font-mono"
                min={0.1}
                max={2.0}
                step={0.1}
              />
            </div>
          </div>
        )}

        {/* Advanced Parameters - LTXv1 only */}
        {showAdvanced && selectedModel === 'ltxv1' && (
          <div className="space-y-4 border-t border-fal-gray-700 pt-6">
            <h4 className="text-fal-gray-900 font-medium">Advanced LTXv1 Parameters</h4>
            
            <div>
              <label className="metric-label mb-2 block">Timesteps (comma-separated)</label>
              <input
                type="text"
                value={ltxv1Config.timesteps.join(', ')}
                onChange={(e) => {
                  try {
                    const timesteps = e.target.value.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n))
                    setLtxv1Config(prev => ({ ...prev, timesteps }))
                  } catch (error) {
                    // Invalid input, ignore
                  }
                }}
                className="w-full bg-fal-gray-100 border border-fal-gray-300 rounded-lg p-3 text-fal-gray-900 font-mono text-sm"
                placeholder="1000, 981, 909, 725, 0.03"
              />
            </div>


          </div>
        )}



        {/* Control Buttons */}
        <div className="flex items-center justify-between pt-4 border-t border-fal-gray-700">
          <div className="flex items-center space-x-4">
            {!isStreaming ? (
              <button
                onClick={() => {
                  // Create config based on selected model
                  if (selectedModel === 'ltxv1') {
                    const processedConfig: TestConfig = {
                      ...ltxv1Config,
                      initial_prompt: displayedPrompt
                    }
                    onStartTest(processedConfig)
                  } else {
                    // For ltxv2, normalize field names to match backend API
                    const processedConfig: any = {
                      ...ltxv2Config,
                      // Map ltxv2 image_url to initial_image_url for backend
                      initial_image_url: ltxv2Config.image_url,
                      initial_prompt: ltxv2Config.prompt
                    }
                    onStartTest(processedConfig)
                  }
                }}
                className="btn-primary flex items-center space-x-2"
              >
                <Play className="w-4 h-4" />
                <span>Start Stream</span>
              </button>
            ) : (
              <button
                onClick={onStopTest}
                className="bg-fal-red-500 hover:bg-fal-red-600 text-white font-medium px-6 py-2 rounded-lg transition-colors flex items-center space-x-2"
              >
                <Square className="w-4 h-4" />
                <span>Stop Stream</span>
              </button>
            )}
          </div>
          

        </div>
      </div>
    </div>
  )
}

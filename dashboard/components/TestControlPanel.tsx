'use client'

import { useState, useRef } from 'react'
import { Play, Square, Upload, Settings, Sliders } from 'lucide-react'

interface LTXTestConfig {
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

interface TestControlPanelProps {
  onStartTest: (config: LTXTestConfig) => void
  onStopTest: () => void
  isStreaming: boolean
}

export default function TestControlPanel({ onStartTest, onStopTest, isStreaming }: TestControlPanelProps) {
  const [config, setConfig] = useState<LTXTestConfig>({
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

  const [showAdvanced, setShowAdvanced] = useState(false)
  const [uploadingImage, setUploadingImage] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // Computed prompt value that includes nightmare prefix when needed
  const displayedPrompt = config.mode === 'nightmare' && !config.initial_prompt.startsWith('(Nightmare Started)')
    ? `(Nightmare Started) ${config.initial_prompt}`
    : config.initial_prompt

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
        setConfig(prev => ({ 
          ...prev, 
          initial_image_url: result
        }))
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
            <h3 className="text-lg font-semibold text-fal-gray-900">Streaming Parameters</h3>
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

        {/* Basic Configuration */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Prompt Configuration */}
          <div className="space-y-4">
            <div>
              <label className="metric-label mb-2 block">Initial Prompt</label>
              <textarea
                value={displayedPrompt}
                onChange={(e) => {
                  let newPrompt = e.target.value
                  // Remove nightmare prefix if user is editing and it exists
                  if (newPrompt.startsWith('(Nightmare Started) ')) {
                    newPrompt = newPrompt.replace('(Nightmare Started) ', '')
                  }
                  setConfig(prev => ({ ...prev, initial_prompt: newPrompt }))
                }}
                className="w-full bg-fal-gray-100 border border-fal-gray-300 rounded-lg p-3 text-fal-gray-900 text-sm"
                rows={3}
                placeholder="Describe the initial video content..."
              />
            </div>
            
            {/* Mode Selector */}
            <div>
              <label className="metric-label mb-2 block">Generation Mode</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setConfig(prev => ({ 
                    ...prev, 
                    mode: 'regular',
                    strength: prev.strength === 1.4 ? 1.0 : prev.strength // Reset to 1.0 if it was nightmare value
                  })) }
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    config.mode === 'regular'
                      ? 'bg-fal-primary-500 text-white'
                      : 'bg-fal-gray-100 text-fal-gray-700 hover:bg-fal-gray-200 border border-fal-gray-300'
                  }`}
                >
                  🌟 Regular
                </button>
                <button
                  type="button"
                  onClick={() => setConfig(prev => ({ 
                    ...prev, 
                    mode: 'nightmare',
                    strength: 1.4 // Automatically set higher strength for nightmare effects
                  }))
                }
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    config.mode === 'nightmare'
                      ? 'bg-fal-red-500 text-white'
                      : 'bg-fal-gray-100 text-fal-gray-700 hover:bg-fal-gray-200 border border-fal-gray-300'
                  }`}
                >
                  😈 Nightmare
                </button>
              </div>
              {config.mode === 'nightmare' && (
                <div className="mt-2 p-2 bg-fal-red-50 border border-fal-red-200 rounded text-xs text-fal-red-700">
                  <strong>Nightmare Mode:</strong> Prompts will be enhanced to create nightmarish/outlandish content.
                  <br />Strength automatically set to 1.4 for more dramatic effects.
                </div>
              )}
            </div>
            
            <div>
              <label className="metric-label mb-2 block">Negative Prompt</label>
              <textarea
                value={config.negative_prompt}
                onChange={(e) => setConfig(prev => ({ ...prev, negative_prompt: e.target.value }))}
                className="w-full bg-fal-gray-100 border border-fal-gray-300 rounded-lg p-3 text-fal-gray-900 text-sm"
                rows={2}
                placeholder="What to avoid in the generation..."
              />
            </div>
          </div>

          {/* Image Upload */}
          <div className="space-y-4">
            <div>
              <label className="metric-label mb-2 block">Initial Image</label>
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
                      : config.initial_image_url 
                        ? 'border-fal-gray-300 bg-fal-gray-50' 
                        : 'border-fal-gray-300 bg-fal-gray-100 hover:border-fal-primary-400 hover:bg-fal-primary-50 cursor-pointer'
                  }`}
                  onClick={() => !uploadingImage && fileInputRef.current?.click()}
                >
                  {config.initial_image_url ? (
                    // Image Preview State - Click to replace
                    <div className="relative group cursor-pointer">
                      <img
                        src={config.initial_image_url}
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
                          setConfig(prev => ({ ...prev, initial_image_url: '' }))
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

        {/* Core Parameters */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="metric-label mb-2 block">Frames</label>
            <input
              type="number"
              value={config.num_frames}
              onChange={(e) => setConfig(prev => ({ ...prev, num_frames: parseInt(e.target.value) }))}
              className="w-full bg-fal-gray-100 border border-fal-gray-300 rounded-lg p-3 text-fal-gray-900 font-mono"
              min={60}
              max={500}
              step={10}
            />
          </div>
          
          <div>
            <label className="metric-label mb-2 block">Target FPS</label>
            <input
              type="number"
              value={config.target_fps}
              onChange={(e) => setConfig(prev => ({ ...prev, target_fps: parseFloat(e.target.value) }))}
              className="w-full bg-fal-gray-100 border border-fal-gray-300 rounded-lg p-3 text-fal-gray-900 font-mono"
              min={1}
              max={30}
              step={0.5}
            />
          </div>
          
          <div>
            <label className="metric-label mb-2 block">Guidance Scale</label>
            <input
              type="number"
              value={config.guidance_scale}
              onChange={(e) => setConfig(prev => ({ ...prev, guidance_scale: parseFloat(e.target.value) }))}
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
              value={config.strength}
              onChange={(e) => setConfig(prev => ({ ...prev, strength: parseFloat(e.target.value) }))}
              className="w-full bg-fal-gray-100 border border-fal-gray-300 rounded-lg p-3 text-fal-gray-900 font-mono"
              min={0.1}
              max={1.0}
              step={0.1}
            />
          </div>
        </div>

        {/* Advanced Parameters */}
        {showAdvanced && (
          <div className="space-y-4 border-t border-fal-gray-700 pt-6">
            <h4 className="text-fal-gray-900 font-medium">Advanced Parameters</h4>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="metric-label mb-2 block">Width</label>
                <input
                  type="number"
                  value={config.width}
                  onChange={(e) => setConfig(prev => ({ ...prev, width: parseInt(e.target.value) }))}
                  className="w-full bg-fal-gray-100 border border-fal-gray-300 rounded-lg p-3 text-fal-gray-900 font-mono"
                  min={256}
                  max={1024}
                  step={32}
                />
              </div>
              
              <div>
                <label className="metric-label mb-2 block">Height</label>
                <input
                  type="number"
                  value={config.height}
                  onChange={(e) => setConfig(prev => ({ ...prev, height: parseInt(e.target.value) }))}
                  className="w-full bg-fal-gray-100 border border-fal-gray-300 rounded-lg p-3 text-fal-gray-900 font-mono"
                  min={256}
                  max={1024}
                  step={32}
                />
              </div>
              
            </div>
            
            <div>
              <label className="metric-label mb-2 block">Timesteps (comma-separated)</label>
              <input
                type="text"
                value={config.timesteps.join(', ')}
                onChange={(e) => {
                  try {
                    const timesteps = e.target.value.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n))
                    setConfig(prev => ({ ...prev, timesteps }))
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
                  // Send config with displayed prompt (includes nightmare prefix if applicable)
                  const processedConfig = {
                    ...config,
                    initial_prompt: displayedPrompt
                  }
                  
                  onStartTest(processedConfig)
                }}
                className="btn-primary flex items-center space-x-2"
              >
                <Play className="w-4 h-4" />
                <span>Start Stream Test</span>
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

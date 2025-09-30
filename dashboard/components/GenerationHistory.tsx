'use client'

import { Clock, Settings, Image, Video } from 'lucide-react'
import type { GenerationParams, GenerationHistoryProps } from '../types'

export default function GenerationHistory({ generationHistory = [] }: GenerationHistoryProps) {
  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString()
  }


  return (
    <div className="fal-card">
      <div className="fal-card-header">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Video className="w-5 h-5 text-fal-blue-500" />
            <h3 className="text-lg font-semibold text-fal-gray-900">Generation History</h3>
          </div>
          <div className="text-sm text-fal-gray-600">
            Last {generationHistory.length} generations
          </div>
        </div>
      </div>
      
      <div className="fal-card-content">
        {generationHistory.length === 0 ? (
          <div className="text-center py-8 text-fal-gray-600">
            <Video className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No generations yet</p>
            <p className="text-sm">Start streaming to see generation parameters</p>
          </div>
        ) : (
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {generationHistory.slice().reverse().map((generation, index) => (
              <div
                key={generation.generation_id}
                className={`border rounded-lg p-4 ${
                  index === 0 
                    ? 'border-fal-green-500 bg-fal-green-500/10' 
                    : 'border-fal-gray-200 bg-fal-gray-50'
                }`}
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-mono text-fal-gray-700">
                        #{generation.generation_id}
                      </span>
                      {index === 0 && (
                        <span className="px-2 py-1 text-xs bg-fal-green-500 text-black rounded-full font-medium">
                          LATEST
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-1 text-xs text-fal-gray-600">
                    <Clock className="w-3 h-3" />
                    <span>{formatTimestamp(generation.timestamp)}</span>
                  </div>
                </div>

                {/* Prompt */}
                <div className="mb-3">
                  <div className="text-sm font-medium text-fal-gray-700 mb-1">Prompt</div>
                  <div className="text-sm text-fal-gray-900 bg-fal-gray-100 rounded p-2 font-mono">
                    {generation.prompt}
                  </div>
                </div>

                {/* Parameters Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                  <div className="space-y-1">
                    <div className="text-fal-gray-600 flex items-center space-x-1">
                      <Image className="w-3 h-3" />
                      <span>Dimensions</span>
                    </div>
                    <div className="text-fal-gray-900 font-mono">
                      {generation.width}×{generation.height}
                    </div>
                  </div>
                  
                  <div className="space-y-1">
                    <div className="text-fal-gray-600 flex items-center space-x-1">
                      <Video className="w-3 h-3" />
                      <span>Frames</span>
                    </div>
                    <div className="text-fal-gray-900 font-mono">
                      {generation.num_frames}
                    </div>
                  </div>
                  
                  <div className="space-y-1">
                    <div className="text-fal-gray-600 flex items-center space-x-1">
                      <Settings className="w-3 h-3" />
                      <span>Strength</span>
                    </div>
                    <div className="text-fal-gray-900 font-mono">
                      {generation.strength}
                    </div>
                  </div>
                  
                  <div className="space-y-1">
                    <div className="text-fal-gray-600 flex items-center space-x-1">
                      <Settings className="w-3 h-3" />
                      <span>Guidance</span>
                    </div>
                    <div className="text-fal-gray-900 font-mono">
                      {generation.guidance_scale}
                    </div>
                  </div>
                </div>

                {/* Timesteps (if space allows) */}
                {generation.timesteps && generation.timesteps.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-fal-gray-700">
                    <div className="text-xs text-fal-gray-600 mb-1">Timesteps</div>
                    <div className="text-xs text-fal-gray-900 font-mono truncate">
                      [{generation.timesteps.join(', ')}]
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

'use client'

import { Brain, Video, Type, Zap, Clock, TrendingUp } from 'lucide-react'
import type { ComponentMetrics } from '../types'

interface AIPerformanceBreakdownProps {
  data: ComponentMetrics | null
}

export default function AIPerformanceBreakdown({ data }: AIPerformanceBreakdownProps) {
  if (!data) {
    return (
      <div className="fal-card">
        <div className="fal-card-content">
          <div className="flex items-center justify-center h-32">
            <div className="text-fal-gray-600">No pipeline data available</div>
          </div>
        </div>
      </div>
    )
  }

  const formatTime = (seconds: number | undefined) => {
    if (!seconds || seconds === 0) return '0ms'
    if (seconds < 0.001) return `${(seconds * 1000000).toFixed(0)}μs`
    if (seconds < 1) return `${(seconds * 1000).toFixed(1)}ms`
    return `${seconds.toFixed(2)}s`
  }

  const getPerformanceColor = (time: number | undefined, threshold: number) => {
    if (!time || time === 0) return 'text-fal-gray-600'
    if (time < threshold * 0.5) return 'text-fal-green-600'
    if (time < threshold) return 'text-fal-yellow-600'
    return 'text-fal-red-600'
  }

  // Calculate total pipeline time
  const totalPipelineTime = (data.prompt?.avg_response_time || 0) + 
                           (data.generator?.avg_generation_time || 0) + 
                           (data.overlay?.avg_time_per_frame || 0) * 240 // ~240 frames per video

  return (
    <div className="fal-card">
      <div className="fal-card-header">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Brain className="w-5 h-5 text-fal-purple-500" />
            <h3 className="text-lg font-semibold text-fal-gray-900">AI Pipeline Breakdown</h3>
          </div>
          <div className="text-sm text-fal-gray-600 font-mono">
            Total: {formatTime(totalPipelineTime)}
          </div>
        </div>
      </div>
      <div className="fal-card-content">
        <div className="space-y-4">
          
          {/* Pipeline Step Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            
            {/* AI Prompt Generation */}
            <div className="bg-fal-gray-50 border border-fal-gray-200 rounded-lg p-4 hover:border-fal-blue-500/50 transition-colors">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Zap className="w-4 h-4 text-fal-blue-500" />
                  <h4 className="font-medium text-fal-gray-900">AI Prompt</h4>
                </div>
                <div className="text-xs text-fal-gray-600">{(data.prompt?.prompts_generated || 0)} total</div>
              </div>
              
              <div className="space-y-2">
                <div className="text-center">
                  <div className={`text-2xl font-bold font-mono ${getPerformanceColor((data.prompt?.avg_response_time || 0), 2.0)}`}>
                    {formatTime((data.prompt?.avg_response_time || 0))}
                  </div>
                  <div className="text-xs text-fal-gray-600">Average</div>
                </div>
                <div className="text-center">
                  <div className={`text-lg font-mono ${getPerformanceColor((data.prompt?.last_generation_time || 0), 2.0)}`}>
                    {formatTime((data.prompt?.last_generation_time || 0))}
                  </div>
                  <div className="text-xs text-fal-gray-600">Latest</div>
                </div>
              </div>
            </div>

            {/* Video Generation */}
            <div className="bg-fal-gray-50 border border-fal-gray-200 rounded-lg p-4 hover:border-fal-green-500/50 transition-colors">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Video className="w-4 h-4 text-fal-green-500" />
                  <h4 className="font-medium text-fal-gray-900">Video Gen</h4>
                </div>
                <div className="text-xs text-fal-gray-600">{(data.generator?.videos_generated || 0)} total</div>
              </div>
              
              <div className="space-y-2">
                <div className="text-center">
                  <div className={`text-2xl font-bold font-mono ${getPerformanceColor((data.generator?.avg_generation_time || 0), 10.0)}`}>
                    {formatTime((data.generator?.avg_generation_time || 0))}
                  </div>
                  <div className="text-xs text-fal-gray-600">Average</div>
                </div>
                <div className="text-center">
                  <div className={`text-lg font-mono ${getPerformanceColor((data.generator?.last_generation_time || 0), 10.0)}`}>
                    {formatTime((data.generator?.last_generation_time || 0))}
                  </div>
                  <div className="text-xs text-fal-gray-600">Latest</div>
                </div>
              </div>
            </div>

            {/* Text Overlay */}
            <div className="bg-fal-gray-50 border border-fal-gray-200 rounded-lg p-4 hover:border-fal-purple-500/50 transition-colors">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Type className="w-4 h-4 text-fal-purple-500" />
                  <h4 className="font-medium text-fal-gray-900">Overlay</h4>
                </div>
                <div className="text-xs text-fal-gray-600">{(data.overlay?.frames_processed || 0)} total | {(data.overlay?.last_batch_size || 0)} last batch</div>
              </div>
              
              <div className="space-y-2">
                <div className="text-center">
                  <div className={`text-2xl font-bold font-mono ${getPerformanceColor((data.overlay?.avg_time_per_frame || 0), 0.01)}`}>
                    {formatTime((data.overlay?.avg_time_per_frame || 0))}
                  </div>
                  <div className="text-xs text-fal-gray-600">Per Frame</div>
                </div>
                <div className="text-center">
                  <div className={`text-lg font-mono ${getPerformanceColor((data.overlay?.last_batch_avg_per_frame || 0), 0.01)}`}>
                    {formatTime((data.overlay?.last_batch_avg_per_frame || 0))}
                  </div>
                  <div className="text-xs text-fal-gray-600">Last Batch Avg</div>
                </div>
              </div>
            </div>
          </div>

          {/* Pipeline Efficiency Bar */}
          <div className="bg-fal-gray-50 border border-fal-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium text-fal-gray-900">Pipeline Efficiency</h4>
              <div className="text-sm text-fal-gray-600">
                {(data.video?.is_running || false) ? 'Processing...' : 'Idle'}
              </div>
            </div>
            
            <div className="space-y-2">
              {/* Visual breakdown of time spent in each stage */}
              <div className="flex h-6 rounded-full overflow-hidden bg-fal-gray-700">
                <div 
                  className="bg-fal-blue-500 transition-all duration-300"
                  style={{ width: `${((data.prompt?.avg_response_time || 0) / totalPipelineTime) * 100}%` }}
                  title={`AI: ${formatTime((data.prompt?.avg_response_time || 0))}`}
                />
                <div 
                  className="bg-fal-green-500 transition-all duration-300"
                  style={{ width: `${((data.generator?.avg_generation_time || 0) / totalPipelineTime) * 100}%` }}
                  title={`Video: ${formatTime((data.generator?.avg_generation_time || 0))}`}
                />
                <div 
                  className="bg-fal-purple-500 transition-all duration-300"
                  style={{ width: `${(((data.overlay?.avg_time_per_frame || 0) * 240) / totalPipelineTime) * 100}%` }}
                  title={`Overlay: ${formatTime((data.overlay?.avg_time_per_frame || 0) * 240)}`}
                />
              </div>
              
              <div className="flex justify-between text-xs text-fal-gray-600">
                <span>🤖 AI: {(((data.prompt?.avg_response_time || 0) / totalPipelineTime) * 100).toFixed(1)}%</span>
                <span>🎬 Video: {(((data.generator?.avg_generation_time || 0) / totalPipelineTime) * 100).toFixed(1)}%</span>
                <span>📝 Overlay: {((((data.overlay?.avg_time_per_frame || 0) * 240) / totalPipelineTime) * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

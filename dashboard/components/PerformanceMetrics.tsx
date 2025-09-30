'use client'

import { Cpu, Zap, Layers, Clock, Activity, MemoryStick } from 'lucide-react'
import type { ComponentMetrics } from '../types'

interface PerformanceMetricsProps {
  data: ComponentMetrics | null
}

export default function PerformanceMetrics({ data }: PerformanceMetricsProps) {
  if (!data) {
    return (
      <div className="fal-card">ß
        <div className="fal-card-content">
          <div className="flex items-center justify-center h-32">
            <div className="text-fal-gray-600">No performance data available</div>
          </div>s
        </div>
      </div>
    )
  }

  const formatTime = (seconds: number) => {
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`
    return `${seconds.toFixed(1)}s`
  }


  return (
    <div className="fal-card">
      <div className="fal-card-header">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Activity className="w-5 h-5 text-fal-purple-500" />
            <h3 className="text-lg font-semibold text-fal-gray-900">Performance Metrics</h3>
          </div>
          <div className="text-sm text-fal-gray-600 font-mono">Real-time FPS & Timing</div>
        </div>
      </div>
      <div className="fal-card-content">

        <div className="space-y-6">
          {/* Generation Performance */}
          <div className="bg-fal-gray-50 border border-fal-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <Zap className="w-5 h-5 text-fal-blue-500" />
                <h4 className="font-medium text-fal-gray-900">AI Generation</h4>
              </div>
              <div className="text-sm text-fal-gray-600 font-mono">
                {data.video?.generation_count || 0} generations
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="metric-value text-fal-green-600">
                  {formatTime(data.generator?.avg_generation_time || 0)}
                </div>
                <div className="metric-label">Avg Video Time</div>
              </div>
              <div className="text-center">
                <div className="metric-value text-fal-blue-600">
                  {formatTime(data.prompt?.avg_response_time || 0)}
                </div>
                <div className="metric-label">Avg AI Time</div>
              </div>
              <div className="text-center">
                <div className={`metric-value ${
                  (data.video?.is_running || false) ? 'text-fal-green-600' : 'text-fal-gray-600'
                }`}>
                  {(data.video?.is_running || false) ? 'ACTIVE' : 'IDLE'}
                </div>
                <div className="metric-label">Status</div>
              </div>
            </div>
          </div>

          {/* GPU Memory */}
          <div className="bg-fal-gray-50 border border-fal-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <MemoryStick className="w-5 h-5 text-fal-red-500" />
                <h4 className="font-medium text-fal-gray-900">GPU Memory</h4>
              </div>
            </div>
            
            <div className="text-center">
              <div className={`text-3xl font-bold font-mono ${
                (data.gpu_memory_allocated || 0) < 30 ? 'text-fal-green-600' : 
                (data.gpu_memory_allocated || 0) < 45 ? 'text-fal-yellow-600' : 'text-fal-red-600'
              }`}>
                {(data.gpu_memory_allocated || 0).toFixed(1)} GB
              </div>
              <div className="metric-label">Allocated</div>
              
              {/* GPU Memory Bar */}
              <div className="mt-4">
                <div className="progress-bar">
                  <div 
                    className={`progress-fill ${
                      (data.gpu_memory_allocated || 0) < 30 ? 'bg-fal-green-500' : 
                      (data.gpu_memory_allocated || 0) < 45 ? 'bg-fal-yellow-500' : 'bg-fal-red-500'
                    }`}
                    style={{ width: `${Math.min(((data.gpu_memory_allocated || 0) / 80) * 100, 100)}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-fal-gray-500 mt-1">
                  <span>0 GB</span>
                  <span>80 GB</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

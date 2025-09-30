'use client'

import { useState, useEffect } from 'react'
import { Activity, AlertTriangle, CheckCircle, Clock, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import type { ComponentMetrics } from '../types'

interface QueueVisualizationProps {
  data: ComponentMetrics | null
}

export default function QueueVisualization({ data }: QueueVisualizationProps) {
  if (!data) {
    return (
      <div className="fal-card">
        <div className="fal-card-content">
          <div className="flex items-center justify-center h-32">
            <div className="text-fal-gray-600">No queue data available</div>
          </div>
        </div>
      </div>
    )
  }

  const getQueueStatus = () => {
    if ((data.rtmp?.queue_size || 0) === 0) return { status: 'empty', color: 'danger', icon: AlertTriangle }
    if ((data.rtmp?.queue_size || 0) < 50) return { status: 'low', color: 'warning', icon: Clock }
    return { status: 'good', color: 'success', icon: CheckCircle }
  }

  const queueStatus = getQueueStatus()
  const StatusIcon = queueStatus.icon

  // Queue visualization bar
  const maxDisplayQueue = 200
  const queueFillPercentage = Math.min(((data.rtmp?.queue_size || 0) / maxDisplayQueue) * 100, 100)

  const getBarColor = () => {
    if ((data.rtmp?.queue_size || 0) === 0) return 'bg-fal-red-500'
    if ((data.rtmp?.queue_size || 0) < 50) return 'bg-fal-yellow-500' 
    return 'bg-fal-green-500'
  }


  return (
    <div className="fal-card">
      <div className="fal-card-header">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Activity className="w-5 h-5 text-fal-green-500" />
            <h3 className="text-lg font-semibold text-fal-gray-900">Queue & Performance</h3>
          </div>
          <div className={`status-indicator status-${queueStatus.color}`}>
            <StatusIcon className="w-4 h-4 mr-1" />
            {queueStatus.status.toUpperCase()}
          </div>
        </div>
      </div>
      <div className="fal-card-content">

        {/* Queue Bar Visualization */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-fal-gray-600 mb-3">
            <span>Queue Size</span>
            <span className="font-mono">{(data.rtmp?.queue_size || 0)} frames ({((data.rtmp?.queue_size || 0) / (data.rtmp?.target_fps || 9)).toFixed(1)}s buffer)</span>
          </div>
          <div className="progress-bar">
            <div 
              className={`progress-fill ${getBarColor()}`}
              style={{ width: `${queueFillPercentage}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-fal-gray-600 mt-1">
            <span>0</span>
            <span className="font-mono">{(data.rtmp?.queue_size || 0)} / {maxDisplayQueue}</span>
            <span>{maxDisplayQueue}</span>
          </div>
        </div>

        {/* Current FPS Display */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-fal-gray-600 mb-3">
            <span>Current FPS</span>
            <span className="font-mono">{(data.rtmp?.current_fps || 0)?.toFixed(1) || '0.0'} / {(data.rtmp?.target_fps || 9) || 9}</span>
          </div>
          <div className="progress-bar">
            <div 
              className={`progress-fill ${
                ((data.rtmp?.current_fps || 0) || 0) >= ((data.rtmp?.target_fps || 9) || 9) * 0.9 ? 'bg-fal-green-500' :
                ((data.rtmp?.current_fps || 0) || 0) >= ((data.rtmp?.target_fps || 9) || 9) * 0.7 ? 'bg-fal-yellow-500' : 'bg-fal-red-500'
              }`}
              style={{ width: `${Math.min((((data.rtmp?.current_fps || 0) || 0) / ((data.rtmp?.target_fps || 9) || 9)) * 100, 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-fal-gray-600 mt-1">
            <span>0</span>
            <span className="font-mono">{(((data.rtmp?.current_fps || 0) || 0) / ((data.rtmp?.target_fps || 9) || 9) * 100).toFixed(0)}%</span>
            <span>{(data.rtmp?.target_fps || 9) || 9}</span>
          </div>
        </div>

        {/* Generation Status */}
        <div className="mt-6 p-4 bg-fal-gray-50 border border-fal-gray-200 rounded-lg">
          <div className="flex items-center space-x-3">
            <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
              (data.video?.is_running || false) ? 'bg-fal-green-500' : 'bg-fal-gray-300'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                (data.video?.is_running || false) ? 'bg-white animate-pulse' : 'bg-fal-gray-600'
              }`}></div>
            </div>
            <div>
              <div className="metric-label">AI Generation Status</div>
              <div className={`text-lg font-bold ${
                (data.video?.is_running || false) ? 'text-fal-green-600' : 'text-fal-gray-600'
              }`}>
                {(data.video?.is_running || false) ? 'ACTIVE' : 'WAITING'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

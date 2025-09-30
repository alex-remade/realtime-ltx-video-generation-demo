'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { useState, useEffect, useMemo } from 'react'
import { TrendingUp, BarChart3, Activity } from 'lucide-react'
import type { ComponentMetrics } from '../types'


interface RealtimeChartProps {
  data: ComponentMetrics[]
  title: string
  type: 'queue' | 'fps' | 'flow'
}

export default function RealtimeChart({ data, title, type }: RealtimeChartProps) {
  // Use useMemo to prevent unnecessary re-calculations and reduce flickering
  const chartData = useMemo(() => {
    if (data.length === 0) {
      return []
    }

    // Create a stable 60-second timeline
    const timelineData = []
    const latestData = data.slice(-60) // Get last 60 data points
    
    // Create 60 fixed time slots
    for (let i = 0; i < 60; i++) {
      const dataIndex = latestData.length - 60 + i
      const point = dataIndex >= 0 ? latestData[dataIndex] : (latestData[0] || {
        rtmp: { queue_size: 0, frames_sent: 0, current_fps: 0, target_fps: 0, is_streaming: false, frames_dropped: 0 },
        timestamp: Date.now() / 1000
      })
      
      timelineData.push({
        queue_size: point.rtmp?.queue_size || 0,
        frames_sent: point.rtmp?.frames_sent || 0,
        current_fps: point.rtmp?.current_fps || 0,
        target_fps: point.rtmp?.target_fps || 0,
        time: `${59 - i}s`,
        timeIndex: i,
        secondsAgo: 59 - i
      })
    }
    
    return timelineData
  }, [data])

  const renderQueueChart = () => (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis 
          dataKey="time" 
          tick={{ fontSize: 11, fill: '#4b5563' }}
          interval={9}
          axisLine={{ stroke: '#e5e7eb' }}
          tickLine={{ stroke: '#e5e7eb' }}
        />
        <YAxis 
          tick={{ fontSize: 11, fill: '#4b5563' }}
          axisLine={{ stroke: '#e5e7eb' }}
          domain={[0, 400]}
        />
        <Tooltip 
          labelFormatter={(value) => `${value} ago`}
          formatter={(value: any, name: string) => [
            `${value} frames`,
            'Queue Size'
          ]}
          contentStyle={{
            backgroundColor: '#ffffff',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            color: '#374151'
          }}
        />
        <Area 
          type="monotone" 
          dataKey="queue_size" 
          stroke="#60a5fa" 
          fill="#60a5fa" 
          fillOpacity={0.2}
          strokeWidth={2}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  )

  const renderFlowChart = () => (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis 
          dataKey="time" 
          tick={{ fontSize: 11, fill: '#4b5563' }}
          interval={9}
          axisLine={{ stroke: '#e5e7eb' }}
          tickLine={{ stroke: '#e5e7eb' }}
        />
        <YAxis 
          tick={{ fontSize: 11, fill: '#4b5563' }}
          axisLine={{ stroke: '#e5e7eb' }}
          domain={[0, 50]}
        />
        <Tooltip 
          labelFormatter={(value) => `${value} ago`}
          formatter={(value: any, name: string, props: any) => {
            const label = props.dataKey === 'frames_added' ? 'Added' : 'Consumed'
            return [`${value} frames/s`, label]
          }}
          contentStyle={{
            backgroundColor: '#ffffff',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            color: '#374151'
          }}
        />
        <Line 
          type="monotone" 
          dataKey="frames_added" 
          stroke="#22c55e" 
          strokeWidth={2}
          dot={false}
          name="Added"
          isAnimationActive={false}
        />
        <Line 
          type="monotone" 
          dataKey="frames_consumed" 
          stroke="#ef4444" 
          strokeWidth={2}
          dot={false}
          name="Consumed"
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )

  const renderFPSChart = () => (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis 
          dataKey="time" 
          tick={{ fontSize: 11, fill: '#4b5563' }}
          interval={9}
          axisLine={{ stroke: '#e5e7eb' }}
          tickLine={{ stroke: '#e5e7eb' }}
        />
        <YAxis 
          tick={{ fontSize: 11, fill: '#4b5563' }}
          axisLine={{ stroke: '#e5e7eb' }}
          domain={[0, 20]}
        />
        <Tooltip 
          labelFormatter={(value) => `${value} ago`}
          formatter={(value: any, name: string) => [
            `${value} FPS`,
            'Generation FPS'
          ]}
          contentStyle={{
            backgroundColor: '#ffffff',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            color: '#374151'
          }}
        />
        <Line 
          type="monotone" 
          dataKey="generation_fps" 
          stroke="#a78bfa" 
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )

  const renderChart = () => {
    switch (type) {
      case 'queue':
        return renderQueueChart()
      case 'flow':
        return renderFlowChart()
      case 'fps':
        return renderFPSChart()
      default:
        return renderQueueChart()
    }
  }

  const getChartIcon = () => {
    switch (type) {
      case 'queue': return BarChart3
      case 'flow': return TrendingUp
      case 'fps': return Activity
      default: return BarChart3
    }
  }
  
  const getChartColor = () => {
    switch (type) {
      case 'queue': return 'text-fal-blue-500'
      case 'flow': return 'text-fal-green-500'
      case 'fps': return 'text-fal-purple-500'
      default: return 'text-fal-blue-500'
    }
  }
  
  const ChartIcon = getChartIcon()

  return (
    <div className="fal-card">
      <div className="fal-card-header">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <ChartIcon className={`w-5 h-5 ${getChartColor()}`} />
            <h3 className="text-lg font-semibold text-fal-gray-900">{title}</h3>
          </div>
          <div className="text-sm text-fal-gray-600 font-mono">
            Last {Math.min(chartData.length, 60)}s
          </div>
        </div>
      </div>
      <div className="fal-card-content">
        {chartData.length > 0 ? (
          <div className="bg-white rounded-lg p-4">
            {renderChart()}
          </div>
        ) : (
          <div className="flex items-center justify-center h-48 bg-white rounded-lg">
            <div className="text-fal-gray-600">No data available</div>
          </div>
        )}
      </div>
    </div>
  )
}
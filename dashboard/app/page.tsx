'use client'

import { useState } from 'react'
import QueueVisualization from '../components/QueueVisualization'
import PerformanceMetrics from '../components/PerformanceMetrics'
import AIPerformanceBreakdown from '../components/AIPerformanceBreakdown'
import RealtimeChart from '../components/RealtimeChart'
import TestControlPanel from '../components/TestControlPanel'
import GenerationHistory from '../components/GenerationHistory'
import { useRealtimeWebSocket } from '../hooks/useRealtimeWebSocket'
import { startStream, stopStream } from '../utils/falApi'
import { Wifi, WifiOff, AlertCircle, RefreshCw, Square } from 'lucide-react'

export default function Dashboard() {
  const { metrics, history, isConnected, error, reconnect } = useRealtimeWebSocket()
  const [isStreaming, setIsStreaming] = useState(false)
  const [testResults, setTestResults] = useState<any>(null)
  
  // Detect if streaming is active based on metrics data
  const isActivelyStreaming = metrics?.video?.is_running || (metrics?.rtmp?.queue_size || 0) > 0

  const handleStartTest = async (config: any) => {
    try {
      setIsStreaming(true)
      console.log('🧪 Starting test with config:', config)
      
      const apiUrl = process.env.NEXT_PUBLIC_FAL_API_URL || 'http://localhost:8000'
      console.log('🧪 API URL:', apiUrl)
      
      const response = await startStream(apiUrl, config)
      
      console.log('🧪 Response received:', { 
        status: response.status, 
        statusText: response.statusText,
        ok: response.ok 
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      console.log('🧪 Response data:', result)
      
      setTestResults(result)
      
      if (result.status === 'error') {
        setIsStreaming(false)
        console.error('Test failed:', result.message)
      } else {
        console.log('✅ Test started successfully:', result)
      }
      
    } catch (error: any) {
      console.error('❌ Failed to start test:', error)
      setTestResults({ 
        status: 'error', 
        message: `Failed to start stream: ${error.message}`,
        error: error.toString()
      })
      setIsStreaming(false)
    }
  }

  const handleStopTest = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_FAL_API_URL || 'http://localhost:8000'
      console.log('🛑 Attempting to stop stream...', { apiUrl })
      
      const response = await stopStream(apiUrl)
      
      console.log('🛑 Response received:', { 
        status: response.status, 
        statusText: response.statusText,
        ok: response.ok 
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      console.log('🛑 Response data:', result)
      
      setTestResults(result)
      setIsStreaming(false)
      
      console.log('🛑 Test stopped successfully:', result)
      
    } catch (error: any) {
      console.error('❌ Failed to stop test:', error)
      setTestResults({ 
        status: 'error', 
        message: `Failed to stop stream: ${error.message}`,
        error: error.toString()
      })
      setIsStreaming(false)
    }
  }

  return (
    <div className="space-y-8">
      {/* FAL Status Bar */}
      <div className="fal-card">
        <div className="fal-card-content py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className={`connection-indicator ${
                isConnected ? 'connection-connected' : 'connection-disconnected'
              }`}>
                {isConnected ? (
                  <>
                    <Wifi className="w-4 h-4" />
                    <span>Connected to FAL App API</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-4 h-4" />
                    <span>Disconnected</span>
                  </>
                )}
              </div>
              
              {error && (
                <div className="flex items-center space-x-2 text-fal-red-600 text-sm">
                  <AlertCircle className="w-4 h-4" />
                  <span>{error}</span>
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-6">
              {/* Emergency Stop Button */}
              {isActivelyStreaming && (
                <button
                  onClick={handleStopTest}
                  className="bg-fal-red-500 hover:bg-fal-red-600 text-white font-medium px-4 py-2 rounded-lg transition-colors flex items-center space-x-2 text-sm"
                >
                  <Square className="w-4 h-4" />
                  <span>Stop Stream</span>
                </button>
              )}
              
              
              {/* Reconnect button if disconnected */}
              {!isConnected && (
                <button
                  onClick={reconnect}
                  className="bg-fal-yellow-500 hover:bg-fal-yellow-600 text-black font-medium px-3 py-1 rounded text-xs transition-colors"
                >
                  Reconnect
                </button>
              )}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full animate-pulse ${
                  isActivelyStreaming ? 'bg-fal-green-500' : 'bg-fal-gray-500'
                }`}></div>
                <span className="text-xs text-fal-gray-700 font-mono">
                  {isActivelyStreaming ? 'STREAMING' : 'IDLE'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Test Control Panel */}
      <TestControlPanel 
        onStartTest={handleStartTest}
        onStopTest={handleStopTest}
        isStreaming={isStreaming}
      />

      {/* Test Results */}
      {testResults && (
        <div className="fal-card">
          <div className="fal-card-header">
            <h3 className="text-lg font-semibold text-fal-gray-900">Test Results</h3>
          </div>
          <div className="fal-card-content">
            <div className="terminal">
              <pre className="text-sm text-fal-green-700">
                {JSON.stringify(testResults, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Queue Visualization */}
        <QueueVisualization data={metrics} />
        
        {/* Performance Metrics */}
        <PerformanceMetrics data={metrics} />
      </div>

      {/* Charts Section - Full Width Stacked */}
      <div className="space-y-6">
        {/* Queue Size Chart */}
        <RealtimeChart 
          data={history} 
          title="Queue Size Over Time" 
          type="queue"
        />
      </div>

      {/* AI Pipeline Performance - Full Width */}
      <div className="w-full">
        <AIPerformanceBreakdown data={metrics} />
      </div>

      {/* Generation History - Full Width */}
      <div className="w-full">
        <GenerationHistory generationHistory={metrics?.video?.generation_params_history} />
      </div>

     
    </div>
  )
}

'use client'

import { useState, useEffect, useCallback } from 'react'
import type { ComponentMetrics, RealtimeData } from '../types'

export function useRealtimeData(apiUrl: string = process.env.NEXT_PUBLIC_FAL_API_URL || 'http://localhost:8000') {
  const [data, setData] = useState<RealtimeData>({
    metrics: null,
    history: [],
    isConnected: false,
    error: null
  })

  const fetchMetrics = useCallback(async () => {
    try {
      const response = await fetch(`${apiUrl}/metrics`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
      })
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const metrics = await response.json()
      
      // Handle error responses
      if (metrics.error) {
        setData(prev => ({
          ...prev,
          isConnected: false,
          error: metrics.error
        }))
        return
      }
      
      // Use metrics directly - no complex transformation needed!
      const componentMetrics = metrics as ComponentMetrics
      
      setData(prev => {
        // Add to history
        const newHistory = [...prev.history, componentMetrics].slice(-300) // Keep last 5 minutes
        
        return {
          metrics: componentMetrics,
          history: newHistory,
          isConnected: true,
          error: null
        }
      })
      
    } catch (error) {
      console.error('Failed to fetch metrics:', error)
      setData(prev => ({
        ...prev,
        isConnected: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }))
    }
  }, [apiUrl])

  useEffect(() => {
    console.log('📡 Starting metrics polling every 1 second...')
    
    // Initial fetch
    fetchMetrics()

    // Set up polling every second
    const interval = setInterval(() => {
      fetchMetrics()
    }, 1000)

    return () => {
      console.log('📡 Stopping metrics polling...')
      clearInterval(interval)
    }
  }, [fetchMetrics])

  return data
}

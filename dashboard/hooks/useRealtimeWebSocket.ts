'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import type { ComponentMetrics, RealtimeData, WebSocketMessage } from '../types'

export function useRealtimeWebSocket(apiUrl: string = process.env.NEXT_PUBLIC_FAL_API_URL || 'http://localhost:8000') {
  const [data, setData] = useState<RealtimeData>({
    metrics: null,
    history: [],
    isConnected: false,
    error: null
  })
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.CONNECTING || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      // Convert HTTP URL to WebSocket URL
      const wsUrl = apiUrl.replace(/^http:\/\//, 'ws://').replace(/^https:\/\//, 'wss://') + '/metrics/ws'
      console.log('📡 Connecting to WebSocket:', wsUrl)
      
      wsRef.current = new WebSocket(wsUrl)
      
      wsRef.current.onopen = () => {
        console.log('📡 WebSocket connected')
        reconnectAttempts.current = 0
        setData(prev => ({
          ...prev,
          isConnected: true,
          error: null
        }))
      }
      
      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          
          if (message.type === 'metrics' && message.data) {
            const componentMetrics = message.data
            
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
          } else if (message.type === 'error') {
            console.error('WebSocket metrics error:', message.message)
            setData(prev => ({
              ...prev,
              error: message.message || 'Unknown WebSocket error'
            }))
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error, event.data)
        }
      }
      
      wsRef.current.onclose = () => {
        console.log('📡 WebSocket disconnected')
        setData(prev => ({
          ...prev,
          isConnected: false
        }))
        
        // Attempt to reconnect if not intentionally closed
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++
          console.log(`📡 Attempting to reconnect (${reconnectAttempts.current}/${maxReconnectAttempts})...`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000)) // Exponential backoff, max 10s
        } else {
          setData(prev => ({
            ...prev,
            error: 'Connection lost. Maximum reconnect attempts reached.'
          }))
        }
      }
      
      wsRef.current.onerror = (error) => {
        console.error('📡 WebSocket error:', error)
        setData(prev => ({
          ...prev,
          isConnected: false,
          error: 'WebSocket connection error'
        }))
      }
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setData(prev => ({
        ...prev,
        isConnected: false,
        error: error instanceof Error ? error.message : 'Connection failed'
      }))
    }
  }, [apiUrl])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    
    setData(prev => ({
      ...prev,
      isConnected: false
    }))
  }, [])

  useEffect(() => {
    connect()
    
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    ...data,
    reconnect: connect,
    disconnect
  }
}

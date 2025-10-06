'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import type { ComponentMetrics, RealtimeData, WebSocketMessage } from '../types'

const TOKEN_EXPIRATION_MS = 300; // 5 minutes

// Fetch temporary JWT token from fal.ai through our proxy
const fetchTemporaryToken = async (appName: string): Promise<string> => {
  const response = await fetch('/api/fal/proxy', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Fal-Target-Url': 'https://rest.alpha.fal.ai/tokens/',
    },
    body: JSON.stringify({
      allowed_apps: [appName],
      token_expiration: TOKEN_EXPIRATION_MS,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch token');
  }

  const token: string = await response.json();
  return token;
};

export function useRealtimeWebSocket(apiUrl: string = process.env.NEXT_PUBLIC_FAL_API_URL || 'http://localhost:8000') {
  const [data, setData] = useState<RealtimeData>({
    metrics: null,
    history: [],
    isConnected: false,
    error: null
  })
  
  const [token, setToken] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const tokenRefreshTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.CONNECTING || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    if (!token) {
      console.log('📡 No token available yet, waiting...')
      return
    }

    try {
      // Convert HTTP URL to WebSocket URL
      let wsUrl = apiUrl.replace(/^http:\/\//, 'ws://').replace(/^https:\/\//, 'wss://') + '/metrics/ws'
      
      // Add fal_jwt_token as query parameter
      wsUrl += `?fal_jwt_token=${encodeURIComponent(token)}`
      
      console.log('📡 Connecting to WebSocket with JWT token')
      
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
  }, [apiUrl, token])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    if (tokenRefreshTimeoutRef.current) {
      clearTimeout(tokenRefreshTimeoutRef.current)
      tokenRefreshTimeoutRef.current = null
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

  // Fetch and refresh token
  useEffect(() => {
    if (token) {
      return // Token already exists
    }

    // Extract app name from the API URL
    // Example: https://fal.run/alex-w67ic4anktp1/realtime-streaming -> realtime-streaming
    const appName = apiUrl.includes('fal.run') 
      ? apiUrl.split('/').pop() || 'realtime-streaming'
      : 'realtime-streaming'

    console.log('📡 Fetching temporary token for app:', appName)
    
    fetchTemporaryToken(appName)
      .then((newToken) => {
        console.log('📡 Token fetched successfully')
        setToken(newToken)
        
        // Schedule token refresh before it expires (90% of expiration time)
        tokenRefreshTimeoutRef.current = setTimeout(() => {
          console.log('📡 Token expiring, refreshing...')
          setToken(null) // Clear token to trigger refetch
        }, TOKEN_EXPIRATION_MS * 1000 * 0.9)
      })
      .catch((error) => {
        console.error('📡 Failed to fetch token:', error)
        setData(prev => ({
          ...prev,
          error: `Authentication failed: ${error.message}`
        }))
      })

    return () => {
      if (tokenRefreshTimeoutRef.current) {
        clearTimeout(tokenRefreshTimeoutRef.current)
        tokenRefreshTimeoutRef.current = null
      }
    }
  }, [token, apiUrl])

  useEffect(() => {
    // Only connect once we have a token
    if (token) {
      connect()
    }
    
    return () => {
      disconnect()
    }
  }, [connect, disconnect, token])

  return {
    ...data,
    reconnect: connect,
    disconnect
  }
}

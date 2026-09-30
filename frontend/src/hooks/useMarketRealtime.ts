import { useEffect, useState, useCallback, useRef } from 'react'

interface MarketUpdate {
  type: string
  indices?: Record<string, any>
  securities?: Array<any>
  data?: any
  timestamp?: string
}

export function useMarketRealtime() {
  const [data, setData] = useState<MarketUpdate | null>(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const ws = useRef<WebSocket | null>(null)
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null)

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      ws.current = new WebSocket(`${protocol}//localhost:5000/ws/market`)

      ws.current.onopen = () => {
        console.log('WebSocket connected')
        setConnected(true)
        setError(null)
      }

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          setData(message)
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }

      ws.current.onerror = (event) => {
        console.error('WebSocket error:', event)
        setError('Connection error')
        setConnected(false)
      }

      ws.current.onclose = () => {
        console.log('WebSocket disconnected')
        setConnected(false)
        // Attempt to reconnect after 3 seconds
        reconnectTimeout.current = setTimeout(() => {
          connect()
        }, 3000)
      }
    } catch (e) {
      console.error('Failed to create WebSocket:', e)
      setError('Failed to connect')
    }
  }, [])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current)
      }
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [connect])

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message))
    }
  }, [])

  return {
    data,
    connected,
    error,
    sendMessage,
  }
}

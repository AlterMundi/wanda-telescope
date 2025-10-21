"use client"

import { useEffect, useRef, useState } from "react"
import { io, type Socket } from "socket.io-client"

// Use empty string for same-origin, or explicit URL if provided
// Note: Empty string means socket.io will use the current page's origin
const WS_BASE_ENV = process.env.NEXT_PUBLIC_WS_URL
const WS_BASE = (WS_BASE_ENV !== undefined && WS_BASE_ENV !== "" ? WS_BASE_ENV : "").replace(/\/$/, "")

// Debug logging to verify configuration (remove in production)
if (typeof window !== "undefined" && WS_BASE) {
  console.log("WebSocket: Using explicit base URL:", WS_BASE)
} else if (typeof window !== "undefined") {
  console.log("WebSocket: Using same-origin (current page URL)")
}

const MAX_RETRY_DELAY_MS = 30_000

function calculateBackoffDelay(attempt: number) {
  const baseDelay = Math.min(1000 * 2 ** attempt, MAX_RETRY_DELAY_MS)
  const jitter = Math.random() * 500
  return baseDelay + jitter
}

interface ConnectionState {
  isConnected: boolean
  isReconnecting: boolean
  connectionAttempts: number
}

const initialState: ConnectionState = {
  isConnected: false,
  isReconnecting: false,
  connectionAttempts: 0,
}

export function useWebSocket(namespace: string) {
  const socketRef = useRef<Socket | null>(null)
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const attemptsRef = useRef(0)
  const mountedRef = useRef(false)
  const [state, setState] = useState<ConnectionState>(initialState)

  useEffect(() => {
    mountedRef.current = true

    if (!namespace) {
      setState(initialState)
      return () => {
        mountedRef.current = false
      }
    }

    const url = `${WS_BASE}${namespace}`

    const clearRetryTimeout = () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current)
        retryTimeoutRef.current = null
      }
    }

    const cleanupSocket = () => {
      if (socketRef.current) {
        socketRef.current.removeAllListeners()
        socketRef.current.disconnect()
        socketRef.current = null
      }
    }

    const scheduleReconnect = () => {
      if (!mountedRef.current) {
        return
      }

      attemptsRef.current += 1
      const attempts = attemptsRef.current
      const delay = calculateBackoffDelay(attempts)

      setState({
        isConnected: false,
        isReconnecting: true,
        connectionAttempts: attempts,
      })

      clearRetryTimeout()
      retryTimeoutRef.current = setTimeout(() => {
        retryTimeoutRef.current = null
        connectSocket()
      }, delay)
    }

    const handleError = () => {
      if (!mountedRef.current) {
        return
      }

      setState((prev) => ({
        ...prev,
        isConnected: false,
      }))

      scheduleReconnect()
    }

    const connectSocket = () => {
      if (!mountedRef.current) {
        return
      }

      cleanupSocket()

      const socket = io(url, {
        transports: ["websocket"],
        autoConnect: true,
        reconnection: false,
        timeout: 5000,
      })

      socketRef.current = socket

      socket.on("connect", () => {
        if (!mountedRef.current) {
          return
        }

        attemptsRef.current = 0
        setState({
          isConnected: true,
          isReconnecting: false,
          connectionAttempts: 0,
        })
      })

      socket.on("disconnect", (reason: Socket.DisconnectReason) => {
        if (!mountedRef.current) {
          return
        }

        setState((prev) => ({
          ...prev,
          isConnected: false,
        }))

        if (reason !== "io client disconnect") {
          scheduleReconnect()
        }
      })

      socket.on("connect_error", handleError)
      socket.on("error", handleError)
    }

    connectSocket()

    return () => {
      mountedRef.current = false
      clearRetryTimeout()
      cleanupSocket()
      attemptsRef.current = 0
      setState(initialState)
    }
  }, [namespace])

  return {
    socket: socketRef.current,
    ...state,
  }
}

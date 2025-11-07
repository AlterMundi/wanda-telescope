"use client"

import { useEffect, useRef, useState } from "react"
import { io, type Socket } from "socket.io-client"

// Derive WebSocket URL from API URL if WS_URL not explicitly set
// In dev mode, API runs on port 5000, so WS should connect there too
const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "/api").replace(/\/$/, "")
const WS_BASE_ENV = process.env.NEXT_PUBLIC_WS_URL

let WS_BASE = ""
if (WS_BASE_ENV !== undefined && WS_BASE_ENV !== "") {
  WS_BASE = WS_BASE_ENV.replace(/\/$/, "")
} else if (API_BASE.startsWith("http")) {
  // If API_BASE is a full URL (dev mode), use it for WebSocket
  WS_BASE = API_BASE.replace(/\/api$/, "")
} else {
  // Check if we're in dev mode by detecting if we're accessing via local IP/localhost
  // In dev mode without explicit API URL, default to port 5000
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname
    const isDevMode = hostname === "localhost" || 
                      hostname === "127.0.0.1" || 
                      hostname.startsWith("192.168.") ||
                      hostname.startsWith("10.") ||
                      hostname.startsWith("172.")
    
    if (isDevMode && process.env.NODE_ENV !== "production") {
      // In dev mode, use the same hostname but port 5000
      const protocol = window.location.protocol === "https:" ? "https:" : "http:"
      WS_BASE = `${protocol}//${hostname}:5000`
    } else {
      // Same-origin (production mode with Nginx proxy)
      WS_BASE = ""
    }
  } else {
    // Server-side rendering - same-origin
    WS_BASE = ""
  }
}

// Debug logging to verify configuration
if (typeof window !== "undefined" && WS_BASE) {
  console.log("WebSocket: Using base URL:", WS_BASE)
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

    // Calculate WebSocket URL dynamically (in case window.location changes)
    let wsBase = WS_BASE
    if (!wsBase && typeof window !== "undefined") {
      const hostname = window.location.hostname
      const port = window.location.port
      // Detect dev mode: localhost, local IPs, or non-standard ports (3000 = Next.js dev)
      const isDevMode = hostname === "localhost" || 
                        hostname === "127.0.0.1" || 
                        hostname.startsWith("192.168.") ||
                        hostname.startsWith("10.") ||
                        hostname.startsWith("172.") ||
                        port === "3000" ||
                        port === ""
      
      // In dev mode, always use port 5000 for WebSocket (backend port)
      if (isDevMode) {
        const protocol = window.location.protocol === "https:" ? "https:" : "http:"
        wsBase = `${protocol}//${hostname}:5000`
        console.log(`WebSocket: Detected dev mode, connecting to ${wsBase}`)
      }
    }

    const url = `${wsBase}${namespace}`

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

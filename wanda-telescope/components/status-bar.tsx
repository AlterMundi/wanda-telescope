"use client"

import { useEffect, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Wifi, HardDrive, Thermometer } from "lucide-react"
import { useWebSocket } from "@/lib/hooks/useWebSocket"

interface StatusState {
  status: string
  exposure_seconds?: number
  iso?: number
}

interface CameraStatusPayload {
  capture_status?: string
  exposure_seconds?: number
  iso?: number
}

interface CaptureEventPayload {
  capture_status?: string
  error?: string
}

export function StatusBar() {
  const [cameraStatus, setCameraStatus] = useState<StatusState>({ status: "Ready" })
  const [isCapturing, setIsCapturing] = useState(false)
  const { socket, isConnected } = useWebSocket("/ws/camera")

  useEffect(() => {
    if (!socket) return

    const handleStatus = (payload: CameraStatusPayload) => {
      setCameraStatus({
        status: payload.capture_status || "Ready",
        exposure_seconds: payload.exposure_seconds,
        iso: payload.iso,
      })
    }

    const handleCaptureStart = () => {
      setIsCapturing(true)
      setCameraStatus((prev) => ({ ...prev, status: "Capturing" }))
    }

    const handleCaptureComplete = (payload: CaptureEventPayload) => {
      setIsCapturing(false)
      setCameraStatus((prev) => ({ ...prev, status: payload.capture_status || "Completed" }))
    }

    const handleCaptureError = (payload: CaptureEventPayload) => {
      setIsCapturing(false)
      setCameraStatus({ status: `Error: ${payload.error ?? "unknown"}` })
    }

    socket.on("status", handleStatus)
    socket.on("capture_start", handleCaptureStart)
    socket.on("capture_complete", handleCaptureComplete)
    socket.on("capture_error", handleCaptureError)

    return () => {
      socket.off("status", handleStatus)
      socket.off("capture_start", handleCaptureStart)
      socket.off("capture_complete", handleCaptureComplete)
      socket.off("capture_error", handleCaptureError)
    }
  }, [socket])

  return (
    <footer className="flex items-center justify-between border-t border-border bg-card px-6 py-2 text-xs">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Wifi className={`h-3 w-3 ${isConnected ? "text-green-500" : "text-muted-foreground"}`} />
          <span className="text-muted-foreground">{isConnected ? "Socket Connected" : "Socket Offline"}</span>
        </div>
        <div className="flex items-center gap-2">
          <HardDrive className="h-3 w-3 text-muted-foreground" />
          <span className="text-muted-foreground">Exposure: {cameraStatus.exposure_seconds ?? "-"}s</span>
        </div>
        <div className="flex items-center gap-2">
          <Thermometer className="h-3 w-3 text-muted-foreground" />
          <span className="text-muted-foreground">ISO: {cameraStatus.iso ?? "-"}</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {isCapturing && (
          <Badge variant="default" className="animate-pulse">
            Recording
          </Badge>
        )}
        <span className="text-muted-foreground">Camera Status: {cameraStatus.status}</span>
      </div>
    </footer>
  )
}

"use client"

import { useEffect, useMemo, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Camera, Wifi, HardDrive, Activity } from "lucide-react"
import { useWebSocket } from "@/lib/hooks/useWebSocket"
import type { CameraStatus } from "@/lib/api-client"

interface MountStatusPayload {
  status?: string
  tracking?: boolean
  direction?: boolean
  speed?: number
}

interface SessionStatusPayload {
  active?: boolean
  name?: string
  captured_images?: number
  total_images?: number
  remaining_time?: number
}

interface StatusState {
  camera: Partial<CameraStatus>
  mount: MountStatusPayload
  session: SessionStatusPayload
}

const initialState: StatusState = {
  camera: {
    capture_status: "Idle",
    exposure_seconds: undefined,
    iso: undefined,
  },
  mount: {
    status: "Idle",
    tracking: false,
  },
  session: {
    active: false,
    captured_images: 0,
    total_images: 0,
  },
}

function formatSession(session: SessionStatusPayload) {
  if (!session.active) {
    return "No active session"
  }

  const progress = session.total_images
    ? `${session.captured_images ?? 0}/${session.total_images}`
    : `${session.captured_images ?? 0}`

  return `${session.name || "Session"} • ${progress}`
}

export function StatusBar() {
  const [status, setStatus] = useState(initialState)
  const cameraSocket = useWebSocket("/ws/camera")
  const mountSocket = useWebSocket("/ws/mount")
  const sessionSocket = useWebSocket("/ws/session")

  useEffect(() => {
    const { socket } = cameraSocket
    if (!socket) return

    const handleStatus = (payload: Partial<CameraStatus>) => {
      setStatus((prev) => ({
        ...prev,
        camera: {
          ...prev.camera,
          ...payload,
        },
      }))
    }

    const handleCaptureStart = () => {
      setStatus((prev) => ({
        ...prev,
        camera: {
          ...prev.camera,
          capture_status: "Capturing",
          recording: true,
        },
      }))
    }

    const handleCaptureComplete = (payload: { capture_status?: string }) => {
      setStatus((prev) => ({
        ...prev,
        camera: {
          ...prev.camera,
          capture_status: payload.capture_status || "Completed",
          recording: false,
        },
      }))
    }

    const handleCaptureError = (payload: { error?: string }) => {
      setStatus((prev) => ({
        ...prev,
        camera: {
          ...prev.camera,
          capture_status: `Error: ${payload.error ?? "Unknown"}`,
          recording: false,
        },
      }))
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
  }, [cameraSocket.socket])

  useEffect(() => {
    const { socket } = mountSocket
    if (!socket) return

    const handleMountUpdate = (payload: MountStatusPayload) => {
      setStatus((prev) => ({
        ...prev,
        mount: {
          ...prev.mount,
          ...payload,
        },
      }))
    }

    socket.on("status", handleMountUpdate)
    socket.on("tracking_start", handleMountUpdate)
    socket.on("tracking_stop", handleMountUpdate)
    socket.on("mount_error", handleMountUpdate)

    return () => {
      socket.off("status", handleMountUpdate)
      socket.off("tracking_start", handleMountUpdate)
      socket.off("tracking_stop", handleMountUpdate)
      socket.off("mount_error", handleMountUpdate)
    }
  }, [mountSocket.socket])

  useEffect(() => {
    const { socket } = sessionSocket
    if (!socket) return

    const handleSessionUpdate = (payload: SessionStatusPayload) => {
      setStatus((prev) => ({
        ...prev,
        session: {
          ...prev.session,
          ...payload,
        },
      }))
    }

    socket.on("status", handleSessionUpdate)
    socket.on("session_start", () => handleSessionUpdate({ active: true }))
    socket.on("session_progress", handleSessionUpdate)
    socket.on("session_complete", () => handleSessionUpdate({ active: false }))
    socket.on("session_error", handleSessionUpdate)

    return () => {
      socket.off("status", handleSessionUpdate)
      socket.off("session_start", handleSessionUpdate)
      socket.off("session_progress", handleSessionUpdate)
      socket.off("session_complete", handleSessionUpdate)
      socket.off("session_error", handleSessionUpdate)
    }
  }, [sessionSocket.socket])

  const cameraConnectionLabel = useMemo(() => {
    if (cameraSocket.isConnected) return "Connected"
    if (cameraSocket.isReconnecting) return "Reconnecting"
    return "Offline"
  }, [cameraSocket.isConnected, cameraSocket.isReconnecting])

  const mountConnectionLabel = useMemo(() => {
    if (mountSocket.isConnected) {
      return status.mount.tracking ? "Tracking" : "Idle"
    }
    if (mountSocket.isReconnecting) return "Reconnecting"
    return "Offline"
  }, [mountSocket.isConnected, mountSocket.isReconnecting, status.mount.tracking])

  const sessionConnectionLabel = useMemo(() => {
    if (sessionSocket.isConnected) return status.session.active ? "Running" : "Monitoring"
    if (sessionSocket.isReconnecting) return "Reconnecting"
    return "Offline"
  }, [sessionSocket.isConnected, sessionSocket.isReconnecting, status.session.active])

  return (
    <footer className="flex flex-col border-t border-border bg-card/80 px-6 py-2 text-xs text-muted-foreground md:flex-row md:items-center md:justify-between">
      <div className="flex flex-1 flex-wrap gap-x-6 gap-y-2">
        <div className="flex items-center gap-2">
          <Wifi className={`h-3 w-3 ${cameraSocket.isConnected ? "text-green-500" : "text-muted-foreground"}`} />
          <span>Camera: {cameraConnectionLabel}</span>
          <Badge variant="outline" className="ml-2">
            {status.camera.capture_status}
          </Badge>
        </div>

        <div className="flex items-center gap-2">
          <Camera className="h-3 w-3 text-muted-foreground" />
          <span>
            Exp: {typeof status.camera.exposure_seconds === "number" ? status.camera.exposure_seconds.toFixed(1) : "-"}s
          </span>
          <span>ISO: {typeof status.camera.iso === "number" ? status.camera.iso : "-"}</span>
        </div>

        <div className="flex items-center gap-2">
          <HardDrive className="h-3 w-3 text-muted-foreground" />
          <span>Mount: {mountConnectionLabel}</span>
          {status.mount.tracking && <Badge variant="secondary">Tracking</Badge>}
        </div>

        <div className="flex items-center gap-2">
          <Activity className="h-3 w-3 text-muted-foreground" />
          <span>{formatSession(status.session)}</span>
        </div>
      </div>

      <div className="mt-2 flex items-center gap-3 md:mt-0">
        <span>Session: {sessionConnectionLabel}</span>
        {status.camera.recording && (
          <Badge variant="default" className="animate-pulse">
            Recording
          </Badge>
        )}
      </div>
    </footer>
  )
}

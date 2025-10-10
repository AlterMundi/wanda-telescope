"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import {
  ApiClientError,
  getMountStatus,
  sendMountAction,
  type MountStatus,
} from "@/lib/api-client"
import { useWebSocket } from "@/lib/hooks/useWebSocket"
import { Compass, RotateCcw, RotateCw, RefreshCw } from "lucide-react"

type Direction = "cw" | "ccw"

const SPEED_MIN = 0.1
const SPEED_MAX = 3.0

function directionFromPayload(value: boolean | undefined): Direction {
  if (value === false) {
    return "ccw"
  }
  return "cw"
}

function toDirectionLabel(direction: Direction) {
  return direction === "cw" ? "Clockwise" : "Counter-Clockwise"
}

export function MountControls() {
  const [status, setStatus] = useState<MountStatus | null>(null)
  const [direction, setDirection] = useState<Direction>("cw")
  const [speed, setSpeed] = useState(1.0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const { socket, isConnected, isReconnecting } = useWebSocket("/ws/mount")

  const connectionLabel = useMemo(() => {
    if (isConnected) return "Connected"
    if (isReconnecting) return "Reconnecting"
    return "Offline"
  }, [isConnected, isReconnecting])

  const syncStatus = useCallback(async () => {
    setIsRefreshing(true)
    setErrorMessage(null)
    try {
      const data = await getMountStatus()
      setStatus(data)
      if (typeof data.direction === "boolean") {
        setDirection(directionFromPayload(data.direction))
      }
      if (typeof data.speed === "number" && !Number.isNaN(data.speed)) {
        setSpeed(Number.parseFloat(data.speed.toFixed(2)))
      }
    } catch (error) {
      console.error("Failed to fetch mount status", error)
      const message =
        error instanceof ApiClientError ? error.message : "Unable to fetch mount status."
      setErrorMessage(message)
    } finally {
      setIsRefreshing(false)
    }
  }, [])

  useEffect(() => {
    syncStatus()
  }, [syncStatus])

  useEffect(() => {
    if (!socket) return

    const handleUpdate = (payload: Partial<MountStatus>) => {
      setStatus((prev) => ({
        status: payload.status ?? prev?.status ?? "Unknown",
        tracking: payload.tracking ?? prev?.tracking ?? false,
        direction: payload.direction ?? prev?.direction,
        speed: payload.speed ?? prev?.speed,
      }))

      if (typeof payload.direction === "boolean") {
        setDirection(directionFromPayload(payload.direction))
      }
      if (typeof payload.speed === "number" && !Number.isNaN(payload.speed)) {
        setSpeed(Number.parseFloat(payload.speed.toFixed(2)))
      }
    }

    const handleError = (payload: { error?: string }) => {
      setErrorMessage(payload.error ?? "Mount error")
    }

    socket.on("status", handleUpdate)
    socket.on("tracking_start", handleUpdate)
    socket.on("tracking_stop", handleUpdate)
    socket.on("mount_error", handleError)

    return () => {
      socket.off("status", handleUpdate)
      socket.off("tracking_start", handleUpdate)
      socket.off("tracking_stop", handleUpdate)
      socket.off("mount_error", handleError)
    }
  }, [socket])

  const handleStartTracking = useCallback(async () => {
    setIsSubmitting(true)
    setErrorMessage(null)
    try {
      await sendMountAction("start", {
        speed,
        direction,
      })
    } catch (error) {
      console.error("Failed to start tracking", error)
      const message = error instanceof ApiClientError ? error.message : "Failed to start tracking."
      setErrorMessage(message)
    } finally {
      setIsSubmitting(false)
    }
  }, [direction, speed])

  const handleStopTracking = useCallback(async () => {
    setIsSubmitting(true)
    setErrorMessage(null)
    try {
      await sendMountAction("stop")
    } catch (error) {
      console.error("Failed to stop tracking", error)
      const message = error instanceof ApiClientError ? error.message : "Failed to stop tracking."
      setErrorMessage(message)
    } finally {
      setIsSubmitting(false)
    }
  }, [])

  const tracking = status?.tracking ?? false
  const displaySpeed = status?.speed ?? speed
  const displayDirection = direction

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Mount Tracking</CardTitle>
          <CardDescription>
            Control equatorial mount motion. Connection status: {connectionLabel}.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <Badge variant={tracking ? "default" : "outline"}>
              {tracking ? "Tracking" : "Idle"}
            </Badge>
            <span>Reported speed: {displaySpeed?.toFixed?.(2) ?? "-"}x</span>
            <span>Direction: {toDirectionLabel(displayDirection)}</span>
            {status?.status && <span>State: {status.status}</span>}
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-3">
              <Label className="text-sm">Tracking Speed</Label>
              <Slider
                value={[speed]}
                min={SPEED_MIN}
                max={SPEED_MAX}
                step={0.1}
                onValueChange={(value) => setSpeed(Number(value[0].toFixed(2)))}
              />
              <p className="text-xs text-muted-foreground">Current: {speed.toFixed(2)}x sidereal</p>
            </div>

            <div className="space-y-3">
              <Label className="text-sm">Direction</Label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant={direction === "cw" ? "default" : "outline"}
                  onClick={() => setDirection("cw")}
                  className="flex-1"
                >
                  <RotateCw className="mr-2 h-4 w-4" /> Clockwise
                </Button>
                <Button
                  type="button"
                  variant={direction === "ccw" ? "default" : "outline"}
                  onClick={() => setDirection("ccw")}
                  className="flex-1"
                >
                  <RotateCcw className="mr-2 h-4 w-4" /> Counter-Clockwise
                </Button>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button onClick={handleStartTracking} disabled={isSubmitting || !isConnected}>
              <Compass className="mr-2 h-4 w-4" /> Start Tracking
            </Button>
            <Button
              variant="outline"
              onClick={handleStopTracking}
              disabled={isSubmitting || !tracking}
            >
              Stop
            </Button>
            <Button
              variant="ghost"
              onClick={syncStatus}
              disabled={isRefreshing}
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>

          {errorMessage && <p className="text-sm text-destructive">{errorMessage}</p>}
        </CardContent>
      </Card>
    </div>
  )
}


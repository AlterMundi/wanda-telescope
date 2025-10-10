"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import {
  ApiClientError,
  getSessionStatus,
  startSession,
  stopSession,
  type SessionStatus,
} from "@/lib/api-client"
import { useWebSocket } from "@/lib/hooks/useWebSocket"
import { Clock, Play, Square, CalendarCheck, RefreshCw } from "lucide-react"

interface SessionFormState {
  name: string
  totalImages: number
  enableTracking: boolean
  useCurrentSettings: boolean
  totalTimeHours: number
}

const DEFAULT_FORM: SessionFormState = {
  name: "Night Session",
  totalImages: 10,
  enableTracking: true,
  useCurrentSettings: true,
  totalTimeHours: 1,
}

function formatRemainingTime(hours?: number) {
  if (hours == null || Number.isNaN(hours)) return "-"
  const totalMinutes = Math.max(0, Math.floor(hours * 60))
  const h = Math.floor(totalMinutes / 60)
  const m = totalMinutes % 60
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

function formatProgress(status: SessionStatus | null) {
  if (!status) return "No session"
  return `${status.captured_images}/${status.total_images}`
}

export function SessionControls() {
  const [status, setStatus] = useState<SessionStatus | null>(null)
  const [form, setForm] = useState<SessionFormState>(DEFAULT_FORM)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const { socket, isConnected, isReconnecting } = useWebSocket("/ws/session")

  const connectionLabel = useMemo(() => {
    if (isConnected) return "Connected"
    if (isReconnecting) return "Reconnecting"
    return "Offline"
  }, [isConnected, isReconnecting])

  const syncStatus = useCallback(async () => {
    setIsRefreshing(true)
    setErrorMessage(null)
    try {
      const data = await getSessionStatus()
      setStatus(data)
    } catch (error) {
      console.error("Failed to load session status", error)
      const message =
        error instanceof ApiClientError ? error.message : "Unable to load session status."
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

    const handleStatus = (payload: SessionStatus) => {
      setStatus(payload)
    }

    const handleEvent = (payload: Partial<SessionStatus>) => {
      setStatus((prev) => ({
        ...(prev ?? {
          active: false,
          name: "",
          total_images: 0,
          captured_images: 0,
          remaining_time: 0,
        }),
        ...payload,
      }))
    }

    socket.on("status", handleStatus)
    socket.on("session_start", () => handleEvent({ active: true }))
    socket.on("session_progress", handleEvent)
    socket.on("session_complete", () => handleEvent({ active: false }))
    socket.on("session_stop", () => handleEvent({ active: false }))
    const handleError = (payload: { error?: string }) => {
      setErrorMessage(payload.error ?? "Session error")
      handleEvent({ active: false })
    }

    socket.on("session_error", handleError)

    return () => {
      socket.off("status", handleStatus)
      socket.off("session_start", handleEvent)
      socket.off("session_progress", handleEvent)
      socket.off("session_complete", handleEvent)
      socket.off("session_stop", handleEvent)
      socket.off("session_error", handleError)
    }
  }, [socket])

  const handleInputChange = (field: keyof SessionFormState) => (value: string | number | boolean) => {
    setForm((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  const handleStartSession = useCallback(async () => {
    setIsSubmitting(true)
    setErrorMessage(null)
    try {
      await startSession({
        name: form.name,
        total_images: form.totalImages,
        enable_tracking: form.enableTracking,
        use_current_settings: form.useCurrentSettings,
        total_time_hours: form.totalTimeHours,
      })
    } catch (error) {
      console.error("Failed to start session", error)
      const message = error instanceof ApiClientError ? error.message : "Failed to start session."
      setErrorMessage(message)
    } finally {
      setIsSubmitting(false)
    }
  }, [form])

  const handleStopSession = useCallback(async () => {
    setIsSubmitting(true)
    setErrorMessage(null)
    try {
      await stopSession()
    } catch (error) {
      console.error("Failed to stop session", error)
      const message = error instanceof ApiClientError ? error.message : "Failed to stop session."
      setErrorMessage(message)
    } finally {
      setIsSubmitting(false)
    }
  }, [])

  const active = status?.active ?? false
  const remainingTime = status?.remaining_time

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Capture Sessions</CardTitle>
          <CardDescription>
            Automate multi-image captures. Connection status: {connectionLabel}.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <Badge variant={active ? "default" : "outline"}>{active ? "Running" : "Idle"}</Badge>
            <span>Name: {status?.name || "n/a"}</span>
            <span>Progress: {formatProgress(status ?? null)}</span>
            <span>Time remaining: {formatRemainingTime(remainingTime)}</span>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-3">
              <Label className="text-sm">Session Name</Label>
              <Input
                value={form.name}
                onChange={(event) => handleInputChange("name")(event.target.value)}
                placeholder="Deep Sky Marathon"
                maxLength={64}
              />
            </div>

            <div className="space-y-3">
              <Label className="text-sm">Images to Capture</Label>
              <Input
                type="number"
                min={1}
                max={999}
                value={form.totalImages}
                onChange={(event) => handleInputChange("totalImages")(Number.parseInt(event.target.value))}
              />
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-3">
              <Label className="text-sm">Total Duration (hours)</Label>
              <Slider
                value={[form.totalTimeHours]}
                min={0.5}
                max={12}
                step={0.5}
                onValueChange={(value) => handleInputChange("totalTimeHours")(Number(value[0].toFixed(1)))}
              />
              <p className="text-xs text-muted-foreground">Planned runtime: {form.totalTimeHours.toFixed(1)} hours</p>
            </div>

            <div className="space-y-3">
              <Label className="text-sm">Notes</Label>
              <textarea
                placeholder="Objects, filters, or instructions"
                rows={3}
                className="w-full resize-none rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              />
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <Button
              onClick={() => handleInputChange("useCurrentSettings")(!form.useCurrentSettings)}
              variant={form.useCurrentSettings ? "default" : "outline"}
              type="button"
            >
              Use Current Camera Settings
            </Button>
            <Button
              onClick={() => handleInputChange("enableTracking")(!form.enableTracking)}
              variant={form.enableTracking ? "default" : "outline"}
              type="button"
            >
              Tracking: {form.enableTracking ? "Enabled" : "Disabled"}
            </Button>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button onClick={handleStartSession} disabled={isSubmitting || active || !isConnected}>
              <Play className="mr-2 h-4 w-4" /> Start Session
            </Button>
            <Button
              variant="outline"
              onClick={handleStopSession}
              disabled={isSubmitting || !active}
            >
              <Square className="mr-2 h-4 w-4" /> Stop Session
            </Button>
            <Button variant="ghost" onClick={syncStatus} disabled={isRefreshing}>
              <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} /> Refresh
            </Button>
          </div>

          {errorMessage && <p className="text-sm text-destructive">{errorMessage}</p>}

          <div className="rounded-md border border-border bg-muted/40 p-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              <span>Last update: {new Date().toLocaleTimeString()}</span>
            </div>
            <div className="mt-2 flex items-center gap-2">
              <CalendarCheck className="h-4 w-4" />
              <span>
                Next milestone: {status?.active ? `${status.captured_images + 1}/${status.total_images}` : "n/a"}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}


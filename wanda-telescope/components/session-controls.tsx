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
  getSessionConfig,
  saveSessionConfig,
  getCameraStatus,
  type SessionStatus,
  type SessionConfig,
} from "@/lib/api-client"
import { useWebSocket } from "@/lib/hooks/useWebSocket"
import { Clock, Play, Square, CalendarCheck, RefreshCw, Save } from "lucide-react"

interface SessionFormState {
  name: string
  totalImages: number
  enableTracking: boolean
  useCurrentSettings: boolean
  sessionMode: "rapid" | "timed"
  totalTimeHours: number
}

const DEFAULT_FORM: SessionFormState = {
  name: "Night Session",
  totalImages: 10,
  enableTracking: true,
  useCurrentSettings: true,
  sessionMode: "timed",
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
  const [isSaving, setIsSaving] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [validationWarning, setValidationWarning] = useState<string | null>(null)
  const [cameraExposure, setCameraExposure] = useState<number>(1.0)
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
    loadSessionConfig()
    loadCameraExposure()
  }, [])

  const loadSessionConfig = useCallback(async () => {
    try {
      const config = await getSessionConfig()
      if (config && Object.keys(config).length > 0) {
        setForm({
          name: config.name || DEFAULT_FORM.name,
          totalImages: config.totalImages || DEFAULT_FORM.totalImages,
          enableTracking: config.enableTracking ?? DEFAULT_FORM.enableTracking,
          useCurrentSettings: config.useCurrentSettings ?? DEFAULT_FORM.useCurrentSettings,
          sessionMode: config.sessionMode || DEFAULT_FORM.sessionMode,
          totalTimeHours: config.totalTimeHours || DEFAULT_FORM.totalTimeHours,
        })
      }
    } catch {
      // Config doesn't exist yet, use defaults
      console.debug("No saved session config found")
    }
  }, [])

  const loadCameraExposure = useCallback(async () => {
    try {
      const cameraStatus = await getCameraStatus()
      if (typeof cameraStatus.exposure_seconds === "number") {
        setCameraExposure(cameraStatus.exposure_seconds)
      }
    } catch (error) {
      console.error("Failed to load camera exposure", error)
    }
  }, [])

  const validateTimedMode = useCallback(() => {
    if (form.sessionMode === "timed") {
      const totalDurationSeconds = form.totalTimeHours * 3600
      const minRequiredSeconds = form.totalImages * cameraExposure
      if (totalDurationSeconds < minRequiredSeconds) {
        const minHours = minRequiredSeconds / 3600
        setValidationWarning(
          `Duration too short! Minimum ${minHours.toFixed(2)} hours required for ${form.totalImages} images with ${cameraExposure.toFixed(1)}s exposure each.`
        )
        return false
      }
    }
    setValidationWarning(null)
    return true
  }, [form.sessionMode, form.totalTimeHours, form.totalImages, cameraExposure])

  useEffect(() => {
    validateTimedMode()
  }, [validateTimedMode])

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
    socket.on("session_complete", (payload: Partial<SessionStatus>) => {
      handleEvent({ active: false, ...payload })
      // Also refresh status to get final state
      syncStatus()
    })
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

  const handleSaveConfig = useCallback(async () => {
    setIsSaving(true)
    setErrorMessage(null)
    try {
      const config: SessionConfig = {
        name: form.name,
        totalImages: form.totalImages,
        enableTracking: form.enableTracking,
        useCurrentSettings: form.useCurrentSettings,
        sessionMode: form.sessionMode,
        totalTimeHours: form.sessionMode === "timed" ? form.totalTimeHours : null,
      }
      await saveSessionConfig(config)
      // Show success briefly (could use a toast library if available)
      setErrorMessage(null)
    } catch (error) {
      console.error("Failed to save session config", error)
      const message = error instanceof ApiClientError ? error.message : "Failed to save session config."
      setErrorMessage(message)
    } finally {
      setIsSaving(false)
    }
  }, [form])

  const handleStartSession = useCallback(async () => {
    if (!validateTimedMode()) {
      setErrorMessage("Please fix validation errors before starting session.")
      return
    }

    setIsSubmitting(true)
    setErrorMessage(null)
    try {
      await startSession({
        name: form.name,
        total_images: form.totalImages,
        enable_tracking: form.enableTracking,
        use_current_settings: form.useCurrentSettings,
        total_time_hours: form.sessionMode === "rapid" ? null : form.totalTimeHours,
      })
    } catch (error) {
      console.error("Failed to start session", error)
      const message = error instanceof ApiClientError ? error.message : "Failed to start session."
      setErrorMessage(message)
    } finally {
      setIsSubmitting(false)
    }
  }, [form, validateTimedMode])

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

          <div className="space-y-3">
            <Label className="text-sm">Session Mode</Label>
            <div className="flex gap-2">
              <Button
                type="button"
                variant={form.sessionMode === "rapid" ? "default" : "outline"}
                onClick={() => handleInputChange("sessionMode")("rapid")}
                className="flex-1"
              >
                Rapid Mode
              </Button>
              <Button
                type="button"
                variant={form.sessionMode === "timed" ? "default" : "outline"}
                onClick={() => handleInputChange("sessionMode")("timed")}
                className="flex-1"
              >
                Timed Mode
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              {form.sessionMode === "rapid"
                ? "Captures images as fast as possible"
                : "Distributes images evenly over specified duration"}
            </p>
          </div>

          {form.sessionMode === "timed" && (
            <div className="space-y-3">
              <Label className="text-sm">Total Duration (hours)</Label>
              <Slider
                value={[form.totalTimeHours]}
                min={0.1}
                max={12}
                step={0.1}
                onValueChange={(value) => handleInputChange("totalTimeHours")(Number(value[0].toFixed(1)))}
              />
              <p className="text-xs text-muted-foreground">Planned runtime: {form.totalTimeHours.toFixed(1)} hours</p>
              {validationWarning && (
                <p className="text-xs text-destructive">{validationWarning}</p>
              )}
            </div>
          )}

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
            <Button onClick={handleStartSession} disabled={isSubmitting || active || !isConnected || !!validationWarning}>
              <Play className="mr-2 h-4 w-4" /> Start Session
            </Button>
            <Button
              variant="outline"
              onClick={handleStopSession}
              disabled={isSubmitting || !active}
            >
              <Square className="mr-2 h-4 w-4" /> Stop Session
            </Button>
            <Button
              variant="secondary"
              onClick={handleSaveConfig}
              disabled={isSaving}
            >
              <Save className={`mr-2 h-4 w-4 ${isSaving ? "animate-spin" : ""}`} /> Save Settings
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


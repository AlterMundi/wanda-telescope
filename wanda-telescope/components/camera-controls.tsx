"use client"

import { useCallback, useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { ChevronDown } from "lucide-react"
import {
  getCameraStatus,
  triggerCapture,
  updateCameraSettings,
} from "@/lib/api-client"
import { useWebSocket } from "@/lib/hooks/useWebSocket"

interface CameraStatusPayload {
  capture_status?: string
  exposure_seconds?: number
  iso?: number
  night_vision_mode?: boolean
  night_vision_intensity?: number
  save_raw?: boolean
  recording?: boolean
}

interface CaptureEventPayload {
  capture_status?: string
  error?: string
  progress?: number
}

export function CameraControls() {
  const [exposure, setExposure] = useState([1.0])
  const [iso, setIso] = useState([800])
  const [intensity, setIntensity] = useState([1.0])
  const [nightVision, setNightVision] = useState(false)
  const [saveRaw, setSaveRaw] = useState(false)
  const [captureStatus, setCaptureStatus] = useState("Idle")
  const [isCapturing, setIsCapturing] = useState(false)
  const { socket, isConnected } = useWebSocket("/ws/camera")

  const syncFromStatus = useCallback(async () => {
    try {
      const status = await getCameraStatus()
      if (status.exposure_seconds) {
        setExposure([Number(status.exposure_seconds.toFixed(1))])
      }
      if (status.iso) {
        setIso([status.iso])
      }
      setNightVision(!!status.night_vision_mode)
      setIntensity([status.night_vision_intensity ?? 1.0])
      setSaveRaw(!!status.save_raw)
      setCaptureStatus(status.capture_status || "Idle")
    } catch (error) {
      console.error("Failed to sync camera status", error)
    }
  }, [])

  useEffect(() => {
    syncFromStatus()
  }, [syncFromStatus])

  useEffect(() => {
    if (!socket) return

    const handleStatus = (data: CameraStatusPayload) => {
      if (data.exposure_seconds) setExposure([Number(data.exposure_seconds.toFixed(1))])
      if (data.iso) setIso([data.iso])
      if (typeof data.night_vision_mode === "boolean") setNightVision(data.night_vision_mode)
      if (typeof data.night_vision_intensity === "number") setIntensity([data.night_vision_intensity])
      if (typeof data.save_raw === "boolean") setSaveRaw(data.save_raw)
      if (data.capture_status) setCaptureStatus(data.capture_status)
    }

    const handleCaptureStart = () => {
      setIsCapturing(true)
      setCaptureStatus("Capturing...")
    }

    const handleCaptureComplete = (payload: CaptureEventPayload) => {
      setIsCapturing(false)
      setCaptureStatus(payload.capture_status || "Completed")
    }

    const handleCaptureError = (payload: CaptureEventPayload) => {
      setIsCapturing(false)
      setCaptureStatus(`Error: ${payload.error ?? "unknown"}`)
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

  const handleExposureChange = async (value: number[]) => {
    setExposure(value)
    try {
      await updateCameraSettings({ exposure_seconds: value[0] })
    } catch (error) {
      console.error("Failed to update exposure", error)
    }
  }

  const handleIsoChange = async (value: number[]) => {
    setIso(value)
    try {
      await updateCameraSettings({ iso: value[0] })
    } catch (error) {
      console.error("Failed to update ISO", error)
    }
  }

  const handleIntensityChange = async (value: number[]) => {
    setIntensity(value)
    try {
      await updateCameraSettings({ night_vision_intensity: value[0] })
    } catch (error) {
      console.error("Failed to update night vision intensity", error)
    }
  }

  const handleNightVisionChange = async (value: boolean) => {
    setNightVision(value)
    try {
      await updateCameraSettings({ night_vision_mode: value })
    } catch (error) {
      console.error("Failed to update night vision mode", error)
    }
  }

  const handleSaveRawChange = async (value: boolean) => {
    setSaveRaw(value)
    try {
      await updateCameraSettings({ save_raw: value })
    } catch (error) {
      console.error("Failed to update save raw", error)
    }
  }

  const handleCapture = async () => {
    try {
      setIsCapturing(true)
      setCaptureStatus("Capturing...")
      await triggerCapture()
    } catch (error) {
      console.error("Capture failed", error)
      setCaptureStatus("Capture failed")
    } finally {
      if (!socket) {
        setIsCapturing(false)
      }
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between rounded-md bg-muted/40 px-4 py-2 text-sm">
        <span>Status: {captureStatus}</span>
        <span className="text-muted-foreground">WebSocket: {isConnected ? "Connected" : "Disconnected"}</span>
      </div>

      <Button onClick={handleCapture} disabled={isCapturing} className="w-full">
        {isCapturing ? "Capturing..." : "Capture Image"}
      </Button>

      <Collapsible defaultOpen>
        <CollapsibleTrigger className="flex w-full items-center justify-between px-6 py-3 hover:bg-accent">
          <span className="text-sm font-medium">Exposure Settings</span>
          <ChevronDown className="h-4 w-4 transition-transform duration-200 data-[state=open]:rotate-180" />
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-6 px-6 pb-6 pt-2">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-sm">Exposure Time</Label>
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  value={exposure[0]}
                  onChange={(e) => handleExposureChange([Number.parseFloat(e.target.value)])}
                  className="h-7 w-20 text-right text-sm"
                  step="0.1"
                  min="0.1"
                  max="300"
                />
                <span className="text-sm text-muted-foreground">s</span>
              </div>
            </div>
            <Slider value={exposure} onValueChange={handleExposureChange} min={0.1} max={300} step={0.1} className="w-full" />
            <p className="text-xs text-muted-foreground">Range: 0.1s - 300s</p>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <Button variant="outline" size="sm" onClick={() => handleExposureChange([0.5])} className="text-xs">
              Bright Objects
            </Button>
            <Button variant="outline" size="sm" onClick={() => handleExposureChange([30])} className="text-xs">
              Deep Sky
            </Button>
            <Button variant="outline" size="sm" onClick={() => handleExposureChange([180])} className="text-xs">
              Long Exposure
            </Button>
          </div>
        </CollapsibleContent>
      </Collapsible>

      <Collapsible defaultOpen>
        <CollapsibleTrigger className="flex w-full items-center justify-between px-6 py-3 hover:bg-accent">
          <span className="text-sm font-medium">ISO Sensitivity</span>
          <ChevronDown className="h-4 w-4 transition-transform duration-200 data-[state=open]:rotate-180" />
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-6 px-6 pb-6 pt-2">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-sm">ISO</Label>
              <Input
                type="number"
                value={iso[0]}
                onChange={(e) => handleIsoChange([Number.parseInt(e.target.value)])}
                className="h-7 w-20 text-right text-sm"
                step="100"
                min="100"
                max="6400"
              />
            </div>
            <Slider value={iso} onValueChange={handleIsoChange} min={100} max={6400} step={100} className="w-full" />
            <p className="text-xs text-muted-foreground">Range: 100 - 6400</p>
          </div>
        </CollapsibleContent>
      </Collapsible>

      <Collapsible defaultOpen>
        <CollapsibleTrigger className="flex w-full items-center justify-between px-6 py-3 hover:bg-accent">
          <span className="text-sm font-medium">Image Quality</span>
          <ChevronDown className="h-4 w-4 transition-transform duration-200 data-[state=open]:rotate-180" />
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-6 px-6 pb-6 pt-2">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-sm">Intensity</Label>
              <Input
                type="number"
                value={intensity[0]}
                onChange={(e) => handleIntensityChange([Number.parseFloat(e.target.value)])}
                className="h-7 w-20 text-right text-sm"
                step="0.1"
                min="1.0"
                max="80.0"
              />
            </div>
            <Slider value={intensity} onValueChange={handleIntensityChange} min={1.0} max={80.0} step={0.1} className="w-full" />
          </div>

          <div className="grid grid-cols-3 gap-2">
            <Button variant="outline" size="sm" onClick={() => handleIntensityChange([10])} className="text-xs">
              Low
            </Button>
            <Button variant="outline" size="sm" onClick={() => handleIntensityChange([40])} className="text-xs">
              Medium
            </Button>
            <Button variant="outline" size="sm" onClick={() => handleIntensityChange([70])} className="text-xs">
              High
            </Button>
          </div>
        </CollapsibleContent>
      </Collapsible>

      <Collapsible>
        <CollapsibleTrigger className="flex w-full items-center justify-between px-6 py-3 hover:bg-accent">
          <span className="text-sm font-medium">Advanced Options</span>
          <ChevronDown className="h-4 w-4 transition-transform duration-200 data-[state=open]:rotate-180" />
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-4 px-6 pb-6 pt-2">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-sm">Night Vision Mode</Label>
              <p className="text-xs text-muted-foreground">Red light interface</p>
            </div>
            <Switch checked={nightVision} onCheckedChange={handleNightVisionChange} />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-sm">Save RAW Files</Label>
              <p className="text-xs text-muted-foreground">Uncompressed format</p>
            </div>
            <Switch checked={saveRaw} onCheckedChange={handleSaveRawChange} />
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  )
}

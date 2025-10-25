"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import Image from "next/image"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Circle, Square, Download, ImageIcon, RefreshCw } from "lucide-react"
import { Progress } from "@/components/ui/progress"
import { useWebSocket } from "@/lib/hooks/useWebSocket"
import { ApiClientError, listCaptures, triggerCapture } from "@/lib/api-client"

export function CapturePanel() {
  const [isCapturing, setIsCapturing] = useState(false)
  const [captureCount, setCaptureCount] = useState(1)
  const [captureProgress, setCaptureProgress] = useState(0)
  const [captures, setCaptures] = useState<string[]>([])
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const { socket, isConnected, isReconnecting } = useWebSocket("/ws/camera")

  const connectionHint = useMemo(() => {
    if (isConnected) return "Live updates"
    if (isReconnecting) return "Reconnecting to camera"
    return "Realtime updates paused"
  }, [isConnected, isReconnecting])

  const fetchCaptures = useCallback(async () => {
    setIsRefreshing(true)
    setErrorMessage(null)
    try {
      const data = await listCaptures()
      setCaptures(data.files)
    } catch (error) {
      console.error("Failed to load captures", error)
      const message =
        error instanceof ApiClientError
          ? error.message
          : "Unable to load captures. Check backend connectivity."
      setErrorMessage(message)
    } finally {
      setIsRefreshing(false)
    }
  }, [])

  const handleManualCapture = useCallback(async () => {
    try {
      setIsCapturing(true)
      setErrorMessage(null)
      await triggerCapture()
    } catch (error) {
      console.error("Failed to trigger capture", error)
      const message =
        error instanceof ApiClientError ? error.message : "Capture request failed. See logs for details."
      setErrorMessage(message)
    }
  }, [])

  useEffect(() => {
    fetchCaptures()
    intervalRef.current = setInterval(fetchCaptures, 10_000)
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [fetchCaptures])

  useEffect(() => {
    if (!socket) return

    const handleCaptureStart = () => {
      setIsCapturing(true)
      setCaptureProgress(0)
    }

    const handleCaptureProgress = (payload: { progress?: number }) => {
      if (typeof payload.progress === "number") {
        setCaptureProgress(payload.progress)
      }
    }

    const handleCaptureComplete = () => {
      setIsCapturing(false)
      setCaptureProgress(100)
      fetchCaptures()
    }

    const handleCaptureError = () => {
      setIsCapturing(false)
      setCaptureProgress(0)
      setErrorMessage("Capture failed. Please retry.")
    }

    socket.on("capture_start", handleCaptureStart)
    socket.on("capture_progress", handleCaptureProgress)
    socket.on("capture_complete", handleCaptureComplete)
    socket.on("capture_error", handleCaptureError)

    return () => {
      socket.off("capture_start", handleCaptureStart)
      socket.off("capture_progress", handleCaptureProgress)
      socket.off("capture_complete", handleCaptureComplete)
      socket.off("capture_error", handleCaptureError)
    }
  }, [socket])

  return (
    <div className="flex h-full flex-col">
      <div className="space-y-6 p-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Capture Control</CardTitle>
            <CardDescription>
              Manual trigger and status updates. {connectionHint}.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button size="lg" className="w-full" onClick={handleManualCapture} disabled={isCapturing}>
              {isCapturing ? (
                <>
                  <Square className="mr-2 h-5 w-5 fill-current" />
                  Capturing...
                </>
              ) : (
                <>
                  <Circle className="mr-2 h-5 w-5" />
                  Trigger Capture
                </>
              )}
            </Button>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label className="text-sm">Number of Frames</Label>
                <Input
                  type="number"
                  value={captureCount}
                  onChange={(e) => setCaptureCount(Number.parseInt(e.target.value))}
                  min="1"
                  max="999"
                  className="h-9"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-sm">Save Location</Label>
                <Input value="/captures" readOnly className="h-9" />
              </div>
            </div>

            {isCapturing && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Exposure in progress</span>
                  <span className="font-mono">{captureProgress.toFixed(0)}%</span>
                </div>
                <Progress value={captureProgress} className="h-2" />
              </div>
            )}

            {errorMessage && <p className="text-sm text-destructive">{errorMessage}</p>}
          </CardContent>
        </Card>
      </div>

      <div className="flex-1 border-t border-border bg-muted/10">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div>
            <h3 className="text-sm font-semibold">Recent Captures</h3>
            <p className="text-xs text-muted-foreground">Latest files saved to the Raspberry Pi.</p>
          </div>
          <Button variant="ghost" size="sm" onClick={fetchCaptures} disabled={isRefreshing}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>

        <div className="flex-1 max-h-[600px] overflow-y-auto p-6">
          {captures.length === 0 ? (
            <div className="flex h-32 flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-border bg-background/60 text-center text-sm text-muted-foreground">
              <ImageIcon className="h-6 w-6" />
              <span>No captures yet. Trigger a capture to populate the gallery.</span>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {captures.slice(0, 20).map((filename) => (
                <Card key={filename} className="overflow-hidden">
                  <CardContent className="flex items-center gap-4 p-4">
                    <div className="relative h-16 w-16 overflow-hidden rounded border border-border">
              <Image
                src={`/api/captures/${encodeURIComponent(filename)}`}
                alt={filename}
                fill
                className="object-cover"
                sizes="64px"
                unoptimized
              />
                    </div>
                    <div className="flex-1 truncate">
                      <p className="truncate text-sm font-medium">{filename}</p>
                      <p className="text-xs text-muted-foreground">Stored in /captures</p>
                    </div>
                    <Button variant="secondary" size="sm" asChild>
                      <Link href={`/api/captures/${encodeURIComponent(filename)}`} target="_blank">
                        <Download className="mr-2 h-4 w-4" />
                        Download
                      </Link>
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

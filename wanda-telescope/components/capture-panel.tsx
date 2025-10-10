"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card } from "@/components/ui/card"
import { Circle, Square, Download, ImageIcon } from "lucide-react"
import { Progress } from "@/components/ui/progress"
import { useWebSocket } from "@/lib/hooks/useWebSocket"
import { listCaptures } from "@/lib/api-client"

interface CaptureProgressPayload {
  progress?: number
}

export function CapturePanel() {
  const [isCapturing, setIsCapturing] = useState(false)
  const [captureCount, setCaptureCount] = useState(1)
  const [captureProgress, setCaptureProgress] = useState(0)
  const [captures, setCaptures] = useState<string[]>([])
  const { socket } = useWebSocket("/ws/camera")

  useEffect(() => {
    const fetchCaptures = async () => {
      try {
        const data = await listCaptures()
        setCaptures(data.files)
      } catch (error) {
        console.error("Failed to load captures", error)
      }
    }

    fetchCaptures()
    const timer = setInterval(fetchCaptures, 5000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    if (!socket) return

    const handleCaptureStart = () => {
      setIsCapturing(true)
      setCaptureProgress(0)
    }

    const handleCaptureProgress = (payload: CaptureProgressPayload) => {
      if (typeof payload.progress === "number") {
        setCaptureProgress(payload.progress)
      }
    }

    const handleCaptureComplete = () => {
      setIsCapturing(false)
      setCaptureProgress(100)
    }

    const handleCaptureError = () => {
      setIsCapturing(false)
      setCaptureProgress(0)
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
        <div>
          <h3 className="mb-4 text-sm font-semibold">Capture</h3>
          <Button size="lg" className="w-full" disabled>
            {isCapturing ? (
              <>
                <Square className="mr-2 h-5 w-5 fill-current" />
                Stop Capture (Handled elsewhere)
              </>
            ) : (
              <>
                <Circle className="mr-2 h-5 w-5" />
                Start Capture via Camera Controls
              </>
            )}
          </Button>

          {isCapturing && (
            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Exposing...</span>
                <span className="font-mono">{captureProgress.toFixed(0)}%</span>
              </div>
              <Progress value={captureProgress} className="h-2" />
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
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

          <div className="space-y-2">
            <Label className="text-sm">Save Location</Label>
            <div className="flex gap-2">
              <Input value="/captures" readOnly className="h-9 flex-1" />
              <Button variant="outline" size="sm" disabled>
                Browse
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 border-t border-border">
        <div className="p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold">Recent Captures</h3>
            <Button variant="ghost" size="sm" disabled>
              <Download className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-2">
            {captures.length === 0 && (
              <p className="text-xs text-muted-foreground">No captures yet.</p>
            )}
            {captures.slice(0, 5).map((filename) => (
              <Card key={filename} className="p-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded bg-muted">
                    <ImageIcon className="h-6 w-6 text-muted-foreground" />
                  </div>
                  <div className="flex-1">
                    <p className="truncate text-sm font-medium">{filename}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Circle, Square, Download, ImageIcon } from "lucide-react"
import { Progress } from "@/components/ui/progress"

interface CapturePanelProps {
  isCapturing: boolean
  onCaptureStart: () => void
  onCaptureStop: () => void
}

export function CapturePanel({ isCapturing, onCaptureStart, onCaptureStop }: CapturePanelProps) {
  const [captureCount, setCaptureCount] = useState(1)
  const [captureProgress, setCaptureProgress] = useState(0)

  return (
    <div className="flex h-full flex-col">
      {/* Capture Controls */}
      <div className="space-y-6 p-6">
        <div>
          <h3 className="mb-4 text-sm font-semibold">Capture</h3>

          {/* Main Capture Button */}
          <Button
            size="lg"
            className="w-full"
            variant={isCapturing ? "destructive" : "default"}
            onClick={isCapturing ? onCaptureStop : onCaptureStart}
          >
            {isCapturing ? (
              <>
                <Square className="mr-2 h-5 w-5 fill-current" />
                Stop Capture
              </>
            ) : (
              <>
                <Circle className="mr-2 h-5 w-5" />
                Start Capture
              </>
            )}
          </Button>

          {/* Capture Progress */}
          {isCapturing && (
            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Exposing...</span>
                <span className="font-mono">15.2s / 30.0s</span>
              </div>
              <Progress value={50} className="h-2" />
            </div>
          )}
        </div>

        {/* Capture Settings */}
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
              <Input value="/captures/session_001" readOnly className="h-9 flex-1" />
              <Button variant="outline" size="sm">
                Browse
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Captures */}
      <div className="flex-1 border-t border-border">
        <div className="p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold">Recent Captures</h3>
            <Button variant="ghost" size="sm">
              <Download className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="p-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded bg-muted">
                    <ImageIcon className="h-6 w-6 text-muted-foreground" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium">IMG_000{i}.fits</p>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs">
                        30s
                      </Badge>
                      <Badge variant="secondary" className="text-xs">
                        ISO 800
                      </Badge>
                    </div>
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

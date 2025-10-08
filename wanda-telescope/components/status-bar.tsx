"use client"

import { Badge } from "@/components/ui/badge"
import { Wifi, HardDrive, Thermometer } from "lucide-react"

interface StatusBarProps {
  isCapturing: boolean
}

export function StatusBar({ isCapturing }: StatusBarProps) {
  return (
    <footer className="flex items-center justify-between border-t border-border bg-card px-6 py-2 text-xs">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Wifi className="h-3 w-3 text-muted-foreground" />
          <span className="text-muted-foreground">Connected</span>
        </div>
        <div className="flex items-center gap-2">
          <HardDrive className="h-3 w-3 text-muted-foreground" />
          <span className="text-muted-foreground">Storage: 234 GB free</span>
        </div>
        <div className="flex items-center gap-2">
          <Thermometer className="h-3 w-3 text-muted-foreground" />
          <span className="text-muted-foreground">Sensor: -10°C</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {isCapturing && (
          <Badge variant="default" className="animate-pulse">
            Recording
          </Badge>
        )}
        <span className="text-muted-foreground">Camera: 12MP IMX477 - ArduCam</span>
      </div>
    </footer>
  )
}

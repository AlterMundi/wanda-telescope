"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export function FocusAssist() {
  return (
    <Card className="w-64 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h4 className="text-sm font-semibold">Focus Assist</h4>
        <Badge variant="secondary">Good</Badge>
      </div>
      <div className="space-y-3">
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Sharpness</span>
            <span className="font-mono">87%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
            <div className="h-full w-[87%] bg-primary" />
          </div>
        </div>
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Contrast</span>
            <span className="font-mono">92%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
            <div className="h-full w-[92%] bg-primary" />
          </div>
        </div>
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Stars Detected</span>
            <span className="font-mono">143</span>
          </div>
        </div>
      </div>
    </Card>
  )
}

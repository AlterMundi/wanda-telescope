"use client"

import { Card } from "@/components/ui/card"

export function Histogram() {
  return (
    <Card className="w-64 p-4">
      <h4 className="mb-3 text-sm font-semibold">Histogram</h4>
      <div className="relative h-32 w-full rounded bg-muted">
        {/* Simplified histogram visualization */}
        <svg className="h-full w-full" viewBox="0 0 256 128">
          <path
            d="M 0 128 L 10 120 L 20 110 L 30 95 L 40 85 L 50 70 L 60 60 L 70 50 L 80 45 L 90 40 L 100 35 L 110 32 L 120 30 L 130 32 L 140 35 L 150 40 L 160 50 L 170 65 L 180 80 L 190 95 L 200 105 L 210 115 L 220 120 L 230 123 L 240 125 L 250 127 L 256 128 Z"
            fill="hsl(var(--primary))"
            opacity="0.5"
          />
        </svg>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
        <div>
          <span className="text-muted-foreground">Min:</span> 12
        </div>
        <div>
          <span className="text-muted-foreground">Avg:</span> 128
        </div>
        <div>
          <span className="text-muted-foreground">Max:</span> 245
        </div>
      </div>
    </Card>
  )
}

"use client"
import { Histogram } from "@/components/histogram"
import { FocusAssist } from "@/components/focus-assist"

interface ImagePreviewProps {
  showHistogram: boolean
  showFocusAssist: boolean
}

export function ImagePreview({ showHistogram, showFocusAssist }: ImagePreviewProps) {
  return (
    <div className="relative flex-1 bg-black">
      {/* Main Image */}
      <div className="flex h-full items-center justify-center p-4">
        <img
          src="/purple-nebula-in-space-astrophotography.jpg"
          alt="Telescope view"
          className="max-h-full max-w-full rounded-lg object-contain"
        />
      </div>

      {/* Overlays */}
      {showHistogram && (
        <div className="absolute right-4 top-4">
          <Histogram />
        </div>
      )}

      {showFocusAssist && (
        <div className="absolute left-4 top-4">
          <FocusAssist />
        </div>
      )}

      {/* Crosshair */}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div className="relative h-8 w-8">
          <div className="absolute left-1/2 top-0 h-2 w-px -translate-x-1/2 bg-primary/50" />
          <div className="absolute bottom-0 left-1/2 h-2 w-px -translate-x-1/2 bg-primary/50" />
          <div className="absolute left-0 top-1/2 h-px w-2 -translate-y-1/2 bg-primary/50" />
          <div className="absolute right-0 top-1/2 h-px w-2 -translate-y-1/2 bg-primary/50" />
          <div className="absolute left-1/2 top-1/2 h-1 w-1 -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/50" />
        </div>
      </div>
    </div>
  )
}

"use client"
import Image from "next/image"
import { Histogram } from "@/components/histogram"
import { FocusAssist } from "@/components/focus-assist"

interface ImagePreviewProps {
  showHistogram: boolean
  showFocusAssist: boolean
}

export function ImagePreview({ showHistogram, showFocusAssist }: ImagePreviewProps) {
  return (
    <div className="relative flex-1 bg-black">
      <div className="flex h-full items-center justify-center p-4">
        <Image
          src="/video_feed"
          alt="Telescope view"
          width={1280}
          height={720}
          className="max-h-full max-w-full rounded-lg object-contain"
          unoptimized
        />
      </div>

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
    </div>
  )
}

"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Camera, Settings, BarChart3, Focus, Maximize2 } from "lucide-react"
import { CameraControls } from "@/components/camera-controls"
import { ImagePreview } from "@/components/image-preview"
import { CapturePanel } from "@/components/capture-panel"
import { StatusBar } from "@/components/status-bar"

export default function TelescopePage() {
  const [isCapturing, setIsCapturing] = useState(false)
  const [showHistogram, setShowHistogram] = useState(false)
  const [showFocusAssist, setShowFocusAssist] = useState(false)
  const [captureCount, setCaptureCount] = useState(0)

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border px-6 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary">
            <Camera className="h-5 w-5 text-primary-foreground" />
          </div>
          <h1 className="text-lg font-semibold">Wanda Telescope</h1>
          <Badge variant="secondary" className="ml-2">
            Connected
          </Badge>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Controls */}
        <aside className="w-80 border-r border-border bg-card">
          <Tabs defaultValue="camera" className="h-full">
            <TabsList className="w-full justify-start rounded-none border-b border-border bg-transparent p-0">
              <TabsTrigger
                value="camera"
                className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
              >
                Camera
              </TabsTrigger>
              <TabsTrigger
                value="mount"
                className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
              >
                Mount
              </TabsTrigger>
              <TabsTrigger
                value="session"
                className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
              >
                Session
              </TabsTrigger>
            </TabsList>

            <TabsContent value="camera" className="h-[calc(100%-3rem)] overflow-y-auto p-0">
              <CameraControls />
            </TabsContent>

            <TabsContent value="mount" className="p-6">
              <p className="text-sm text-muted-foreground">Mount controls coming soon...</p>
            </TabsContent>

            <TabsContent value="session" className="p-6">
              <p className="text-sm text-muted-foreground">Session management coming soon...</p>
            </TabsContent>
          </Tabs>
        </aside>

        {/* Center - Image Preview */}
        <main className="flex flex-1 flex-col">
          <ImagePreview showHistogram={showHistogram} showFocusAssist={showFocusAssist} />

          {/* Bottom Toolbar */}
          <div className="flex items-center justify-between border-t border-border bg-card px-6 py-3">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={() => setShowHistogram(!showHistogram)}>
                <BarChart3 className="mr-2 h-4 w-4" />
                Histogram
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setShowFocusAssist(!showFocusAssist)}>
                <Focus className="mr-2 h-4 w-4" />
                Focus Assist
              </Button>
              <Button variant="ghost" size="sm">
                <Maximize2 className="mr-2 h-4 w-4" />
                Fullscreen
              </Button>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">{captureCount} images captured</span>
            </div>
          </div>
        </main>

        {/* Right Sidebar - Capture Panel */}
        <aside className="w-80 border-l border-border bg-card">
          <CapturePanel
            isCapturing={isCapturing}
            onCaptureStart={() => setIsCapturing(true)}
            onCaptureStop={() => {
              setIsCapturing(false)
              setCaptureCount((prev) => prev + 1)
            }}
          />
        </aside>
      </div>

      {/* Status Bar */}
      <StatusBar isCapturing={isCapturing} />
    </div>
  )
}

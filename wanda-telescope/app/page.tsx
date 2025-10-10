"use client"

import Image from "next/image"
import { CameraControls } from "@/components/camera-controls"
import { CapturePanel } from "@/components/capture-panel"
import { ImagePreview } from "@/components/image-preview"
import { StatusBar } from "@/components/status-bar"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="border-b border-border bg-card/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <Image src="/favicon.ico" alt="WANDA" width={32} height={32} className="rounded" />
            <div>
              <h1 className="text-lg font-semibold">WANDA Telescope Control</h1>
              <p className="text-xs text-muted-foreground">Raspberry Pi 5 • Flask API • Next.js UI</p>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-6 py-6">
        <section className="grid gap-6 md:grid-cols-[1.6fr_1fr]">
          <div className="flex flex-col gap-6">
            <div className="flex flex-col rounded-xl border border-border bg-card shadow-sm">
              <div className="border-b border-border px-6 py-4">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Camera Feed</h2>
              </div>
              <ImagePreview showHistogram showFocusAssist={false} />
            </div>

            <div className="rounded-xl border border-border bg-card shadow-sm">
              <Tabs defaultValue="camera" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="camera">Camera</TabsTrigger>
                  <TabsTrigger value="mount">Mount</TabsTrigger>
                  <TabsTrigger value="session">Sessions</TabsTrigger>
                </TabsList>
                <TabsContent value="camera" className="p-6">
                  <CameraControls />
                </TabsContent>
                <TabsContent value="mount" className="p-6 text-sm text-muted-foreground">
                  Placeholder mount controls (to be implemented)
                </TabsContent>
                <TabsContent value="session" className="p-6 text-sm text-muted-foreground">
                  Placeholder session controls (to be implemented)
                </TabsContent>
              </Tabs>
            </div>
          </div>

          <div className="flex h-full flex-col gap-6">
            <div className="rounded-xl border border-border bg-card shadow-sm">
              <div className="border-b border-border px-6 py-4">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Capture Control</h2>
              </div>
              <CapturePanel />
            </div>
          </div>
        </section>
      </main>

      <StatusBar />
    </div>
  )
}

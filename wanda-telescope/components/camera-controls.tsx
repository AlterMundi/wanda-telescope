"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { ChevronDown } from "lucide-react"

export function CameraControls() {
  const [exposure, setExposure] = useState([0.1])
  const [iso, setIso] = useState([100])
  const [intensity, setIntensity] = useState([1.0])
  const [nightVision, setNightVision] = useState(false)
  const [saveRaw, setSaveRaw] = useState(false)

  return (
    <div className="space-y-1">
      {/* Exposure Settings */}
      <Collapsible defaultOpen>
        <CollapsibleTrigger className="flex w-full items-center justify-between px-6 py-3 hover:bg-accent">
          <span className="text-sm font-medium">Exposure Settings</span>
          <ChevronDown className="h-4 w-4 transition-transform duration-200 data-[state=open]:rotate-180" />
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-6 px-6 pb-6 pt-2">
          {/* Exposure Time */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-sm">Exposure Time</Label>
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  value={exposure[0]}
                  onChange={(e) => setExposure([Number.parseFloat(e.target.value)])}
                  className="h-7 w-20 text-right text-sm"
                  step="0.1"
                  min="0.1"
                  max="300"
                />
                <span className="text-sm text-muted-foreground">s</span>
              </div>
            </div>
            <Slider value={exposure} onValueChange={setExposure} min={0.1} max={300} step={0.1} className="w-full" />
            <p className="text-xs text-muted-foreground">Range: 0.1s - 300s</p>
          </div>

          {/* Preset Buttons */}
          <div className="grid grid-cols-3 gap-2">
            <Button variant="outline" size="sm" onClick={() => setExposure([0.5])} className="text-xs">
              Bright Objects
            </Button>
            <Button variant="outline" size="sm" onClick={() => setExposure([30])} className="text-xs">
              Deep Sky
            </Button>
            <Button variant="outline" size="sm" onClick={() => setExposure([180])} className="text-xs">
              Long Exposure
            </Button>
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* ISO Sensitivity */}
      <Collapsible defaultOpen>
        <CollapsibleTrigger className="flex w-full items-center justify-between px-6 py-3 hover:bg-accent">
          <span className="text-sm font-medium">ISO Sensitivity</span>
          <ChevronDown className="h-4 w-4 transition-transform duration-200 data-[state=open]:rotate-180" />
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-6 px-6 pb-6 pt-2">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-sm">ISO</Label>
              <Input
                type="number"
                value={iso[0]}
                onChange={(e) => setIso([Number.parseInt(e.target.value)])}
                className="h-7 w-20 text-right text-sm"
                step="100"
                min="100"
                max="6400"
              />
            </div>
            <Slider value={iso} onValueChange={setIso} min={100} max={6400} step={100} className="w-full" />
            <p className="text-xs text-muted-foreground">Range: 100 - 6400</p>
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Image Quality */}
      <Collapsible defaultOpen>
        <CollapsibleTrigger className="flex w-full items-center justify-between px-6 py-3 hover:bg-accent">
          <span className="text-sm font-medium">Image Quality</span>
          <ChevronDown className="h-4 w-4 transition-transform duration-200 data-[state=open]:rotate-180" />
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-6 px-6 pb-6 pt-2">
          {/* Intensity */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-sm">Intensity</Label>
              <Input
                type="number"
                value={intensity[0]}
                onChange={(e) => setIntensity([Number.parseFloat(e.target.value)])}
                className="h-7 w-20 text-right text-sm"
                step="0.1"
                min="1.0"
                max="80.0"
              />
            </div>
            <Slider value={intensity} onValueChange={setIntensity} min={1.0} max={80.0} step={0.1} className="w-full" />
          </div>

          {/* Preset Buttons */}
          <div className="grid grid-cols-3 gap-2">
            <Button variant="outline" size="sm" onClick={() => setIntensity([10])} className="text-xs">
              Low
            </Button>
            <Button variant="outline" size="sm" onClick={() => setIntensity([40])} className="text-xs">
              Medium
            </Button>
            <Button variant="outline" size="sm" onClick={() => setIntensity([70])} className="text-xs">
              High
            </Button>
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Advanced Options */}
      <Collapsible>
        <CollapsibleTrigger className="flex w-full items-center justify-between px-6 py-3 hover:bg-accent">
          <span className="text-sm font-medium">Advanced Options</span>
          <ChevronDown className="h-4 w-4 transition-transform duration-200 data-[state=open]:rotate-180" />
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-4 px-6 pb-6 pt-2">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-sm">Night Vision Mode</Label>
              <p className="text-xs text-muted-foreground">Red light interface</p>
            </div>
            <Switch checked={nightVision} onCheckedChange={setNightVision} />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-sm">Save RAW Files</Label>
              <p className="text-xs text-muted-foreground">Uncompressed format</p>
            </div>
            <Switch checked={saveRaw} onCheckedChange={setSaveRaw} />
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  )
}

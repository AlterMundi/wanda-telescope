import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor, fireEvent } from "@testing-library/react"
import { CameraControls } from "@/components/camera-controls"
import { getCameraStatus, updateCameraSettings, triggerCapture } from "@/lib/api-client"

vi.mock("@/lib/api-client", () => ({
  getCameraStatus: vi.fn(),
  updateCameraSettings: vi.fn(),
  triggerCapture: vi.fn(),
}))

const mockSocket = {
  on: vi.fn(),
  off: vi.fn(),
}

vi.mock("@/lib/hooks/useWebSocket", () => ({
  useWebSocket: () => ({
    socket: mockSocket,
    isConnected: true,
    isReconnecting: false,
    connectionAttempts: 0,
  }),
}))

describe("CameraControls", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(getCameraStatus).mockResolvedValue({
      mode: "photo",
      capture_status: "Idle",
      exposure_seconds: 1.2,
      iso: 800,
      gain: 1.0,
      night_vision_mode: false,
      night_vision_intensity: 5,
      save_raw: false,
      skip_frames: 0,
      recording: false,
    })
  })

  it("loads initial status", async () => {
    render(<CameraControls />)
    await waitFor(() => expect(getCameraStatus).toHaveBeenCalled())
    expect(screen.getByText(/Status: Idle/i)).toBeInTheDocument()
    expect(screen.getByRole("slider", { name: /Exposure Time/i })).toBeInTheDocument()
  })

  it("updates exposure", async () => {
    render(<CameraControls />)
    await waitFor(() => expect(getCameraStatus).toHaveBeenCalled())

    const exposureInput = screen.getByRole("spinbutton", { name: /Exposure Time/i })
    fireEvent.change(exposureInput, { target: { value: "2.5" } })

    await waitFor(() => {
      expect(vi.mocked(updateCameraSettings)).toHaveBeenCalledWith({ exposure_seconds: 2.5 })
    })
  })

  it("triggers capture", async () => {
    render(<CameraControls />)
    await waitFor(() => expect(getCameraStatus).toHaveBeenCalled())

    fireEvent.click(screen.getByRole("button", { name: /Capture Image/i }))

    await waitFor(() => {
      expect(vi.mocked(triggerCapture)).toHaveBeenCalled()
    })
  })
})


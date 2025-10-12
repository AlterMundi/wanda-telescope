import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, waitFor, fireEvent } from "@testing-library/react"
import { MountControls } from "@/components/mount-controls"

vi.mock("@/lib/api-client", () => ({
  getMountStatus: vi.fn(),
  sendMountAction: vi.fn(),
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

describe("MountControls", () => {
  const { getMountStatus, sendMountAction } = require("@/lib/api-client")

  beforeEach(() => {
    vi.clearAllMocks()
    getMountStatus.mockResolvedValue({
      status: "Ready",
      tracking: false,
      direction: true,
      speed: 1.0,
    })
  })

  afterEach(() => {
    vi.resetModules()
  })

  it("renders initial status", async () => {
    render(<MountControls />)
    await waitFor(() => expect(getMountStatus).toHaveBeenCalled())
    expect(screen.getByText(/Mount Tracking/i)).toBeInTheDocument()
    expect(screen.getByText(/State: Ready/i)).toBeInTheDocument()
  })

  it("starts tracking with current speed and direction", async () => {
    render(<MountControls />)
    await waitFor(() => expect(getMountStatus).toHaveBeenCalled())

    fireEvent.click(screen.getByRole("button", { name: /Start Tracking/i }))

    await waitFor(() => {
      expect(sendMountAction).toHaveBeenCalledWith("start", expect.objectContaining({
        speed: expect.any(Number),
        direction: "cw",
      }))
    })
  })

  it("handles stop tracking", async () => {
    getMountStatus.mockResolvedValueOnce({
      status: "Tracking",
      tracking: true,
      direction: true,
      speed: 1.3,
    })

    render(<MountControls />)
    await waitFor(() => expect(getMountStatus).toHaveBeenCalled())

    fireEvent.click(screen.getByRole("button", { name: /^Stop$/i }))

    await waitFor(() => {
      expect(sendMountAction).toHaveBeenCalledWith("stop")
    })
  })
})


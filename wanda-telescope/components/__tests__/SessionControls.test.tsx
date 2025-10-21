import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor, fireEvent } from "@testing-library/react"
import { SessionControls } from "@/components/session-controls"
import { getSessionStatus, startSession, stopSession } from "@/lib/api-client"

vi.mock("@/lib/api-client", () => ({
  getSessionStatus: vi.fn(),
  startSession: vi.fn(),
  stopSession: vi.fn(),
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

describe("SessionControls", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(getSessionStatus).mockResolvedValue({
      active: false,
      name: "Night Session",
      total_images: 10,
      captured_images: 3,
      remaining_time: 1.5,
    })
  })

  it("shows session info", async () => {
    render(<SessionControls />)
    await waitFor(() => expect(getSessionStatus).toHaveBeenCalled())
    expect(screen.getByText(/Capture Sessions/i)).toBeInTheDocument()
    expect(screen.getByText(/Progress: 3\/10/i)).toBeInTheDocument()
  })

  it("starts a session", async () => {
    render(<SessionControls />)
    await waitFor(() => expect(getSessionStatus).toHaveBeenCalled())

    fireEvent.click(screen.getByRole("button", { name: /Start Session/i }))

    await waitFor(() => {
      expect(startSession).toHaveBeenCalled()
    })
  })

  it("stops a session", async () => {
    vi.mocked(getSessionStatus).mockResolvedValueOnce({
      active: true,
      name: "Active Session",
      total_images: 5,
      captured_images: 2,
      remaining_time: 0.5,
    })

    render(<SessionControls />)
    await waitFor(() => expect(getSessionStatus).toHaveBeenCalled())

    fireEvent.click(screen.getByRole("button", { name: /Stop Session/i }))

    await waitFor(() => {
      expect(stopSession).toHaveBeenCalled()
    })
  })
})


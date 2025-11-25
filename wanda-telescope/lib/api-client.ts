"use client"

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "/api").replace(/\/$/, "")

interface ApiResponse<T> {
  success: boolean
  data: T
  message?: string
  error?: string
  code?: string
}

type ApiOptions = Omit<RequestInit, 'body'> & {
  body?: BodyInit | Record<string, unknown> | null | undefined
  parseJson?: boolean
  skipDefaultHeaders?: boolean
}

export class ApiClientError extends Error {
  status: number
  code?: string
  details?: unknown

  constructor(message: string, status: number, code?: string, details?: unknown) {
    super(message)
    this.name = "ApiClientError"
    this.status = status
    this.code = code
    this.details = details
  }
}

function buildUrl(endpoint: string): string {
  if (!endpoint) {
    throw new Error("endpoint is required")
  }

  const normalizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`
  return `${API_BASE}${normalizedEndpoint}`
}

async function parseResponseJson<T>(response: Response): Promise<ApiResponse<T>> {
  const contentType = response.headers.get("Content-Type") || ""
  if (!contentType.includes("application/json")) {
    throw new ApiClientError("Expected JSON response", response.status)
  }

  try {
    return (await response.json()) as ApiResponse<T>
  } catch (error) {
    throw new ApiClientError("Failed to parse API response", response.status, undefined, error)
  }
}

export async function apiCall<T>(endpoint: string, options: ApiOptions = {}): Promise<T> {
  const {
    parseJson = true,
    skipDefaultHeaders = false,
    headers,
    body,
    cache,
    credentials,
    ...rest
  } = options

  const requestInit: RequestInit = {
    ...rest,
    method: rest.method ?? (body ? "POST" : "GET"),
    cache: cache ?? "no-store",
    credentials: credentials ?? "same-origin",
  }

  const requestHeaders = new Headers(headers)
  if (!skipDefaultHeaders && !requestHeaders.has("Content-Type")) {
    requestHeaders.set("Content-Type", "application/json")
  }

  if (["POST", "PUT", "PATCH", "DELETE"].includes((requestInit.method || "").toUpperCase())) {
    if (body && typeof body !== "string" && !(body instanceof FormData)) {
      requestInit.body = JSON.stringify(body)
    } else {
      requestInit.body = body
    }
  }

  if (requestHeaders.keys().next().done === false) {
    requestInit.headers = requestHeaders
  }

  const response = await fetch(buildUrl(endpoint), requestInit)

  if (!parseJson) {
    if (!response.ok) {
      throw new ApiClientError(response.statusText || "Request failed", response.status)
    }
    return undefined as T
  }

  const payload = await parseResponseJson<T>(response)

  if (!response.ok || !payload.success) {
    throw new ApiClientError(
      payload.error || response.statusText || "Request failed",
      response.status,
      payload.code,
      payload
    )
  }

  return payload.data
}

// ---------------------------------------------------------------------------
// High-level typed helpers
// ---------------------------------------------------------------------------

export interface CameraStatus {
  mode: string
  capture_status: string
  recording: boolean
  iso: number
  gain: number
  exposure_seconds: number
  night_vision_mode: boolean
  night_vision_intensity: number
  save_raw: boolean
  skip_frames: number
}

export interface CaptureResult {
  capture_status: string
  recording: boolean
}

export interface MountStatus {
  status: string
  tracking: boolean
  direction?: boolean
  speed?: number
}

export interface SessionStatus {
  active: boolean
  name: string
  total_images: number
  captured_images: number
  remaining_time: number
  [key: string]: unknown
}

export async function getCameraStatus() {
  return apiCall<CameraStatus>("/camera/status")
}

export async function updateCameraSettings(payload: Record<string, unknown>) {
  return apiCall<CameraStatus>("/camera/settings", {
    method: "POST",
    body: payload,
  })
}

export async function triggerCapture() {
  return apiCall<CaptureResult>("/camera/capture", {
    method: "POST",
  })
}

export async function getMountStatus() {
  return apiCall<MountStatus>("/mount/status")
}

export async function sendMountAction(action: "start" | "stop", payload?: Record<string, unknown>) {
  return apiCall<MountStatus>("/mount/tracking", {
    method: "POST",
    body: { action, ...payload },
  })
}

export async function getSessionStatus() {
  return apiCall<SessionStatus>("/session/status")
}

export async function startSession(payload: Record<string, unknown>) {
  return apiCall<SessionStatus>("/session/start", {
    method: "POST",
    body: payload,
  })
}

export async function stopSession() {
  return apiCall<SessionStatus>("/session/stop", {
    method: "POST",
  })
}

export async function listCaptures(folder?: string | null) {
  const url = folder ? `/captures?folder=${encodeURIComponent(folder)}` : "/captures"
  return apiCall<{ files: string[] }>(url)
}

export async function listCaptureFolders() {
  return apiCall<{ folders: string[] }>("/captures/folders")
}

export interface SessionConfig {
  name: string
  totalImages: number
  enableTracking: boolean
  useCurrentSettings: boolean
  sessionMode: "rapid" | "timed"
  totalTimeHours: number | null
}

export async function getSessionConfig() {
  return apiCall<SessionConfig>("/session/config")
}

export async function saveSessionConfig(config: SessionConfig) {
  return apiCall<SessionConfig>("/session/config", {
    method: "POST",
    body: config as unknown as Record<string, unknown>,
  })
}

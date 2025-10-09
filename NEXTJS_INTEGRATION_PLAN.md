# Next.js Integration Plan - Wanda Telescope

**Project:** Full integration of v0-generated Next.js frontend with Flask backend  
**Target Platform:** Raspberry Pi 5  
**Deployment Scope:** Local network (Cloudflare Tunnel to be added later)  
**Real-time Communication:** WebSockets (Flask-SocketIO)  
**Estimated Timeline:** 27-38 hours (3-5 days)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Development                          │
│                                                         │
│   Laptop/Desktop (Code editing)                        │
│   ├─ Edit Next.js code (wanda-telescope/)             │
│   ├─ Edit Flask code (web/, camera/, mount/)          │
│   └─ Git push to repository                           │
│                                                         │
└────────────────────┬────────────────────────────────────┘
                     │ Deploy
                     ↓
┌─────────────────────────────────────────────────────────┐
│              Raspberry Pi 5 Production                  │
│                                                         │
│   Systemd Services:                                    │
│   ├─ wanda-frontend.service (Next.js on port 3000)    │
│   └─ wanda-backend.service (Flask on port 5000)       │
│                                                         │
│   Nginx Reverse Proxy (port 80/443):                  │
│   ├─ / → localhost:3000 (Next.js)                     │
│   └─ /api → localhost:5000 (Flask)                    │
│                                                         │
│   Communication:                                        │
│   ├─ REST API (HTTP/JSON)                             │
│   ├─ WebSockets (real-time updates)                   │
│   └─ MJPEG Stream (video feed)                        │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 1: Flask Backend Refactoring
**Goal:** Convert Flask from template-based to pure REST API  
**Time Estimate:** 3-4 hours  
**Complexity:** 🟡 Medium

### Tasks

#### 1.1 - Update Flask routes to return JSON
**Current:**
```python
@app.route('/')
def index():
    return render_template('index.html', exposure=camera.exposure)
```

**Target:**
```python
@app.route('/api/status')
def get_status():
    return jsonify({
        'success': True,
        'data': {
            'exposure': camera.exposure,
            'iso': camera.iso,
            'mode': camera.mode
        }
    })
```

**Files to modify:**
- `web/app.py` - All route handlers

#### 1.2 - Create standardized API response format
**Standard Success Response:**
```json
{
  "success": true,
  "data": { /* payload */ },
  "message": "Operation completed successfully"
}
```

**Standard Error Response:**
```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE"
}
```

**Implementation:**
- Create utility functions: `success_response()`, `error_response()`
- Use consistently across all endpoints

#### 1.3 - Add CORS support
**Why:** Next.js dev server (port 3000) needs to call Flask (port 5000) = cross-origin

**Install:**
```bash
pip install flask-cors
```

**Configure:**
```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'])
```

#### 1.4 - Organize routes under /api prefix
**New route structure:**
```
/api/camera/capture      (POST) - Capture single image
/api/camera/settings     (GET/POST) - Get/update camera settings
/api/camera/status       (GET) - Get current status
/api/mount/tracking      (POST) - Start/stop tracking
/api/mount/status        (GET) - Get mount status
/api/session/start       (POST) - Start capture session
/api/session/stop        (POST) - Stop capture session
/api/session/status      (GET) - Get session progress
/api/captures            (GET) - List captured images
```

#### 1.5 - Keep /video_feed endpoint
**Why:** MJPEG streaming works well, no need to change

**Usage:** Next.js will consume as: `<img src="/video_feed" />`

#### 1.6 - Update Flask tests
**Changes needed:**
- Remove assertions checking for HTML content
- Add assertions for JSON structure
- Update test fixtures to expect API responses

**Example:**
```python
# Before
assert b'<html>' in response.data

# After
data = json.loads(response.data)
assert data['success'] == True
assert 'exposure' in data['data']
```

---

## Phase 2: WebSocket Implementation
**Goal:** Add real-time bidirectional communication  
**Time Estimate:** 4-5 hours  
**Complexity:** 🔴 High

### Tasks

#### 2.1 - Install Flask-SocketIO
**Dependencies:**
```bash
pip install flask-socketio python-socketio eventlet
```

**Add to `requirements.txt`:**
```
flask-socketio==5.3.5
python-socketio==5.10.0
eventlet==0.35.1
```

#### 2.2 - Implement camera status WebSocket events
**Server (Flask):**
```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins=['http://localhost:3000'])

@socketio.on('connect', namespace='/ws/camera')
def handle_camera_connect():
    emit('status', {
        'exposure': camera.exposure,
        'iso': camera.iso,
        'mode': camera.mode
    })

def broadcast_camera_update():
    """Call this whenever camera settings change"""
    socketio.emit('status', {
        'exposure': camera.exposure,
        'iso': camera.iso
    }, namespace='/ws/camera')
```

**Client (Next.js):**
```typescript
import { io } from 'socket.io-client'

const socket = io('http://localhost:5000/ws/camera')

socket.on('status', (data) => {
  console.log('Camera status:', data)
  // Update React state
})
```

#### 2.3 - Implement capture status events
**Events to emit:**
- `capture_start` - When capture begins
- `capture_progress` - During long exposures
- `capture_complete` - When image is saved
- `capture_error` - If capture fails

**Example:**
```python
# In camera.capture_file()
socketio.emit('capture_start', {
    'timestamp': time.time()
}, namespace='/ws/camera')

# ... capture logic ...

socketio.emit('capture_complete', {
    'filename': filename,
    'filepath': filepath
}, namespace='/ws/camera')
```

#### 2.4 - Implement session progress events
**Events:**
- `session_start` - Session begins
- `session_progress` - After each image (count, elapsed time)
- `session_complete` - Session finishes
- `session_error` - If session fails

#### 2.5 - Implement mount tracking events
**Events:**
- `tracking_start` - Tracking begins
- `tracking_stop` - Tracking stops
- `mount_position` - Position updates (RA/Dec)

#### 2.6 - Add WebSocket namespace organization
**Namespaces:**
- `/ws/camera` - Camera-related events
- `/ws/mount` - Mount-related events
- `/ws/session` - Session-related events

**Why namespaces:** Separate concerns, easier to manage connections

---

## Phase 3: Next.js Frontend Configuration
**Goal:** Configure Next.js to communicate with Flask  
**Time Estimate:** 2-3 hours  
**Complexity:** 🟢 Low

### Tasks

#### 3.1 - Configure API proxy in next.config.mjs
**File:** `wanda-telescope/next.config.mjs`

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:5000/api/:path*',
      },
      {
        source: '/video_feed',
        destination: 'http://localhost:5000/video_feed',
      },
      {
        source: '/socket.io/:path*',
        destination: 'http://localhost:5000/socket.io/:path*',
      },
    ]
  },
}

export default nextConfig
```

**Why:** In development, Next.js proxies API requests to Flask seamlessly

#### 3.2 - Create API client utility
**File:** `wanda-telescope/lib/api-client.ts`

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api'

export async function apiCall<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }

  const data = await response.json()
  
  if (!data.success) {
    throw new Error(data.error || 'Unknown error')
  }

  return data.data
}

// Usage examples:
// const status = await apiCall<CameraStatus>('/camera/status')
// await apiCall('/camera/capture', { method: 'POST' })
```

#### 3.3 - Install socket.io-client
```bash
cd wanda-telescope
npm install socket.io-client
```

#### 3.4 - Create WebSocket hook
**File:** `wanda-telescope/lib/hooks/useWebSocket.ts`

```typescript
'use client'

import { useEffect, useState } from 'react'
import { io, Socket } from 'socket.io-client'

export function useWebSocket(namespace: string) {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    const socketInstance = io(`http://localhost:5000${namespace}`)

    socketInstance.on('connect', () => {
      setIsConnected(true)
      console.log(`Connected to ${namespace}`)
    })

    socketInstance.on('disconnect', () => {
      setIsConnected(false)
      console.log(`Disconnected from ${namespace}`)
    })

    setSocket(socketInstance)

    return () => {
      socketInstance.disconnect()
    }
  }, [namespace])

  return { socket, isConnected }
}
```

**Usage in components:**
```typescript
const { socket, isConnected } = useWebSocket('/ws/camera')

useEffect(() => {
  if (!socket) return

  socket.on('status', (data) => {
    setCameraStatus(data)
  })

  return () => {
    socket.off('status')
  }
}, [socket])
```

#### 3.5 - Create environment configuration
**File:** `wanda-telescope/.env.local`

```bash
# Development
NEXT_PUBLIC_API_URL=http://localhost:5000/api
NEXT_PUBLIC_WS_URL=http://localhost:5000

# Production (will be same server through Nginx)
# NEXT_PUBLIC_API_URL=/api
# NEXT_PUBLIC_WS_URL=
```

**File:** `wanda-telescope/.env.production`

```bash
# Production on Pi (through Nginx)
NEXT_PUBLIC_API_URL=/api
NEXT_PUBLIC_WS_URL=
```

---

## Phase 4: Component Integration
**Goal:** Wire Next.js components to Flask API  
**Time Estimate:** 6-8 hours  
**Complexity:** 🔴 High

### Tasks

#### 4.1 - Update CameraControls component
**File:** `wanda-telescope/components/camera-controls.tsx`

**Add API calls:**
```typescript
'use client'

import { useState, useEffect } from 'react'
import { apiCall } from '@/lib/api-client'
import { useWebSocket } from '@/lib/hooks/useWebSocket'

export function CameraControls() {
  const [exposure, setExposure] = useState(1000)
  const [iso, setIso] = useState(800)
  const { socket, isConnected } = useWebSocket('/ws/camera')

  // Listen for real-time updates
  useEffect(() => {
    if (!socket) return

    socket.on('status', (data) => {
      setExposure(data.exposure)
      setIso(data.iso)
    })

    return () => socket.off('status')
  }, [socket])

  const handleExposureChange = async (value: number) => {
    try {
      await apiCall('/camera/settings', {
        method: 'POST',
        body: JSON.stringify({ exposure: value })
      })
      // No need to update state - WebSocket will push update
    } catch (error) {
      console.error('Failed to update exposure:', error)
    }
  }

  return (
    <div>
      <Slider value={exposure} onChange={handleExposureChange} />
      {/* ... rest of component */}
    </div>
  )
}
```

#### 4.2 - Real-time camera status updates
**Display live status:**
- Exposure time (updates when changed)
- ISO setting
- Camera mode (still/video)
- Capture status (ready/capturing/error)
- Last capture timestamp

#### 4.3 - Update ImagePreview component
**File:** `wanda-telescope/components/image-preview.tsx`

```typescript
export function ImagePreview({ showHistogram, showFocusAssist }) {
  return (
    <div className="relative">
      <img 
        src="/video_feed" 
        alt="Live camera feed"
        className="w-full h-full object-contain"
      />
      {showHistogram && <Histogram />}
      {showFocusAssist && <FocusAssist />}
    </div>
  )
}
```

**Note:** MJPEG stream works natively in `<img>` tags

#### 4.4 - Update CapturePanel component
**File:** `wanda-telescope/components/capture-panel.tsx`

```typescript
const handleCapture = async () => {
  try {
    setIsCapturing(true)
    
    const result = await apiCall<{ filename: string }>('/camera/capture', {
      method: 'POST'
    })
    
    toast.success(`Captured: ${result.filename}`)
    
    // Refresh gallery
    await fetchRecentCaptures()
  } catch (error) {
    toast.error('Capture failed')
  } finally {
    setIsCapturing(false)
  }
}
```

#### 4.5 - Implement image gallery
**Fetch recent captures:**
```typescript
const [captures, setCaptures] = useState<string[]>([])

useEffect(() => {
  const fetchCaptures = async () => {
    const data = await apiCall<{ files: string[] }>('/captures')
    setCaptures(data.files)
  }
  
  fetchCaptures()
  
  // Refresh every 5 seconds
  const interval = setInterval(fetchCaptures, 5000)
  return () => clearInterval(interval)
}, [])
```

**Display thumbnails:**
```typescript
<div className="grid grid-cols-2 gap-2">
  {captures.map((filename) => (
    <img 
      key={filename}
      src={`/api/captures/${filename}`}
      alt={filename}
      className="rounded cursor-pointer hover:opacity-80"
    />
  ))}
</div>
```

#### 4.6 - Update StatusBar component
**File:** `wanda-telescope/components/status-bar.tsx`

```typescript
export function StatusBar() {
  const [status, setStatus] = useState('Ready')
  const { socket } = useWebSocket('/ws/camera')

  useEffect(() => {
    if (!socket) return

    socket.on('capture_start', () => setStatus('Capturing...'))
    socket.on('capture_complete', () => setStatus('Ready'))
    socket.on('capture_error', (err) => setStatus(`Error: ${err.message}`))

    return () => {
      socket.off('capture_start')
      socket.off('capture_complete')
      socket.off('capture_error')
    }
  }, [socket])

  return (
    <div className="status-bar">
      <span>{status}</span>
    </div>
  )
}
```

#### 4.7 - Implement Mount controls tab
**Features:**
- Start/Stop tracking button
- Current tracking status
- Manual position adjustment (future)
- RA/Dec display (future)

#### 4.8 - Implement Session controls tab
**Features:**
- Start session form (count, interval, duration)
- Stop session button
- Progress display (X/Y images captured)
- Elapsed time counter
- Recent session images

---

## Phase 5: Development Environment Setup
**Goal:** Test on Raspberry Pi in development mode  
**Time Estimate:** 2-3 hours  
**Complexity:** 🟢 Low

### Tasks

#### 5.1 - Install Node.js 20.x on Pi
```bash
# Check current version
node --version

# If not 20.x, install:
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify
node --version  # Should be v20.x.x
npm --version   # Should be 10.x.x
```

#### 5.2 - Install dependencies
```bash
cd /home/admin/wanda-telescope/wanda-telescope
npm install
```

**Note:** This may take 10-15 minutes on Pi. Be patient!

#### 5.3 - Test Flask API in isolation
```bash
# Activate venv
cd /home/admin/wanda-telescope
source venv/bin/activate

# Run Flask
python main.py
```

**Test with curl:**
```bash
# In another terminal
curl http://localhost:5000/api/camera/status
# Should return JSON

curl -X POST http://localhost:5000/api/camera/capture
# Should trigger capture
```

#### 5.4 - Test Next.js dev server
```bash
cd /home/admin/wanda-telescope/wanda-telescope
npm run dev
```

**Access:** `http://raspberry-pi-ip:3000`

**Verify:**
- Page loads
- API calls work (check Network tab in browser DevTools)
- No CORS errors

#### 5.5 - Test WebSocket connections
**In browser console:**
```javascript
// Should see "Connected to /ws/camera" in console
```

**Trigger updates:**
- Change camera settings
- Verify UI updates in real-time without page refresh

#### 5.6 - Test camera capture end-to-end
1. Click "Capture" button in UI
2. Verify loading state appears
3. Check Flask logs for capture activity
4. Verify image saved to `captures/`
5. Verify gallery updates with new image
6. Verify success notification appears

---

## Phase 6: Production Build
**Goal:** Build optimized Next.js for production  
**Time Estimate:** 1-2 hours  
**Complexity:** 🟢 Low

### Tasks

#### 6.1 - Build Next.js
```bash
cd /home/admin/wanda-telescope/wanda-telescope
npm run build
```

**Output:**
```
Route (app)                              Size     First Load JS
┌ ○ /                                    5.2 kB         87.3 kB
└ ○ /favicon.ico                         0 B                0 B

○ (Static)  prerendered as static content
```

#### 6.2 - Test production build
```bash
npm start
```

**Access:** `http://raspberry-pi-ip:3000`

**Verify:**
- Faster page loads (optimized bundle)
- All features work
- No console errors

#### 6.3 - Verify static assets
**Check:**
- Fonts load correctly (Geist Sans, Geist Mono)
- Images load
- CSS styling applied
- No 404 errors in DevTools

#### 6.4 - Check bundle size
**Target:** < 5MB total JavaScript

**If too large:**
- Check for unused dependencies
- Use dynamic imports for large components
- Optimize images

---

## Phase 7: Systemd Service Configuration
**Goal:** Run both services automatically on boot  
**Time Estimate:** 2-3 hours  
**Complexity:** 🟡 Medium

### Tasks

#### 7.1 - Create wanda-backend.service
**File:** `/etc/systemd/system/wanda-backend.service`

```ini
[Unit]
Description=Wanda Telescope Backend API
After=network.target
Documentation=https://github.com/yourusername/wanda-telescope

[Service]
Type=simple
User=admin
Group=admin
WorkingDirectory=/home/admin/wanda-telescope
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/admin/wanda-telescope/venv/bin/python main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Create file:**
```bash
sudo nano /etc/systemd/system/wanda-backend.service
# Paste content above
```

#### 7.2 - Create wanda-frontend.service
**File:** `/etc/systemd/system/wanda-frontend.service`

```ini
[Unit]
Description=Wanda Telescope Next.js Frontend
After=network.target wanda-backend.service
Requires=wanda-backend.service
Documentation=https://github.com/yourusername/wanda-telescope

[Service]
Type=simple
User=admin
Group=admin
WorkingDirectory=/home/admin/wanda-telescope/wanda-telescope
Environment="NODE_ENV=production"
Environment="PORT=3000"
ExecStart=/usr/bin/npm start
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### 7.3 - Configure service dependencies
**Already done:** `Requires=wanda-backend.service` ensures backend starts first

#### 7.4 - Set up restart policies
**Already configured:**
- `Restart=on-failure` - Restart if crashes
- `RestartSec=10` - Wait 10 seconds before restart

#### 7.5 - Enable services
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable wanda-backend.service
sudo systemctl enable wanda-frontend.service

# Start services now
sudo systemctl start wanda-backend.service
sudo systemctl start wanda-frontend.service
```

#### 7.6 - Test service commands
```bash
# Check status
sudo systemctl status wanda-backend.service
sudo systemctl status wanda-frontend.service

# View logs
sudo journalctl -u wanda-backend.service -f
sudo journalctl -u wanda-frontend.service -f

# Restart services
sudo systemctl restart wanda-backend.service
sudo systemctl restart wanda-frontend.service

# Stop services
sudo systemctl stop wanda-backend.service
sudo systemctl stop wanda-frontend.service
```

---

## Phase 8: Nginx Reverse Proxy Setup
**Goal:** Unified access through port 80  
**Time Estimate:** 2-3 hours  
**Complexity:** 🟡 Medium

### Tasks

#### 8.1 - Install Nginx
```bash
sudo apt update
sudo apt install nginx -y

# Verify installation
nginx -v
```

#### 8.2 - Create Nginx configuration
**File:** `/etc/nginx/sites-available/wanda`

```nginx
server {
    listen 80;
    server_name wanda.local _;

    # Access logs
    access_log /var/log/nginx/wanda-access.log;
    error_log /var/log/nginx/wanda-error.log;

    # Next.js frontend (default)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Flask API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket connections
    location /socket.io {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # MJPEG video feed
    location /video_feed {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_buffering off;
        proxy_cache off;
    }

    # Captured images
    location /captures {
        alias /home/admin/wanda-telescope/captures;
        autoindex off;
        add_header Cache-Control "public, max-age=3600";
    }
}
```

**Create file:**
```bash
sudo nano /etc/nginx/sites-available/wanda
# Paste content above
```

#### 8.3-8.4 - Proxy pass configuration
**Already configured in step 8.2**

#### 8.5 - Configure WebSocket headers
**Already configured in step 8.2** - `location /socket.io` block

#### 8.6 - Enable site and test
```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/wanda /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t
# Should output: "syntax is ok" and "test is successful"
```

#### 8.7 - Restart Nginx
```bash
sudo systemctl restart nginx
sudo systemctl status nginx

# Enable on boot (if not already)
sudo systemctl enable nginx
```

**Test access:** `http://raspberry-pi-ip/`

---

## Phase 9: Testing & Validation
**Goal:** Comprehensive testing of full system  
**Time Estimate:** 3-4 hours  
**Complexity:** 🟡 Medium

### Tasks

#### 9.1 - Test capture workflow
**Steps:**
1. Open `http://raspberry-pi-ip/` in browser
2. Adjust exposure slider
3. Verify real-time update (check value in UI)
4. Click "Capture" button
5. Verify loading spinner appears
6. Wait for capture to complete
7. Verify success notification
8. Check gallery for new image
9. Verify image can be viewed full-size

**Expected:** < 3 seconds from button click to image appearing

#### 9.2 - Test video streaming
**Metrics to verify:**
- Frame rate: ~30 fps
- Latency: < 100ms
- No stuttering or buffering
- Stream recovers if network hiccup

**Test:**
1. Open live feed
2. Wave hand in front of camera
3. Verify smooth motion in browser
4. Check browser DevTools Network tab (video_feed connection)

#### 9.3 - Test WebSocket real-time updates
**Test:**
1. Open browser DevTools Console
2. Change exposure slider
3. Verify WebSocket message received (check Network > WS tab)
4. Open same page in second browser tab
5. Change setting in tab 1
6. Verify tab 2 updates automatically

#### 9.4 - Test mount controls
**Steps:**
1. Navigate to "Mount" tab
2. Click "Start Tracking"
3. Verify status changes to "Tracking"
4. Click "Stop Tracking"
5. Verify status changes to "Stopped"

#### 9.5 - Test session workflow
**Steps:**
1. Navigate to "Session" tab
2. Enter settings (5 images, 10 second interval)
3. Click "Start Session"
4. Verify progress counter updates (1/5, 2/5, etc.)
5. Verify images appear in gallery
6. Verify session completes automatically
7. Test "Stop Session" button (manual stop)

#### 9.6 - Test error handling
**Scenarios:**
1. **Disconnect camera cable**
   - Capture should fail gracefully
   - Error message displayed in UI
   - No crash

2. **Restart Flask service**
   - WebSocket should reconnect automatically
   - UI should show "Reconnecting..." status

3. **Invalid settings**
   - Try exposure > max value
   - Should show validation error

4. **Network error**
   - Kill Flask process
   - UI should handle failed requests gracefully

#### 9.7 - Test system restart
```bash
sudo reboot
```

**After reboot:**
1. Wait 60 seconds for services to start
2. Access `http://raspberry-pi-ip/`
3. Verify both services running:
   ```bash
   sudo systemctl status wanda-backend.service
   sudo systemctl status wanda-frontend.service
   ```
4. Test capture workflow
5. Test WebSocket connection

#### 9.8 - Run Python test suite
```bash
cd /home/admin/wanda-telescope
source venv/bin/activate
pytest tests/ --cov --cov-report=html

# Verify:
# - All tests pass
# - Coverage >= 85%
```

---

## Phase 10: Documentation & Cleanup
**Goal:** Document new architecture and remove old code  
**Time Estimate:** 2-3 hours  
**Complexity:** 🟢 Low

### Tasks

#### 10.1 - Update main README.md
**Add sections:**
- Architecture diagram (copy from this doc)
- New setup instructions
- How to run in development
- How to deploy to production
- Troubleshooting guide

#### 10.2 - Create DEPLOYMENT.md
**Contents:**
- Prerequisites (Node.js, Python, Nginx)
- Step-by-step deployment guide
- Systemd service setup
- Nginx configuration
- Common issues and solutions

#### 10.3 - Document API endpoints
**Create:** `docs/API.md`

**Format:**
```markdown
# API Documentation

## Camera Endpoints

### GET /api/camera/status
Returns current camera status.

**Response:**
```json
{
  "success": true,
  "data": {
    "exposure": 1000,
    "iso": 800,
    "mode": "still"
  }
}
```

### POST /api/camera/capture
Captures a single image.

**Response:**
```json
{
  "success": true,
  "data": {
    "filename": "capture_1234567890.jpg",
    "filepath": "/home/admin/wanda-telescope/captures/capture_1234567890.jpg"
  }
}
```
```

#### 10.4 - Document WebSocket events
**Create:** `docs/WEBSOCKETS.md`

**Format:**
```markdown
# WebSocket Events

## Camera Namespace: /ws/camera

### Server → Client Events

#### `status`
Emitted when camera settings change.

**Payload:**
```json
{
  "exposure": 1000,
  "iso": 800,
  "mode": "still"
}
```

#### `capture_complete`
Emitted when image capture completes.

**Payload:**
```json
{
  "filename": "capture_1234567890.jpg",
  "timestamp": 1234567890
}
```
```

#### 10.5 - Remove old Flask templates
```bash
# These are no longer used (Next.js replaced them)
rm -rf web/templates/
```

**Keep only:**
- `web/app.py` (Flask API)
- `web/__init__.py`

#### 10.6 - Remove old static assets
```bash
# Remove old CSS/JS that were manually ported
rm web/static/css/wanda-ui.css
rm web/static/css/shadcn.css
rm web/static/js/wanda-ui.js
rm web/static/js/ajax-utils.js
```

**Keep:**
- `web/static/img/` (if any static images)

#### 10.7 - Update v0-report.md
**Add section:**
```markdown
## Update: Full Next.js Integration

As of [DATE], we completed full integration of the v0-generated Next.js
application. The initial manual port to Flask templates has been replaced
with a proper decoupled architecture:

- **Frontend:** Next.js (React) running on port 3000
- **Backend:** Flask API running on port 5000
- **Communication:** REST API + WebSockets + MJPEG streaming
- **Deployment:** Both services on Raspberry Pi 5, unified via Nginx

This allows us to use v0 components directly without manual translation,
provides a modern development experience, and enables real-time updates
via WebSockets.

See `NEXTJS_INTEGRATION_PLAN.md` for full architecture details.
```

---

## Technical Specifications

### Dependencies

**Backend (Python):**
```txt
flask==3.0.0
flask-cors==4.0.0
flask-socketio==5.3.5
python-socketio==5.10.0
eventlet==0.35.1
picamera2>=0.3.13
numpy<2.0.0
```

**Frontend (Node.js):**
```json
{
  "dependencies": {
    "next": "14.2.25",
    "react": "^19",
    "react-dom": "^19",
    "socket.io-client": "^4.7.0"
  }
}
```

### Port Allocation

| Service | Port | Access |
|---------|------|--------|
| Flask API | 5000 | Internal only |
| Next.js | 3000 | Internal only |
| Nginx | 80 | Public (local network) |
| Nginx SSL | 443 | Future (Cloudflare) |

### Resource Requirements

**Raspberry Pi 5:**
- RAM: 4GB minimum (8GB recommended)
- Storage: 16GB free (for captures)
- Network: 100 Mbps Ethernet recommended

**Expected usage:**
- Flask: ~200MB RAM
- Next.js: ~300-500MB RAM
- Nginx: ~10MB RAM
- Total: ~600-800MB RAM

---

## Timeline & Milestones

| Phase | Duration | Milestone |
|-------|----------|-----------|
| Phase 1 | Day 1 AM | Flask API ready |
| Phase 2 | Day 1 PM | WebSockets working |
| Phase 3 | Day 2 AM | Next.js configured |
| Phase 4 | Day 2-3 | Components wired up |
| Phase 5 | Day 3 | Dev environment tested |
| Phase 6 | Day 3 | Production build ready |
| Phase 7 | Day 4 | Services configured |
| Phase 8 | Day 4 | Nginx deployed |
| Phase 9 | Day 5 AM | Full system tested |
| Phase 10 | Day 5 PM | Documentation complete |

---

## Success Criteria

✅ **Functionality:**
- [ ] Camera capture works via UI
- [ ] Real-time settings update in UI
- [ ] Video feed streams smoothly (30fps)
- [ ] Mount controls functional
- [ ] Session automation works
- [ ] WebSocket reconnection handles network issues

✅ **Performance:**
- [ ] Page load < 2 seconds
- [ ] Capture latency < 3 seconds
- [ ] Video latency < 100ms
- [ ] WebSocket updates < 50ms

✅ **Reliability:**
- [ ] Services start on boot
- [ ] Services auto-restart on failure
- [ ] Python tests pass (>85% coverage)
- [ ] No memory leaks (24hr test)

✅ **Documentation:**
- [ ] README updated
- [ ] API documented
- [ ] WebSocket events documented
- [ ] Deployment guide complete

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| WebSocket connection drops | Implement auto-reconnect with exponential backoff |
| Next.js consumes too much RAM | Monitor with `htop`, optimize bundle size |
| MJPEG stream bandwidth high | Reduce resolution or frame rate if needed |
| Services fail to start on boot | Test with multiple reboots, check logs |
| CORS issues in production | Ensure Nginx properly routes all requests |

---

## Future Enhancements (Post-Integration)

- [ ] Add Cloudflare Tunnel for internet access
- [ ] Implement user authentication (JWT)
- [ ] Add HTTPS support
- [ ] Optimize video streaming (HLS or WebRTC)
- [ ] Add mobile-responsive design
- [ ] Implement image processing pipeline
- [ ] Add database for capture metadata
- [ ] Create admin dashboard

---

## Support & Troubleshooting

### Common Issues

**Issue: Next.js won't start**
```bash
# Check Node version
node --version  # Should be 20.x

# Clear cache and reinstall
rm -rf node_modules package-lock.json .next
npm install
npm run build
```

**Issue: WebSocket connection refused**
```bash
# Check Flask is running with SocketIO
sudo systemctl status wanda-backend.service
sudo journalctl -u wanda-backend.service -n 50

# Verify port 5000 listening
sudo netstat -tulpn | grep 5000
```

**Issue: 502 Bad Gateway (Nginx)**
```bash
# Check backend services
sudo systemctl status wanda-backend.service
sudo systemctl status wanda-frontend.service

# Check Nginx error logs
sudo tail -f /var/log/nginx/wanda-error.log
```

### Useful Commands

```bash
# View all service logs
sudo journalctl -f

# Restart everything
sudo systemctl restart wanda-backend wanda-frontend nginx

# Check resource usage
htop

# Test API directly
curl http://localhost:5000/api/camera/status

# Test through Nginx
curl http://localhost/api/camera/status
```

---

## Contact & Resources

- **Project Repository:** [Your GitHub URL]
- **Issue Tracker:** [GitHub Issues]
- **Documentation:** `docs/` directory
- **Flask-SocketIO Docs:** https://flask-socketio.readthedocs.io/
- **Next.js Docs:** https://nextjs.org/docs

---

**Document Version:** 1.0  
**Last Updated:** [Current Date]  
**Status:** Ready for Implementation


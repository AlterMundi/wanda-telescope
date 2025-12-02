# IPFS Integration for WANDA

## What is IPFS (Quick Overview)

IPFS (InterPlanetary File System) is a peer-to-peer network for storing and sharing files. Key concepts:

- **Content-addressed**: Files are identified by their hash (CID), not location
- **Decentralized**: No central server—files live across multiple peers
- **Immutable**: Same content = same CID, always

## Why IPFS for WANDA?

1. **Share captures across WANDA nodes** without central server
2. **Content verification** via CIDs (hashes)
3. **Resilient storage** across distributed telescope network
4. **Natural fit** for mesh/community networks (AlterMundi use case)

---

## Recommended Approach: Kubo + py-ipfs-api

### 1. Install Kubo (IPFS daemon) on Raspberry Pi

```bash
# Download Kubo for ARM
wget https://dist.ipfs.tech/kubo/v0.32.1/kubo_v0.32.1_linux-arm64.tar.gz
tar -xvzf kubo_v0.32.1_linux-arm64.tar.gz
cd kubo
sudo ./install.sh

# Initialize IPFS
ipfs init

# Start daemon (will run as service)
ipfs daemon &
```

### 2. Python Integration

Install the HTTP API client:

```bash
pip install ipfshttpclient
```

Basic usage:

```python
import ipfshttpclient

# Connect to local IPFS daemon
client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

# Add a file → returns CID
result = client.add('captures/session_001/image_0001.jpg')
cid = result['Hash']  # e.g., "QmXyz..."

# Add entire session folder
result = client.add('captures/session_001', recursive=True)

# Retrieve file by CID
client.get(cid, target='./downloads/')
```

---

## Integration Points in WANDA

### Option A: Post-Capture Hook (Simplest)

Modify `session/controller.py` to pin images after capture:

```python
# In _capture_session_image() after successful capture:
if self.ipfs_enabled:
    cid = self.ipfs_client.add(filename)['Hash']
    self._save_cid_to_metadata(image_number, cid)
```

### Option B: Batch Upload on Session Complete

Pin entire session folder when session finishes:

```python
# In stop_session() or session_complete:
result = self.ipfs_client.add(session_dir, recursive=True)
session_cid = result[-1]['Hash']  # Root folder CID
```

---

## Minimal Implementation Plan

1. **Create `utils/ipfs.py`** - IPFS client wrapper with connect/add/get
2. **Add config options** - `IPFS_ENABLED`, `IPFS_API_ADDR` in `config.py`
3. **Modify `SessionController`** - Add CIDs to session metadata
4. **Add API endpoint** - `GET /api/session/<name>/ipfs` for CID info

---

## Discovery Between WANDA Nodes

For nodes to find each other on local mesh networks:

```bash
# On each node, advertise via mDNS (enabled by default)
ipfs config --json Discovery.MDNS.Enabled true

# Or manually connect peers
ipfs swarm connect /ip4/<peer-ip>/tcp/4001/p2p/<peer-id>
```

---

## Recommended Architecture: RPi Light Node + Server Storage

To keep RPi storage minimal, offload actual images to a server:

```
┌─────────────────────────────────────────────────────────────────┐
│                         CAPTURE FLOW                            │
└─────────────────────────────────────────────────────────────────┘

  RPi (WANDA node)                         Server
  ───────────────                          ──────
       │
  1. Capture image
       │
  2. ipfs add → get CID
       │
  3. ─────── Send image to server ───────────→  Server receives & pins
       │                                              │
  4. Delete local image                         Image stored permanently
       │
  5. Save CID to session_metadata.json
       │
       ▼
  ┌─────────────────┐
  │ session_001/    │
  │   metadata.json │  ← only CIDs, no images!
  │   (CID list)    │
  └─────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                         DISPLAY FLOW                            │
└─────────────────────────────────────────────────────────────────┘

  App requests image
       │
       ▼
  ipfs://<CID>  or  https://ipfs.io/ipfs/<CID>
       │
       ▼
  IPFS network resolves → Server serves the file
```

**What the RPi keeps:**
```json
{
  "name": "session_001",
  "images": [
    { "number": 1, "cid": "QmXyz123..." },
    { "number": 2, "cid": "QmAbc456..." }
  ]
}
```

**What the server keeps:**
- Actual image files pinned in IPFS

### Why This Works

1. **RPi stays lightweight** — just metadata, no image bloat
2. **Server = persistent storage** — handles the heavy lifting
3. **IPFS = universal addressing** — any gateway can serve `ipfs://CID`
4. **RPi is still a node** — helps with discovery, can cache popular images
5. **Decoupled** — server could be AlterMundi infra, Pinata, or any IPFS pinner

### Frontend Display (Next.js)

```tsx
const IPFS_GATEWAY = "https://ipfs.io/ipfs/";

<img src={`${IPFS_GATEWAY}${image.cid}`} />
```

---

## Next Steps

1. [ ] Install Kubo on a test Pi
2. [ ] Create `utils/ipfs.py` with basic add/get operations
3. [ ] Set up server with IPFS pinning
4. [ ] Add CID tracking to session metadata
5. [ ] Build frontend to display images via IPFS gateway


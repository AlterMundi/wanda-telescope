# IPFS Integration for WANDA

## What is IPFS (Quick Overview)

IPFS (InterPlanetary File System) is a peer-to-peer network for storing and sharing files. Key concepts:

- **Content-addressed**: Files are identified by their hash (CID), not location
- **Decentralized**: No central server—files live across multiple peers
- **Immutable**: Same content = same CID, always

## What is IPFS Cluster?

[IPFS Cluster](https://ipfscluster.io/) is a distributed application that runs alongside IPFS daemons to orchestrate pinning across multiple nodes:

- **Automated replication**: Pin to N nodes with configurable replication factor
- **Fire & forget**: Cluster tracks pins, retries failures automatically
- **Single API**: One endpoint to manage pins across all storage nodes
- **Follower peers**: Nodes that store content without modification permissions (perfect for AlterMundi infra)

## Why IPFS + Cluster for WANDA?

1. **Share captures across WANDA nodes** without central server
2. **Content verification** via CIDs (hashes)
3. **Resilient storage** with automatic replication across nodes
4. **Natural fit** for mesh/community networks (AlterMundi use case)
5. **Future-proof** for scaling to multiple storage servers

---

## Architecture: RPi Light Node + Server Cluster

```
┌─────────────────────────────────────────────────────────────────┐
│                         CAPTURE FLOW                            │
└─────────────────────────────────────────────────────────────────┘

  RPi (WANDA node)                      Server(s) + IPFS Cluster
  ───────────────                       ────────────────────────
       │
  1. Capture image
       │
  2. ipfs add → get CID
       │
  3. ─────── POST to Cluster API ──────────→  Cluster receives CID
       │                                              │
       │                                     Replicates pin to N peers
       │                                              │
  4. Delete local image                      Images stored redundantly
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
  IPFS network resolves → Cluster node serves the file
```

---

## Installation

### 1. RPi (WANDA Node) — Kubo Only

The RPi just needs a basic IPFS daemon for `ipfs add`:

```bash
# Download Kubo for ARM
wget https://dist.ipfs.tech/kubo/v0.32.1/kubo_v0.32.1_linux-arm64.tar.gz
tar -xvzf kubo_v0.32.1_linux-arm64.tar.gz
cd kubo
sudo ./install.sh

# Initialize and start
ipfs init
ipfs daemon &
```

### 2. Server — Kubo + IPFS Cluster

```bash
# Install Kubo (same as above, use amd64 for server)
wget https://dist.ipfs.tech/kubo/v0.32.1/kubo_v0.32.1_linux-amd64.tar.gz
tar -xvzf kubo_v0.32.1_linux-amd64.tar.gz
cd kubo && sudo ./install.sh
ipfs init && ipfs daemon &

# Install IPFS Cluster
wget https://dist.ipfs.tech/ipfs-cluster-service/v1.1.1/ipfs-cluster-service_v1.1.1_linux-amd64.tar.gz
tar -xvzf ipfs-cluster-service_v1.1.1_linux-amd64.tar.gz
cd ipfs-cluster-service && sudo ./install.sh

# Initialize cluster (generates secret)
ipfs-cluster-service init

# Start cluster service
ipfs-cluster-service daemon &
```

### 3. Add Follower Nodes (Additional Servers)

For additional storage nodes (e.g., AlterMundi infrastructure):

```bash
# On follower node, init with the cluster secret from primary
ipfs-cluster-service init --secret <CLUSTER_SECRET>

# Or init as follower (read-only, can't modify pinset)
ipfs-cluster-follow <cluster-name> init <config-url>
ipfs-cluster-follow <cluster-name> run
```

---

## Python Integration

### RPi Side — Add to IPFS + Notify Cluster

```bash
pip install ipfshttpclient requests
```

```python
import ipfshttpclient
import requests

# Local IPFS daemon
ipfs = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

# Cluster API endpoint (on server)
CLUSTER_API = "http://<server-ip>:9094"

def add_and_pin_to_cluster(filepath: str) -> str:
    """Add file locally, then tell cluster to pin it."""
    # 1. Add to local IPFS → get CID
    result = ipfs.add(filepath)
    cid = result['Hash']
    
    # 2. Tell cluster to pin this CID
    response = requests.post(
        f"{CLUSTER_API}/pins/{cid}",
        params={"replication-min": 2, "replication-max": 3}
    )
    response.raise_for_status()
    
    return cid

def get_pin_status(cid: str) -> dict:
    """Check pin status across cluster."""
    response = requests.get(f"{CLUSTER_API}/pins/{cid}")
    return response.json()
```

### Server Side — Cluster REST API

The cluster exposes a REST API on port `9094` by default:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/pins/{cid}` | POST | Pin a CID to the cluster |
| `/pins/{cid}` | DELETE | Unpin from cluster |
| `/pins/{cid}` | GET | Get pin status |
| `/pins` | GET | List all pins |
| `/peers` | GET | List cluster peers |

---

## Integration Points in WANDA

### Option A: Post-Capture Hook

Modify `session/controller.py` to pin images after capture:

```python
# In _capture_session_image() after successful capture:
if self.ipfs_enabled:
    cid = self.ipfs_service.add_and_pin(filename)
    self._save_cid_to_metadata(image_number, cid)
    if self.delete_after_pin:
        os.remove(filename)  # RPi stays lightweight
```

### Option B: Batch Upload on Session Complete

Pin entire session folder when session finishes:

```python
# In stop_session() or session_complete:
cids = []
for image_path in session_images:
    cid = self.ipfs_service.add_and_pin(image_path)
    cids.append(cid)
# Save all CIDs to session metadata
```

---

## Minimal Implementation Plan

1. **Create `utils/ipfs_service.py`**
   - IPFS client wrapper (connect, add)
   - Cluster API client (pin, status, unpin)
   - Retry logic for network failures

2. **Add config options to `config.py`**
   ```python
   IPFS_ENABLED = True
   IPFS_API_ADDR = '/ip4/127.0.0.1/tcp/5001'
   IPFS_CLUSTER_API = 'http://<server-ip>:9094'
   IPFS_DELETE_AFTER_PIN = True  # Keep RPi lightweight
   IPFS_REPLICATION_MIN = 2
   IPFS_REPLICATION_MAX = 3
   ```

3. **Modify `SessionController`**
   - Add CIDs to session metadata
   - Optional: delete local files after cluster confirms pin

4. **Add API endpoints**
   - `GET /api/session/<name>/ipfs` — list CIDs for session
   - `GET /api/ipfs/status/<cid>` — check pin status

5. **Frontend display**
   ```tsx
   const IPFS_GATEWAY = "https://ipfs.io/ipfs/";
   // Or use cluster's gateway if configured
   <img src={`${IPFS_GATEWAY}${image.cid}`} />
   ```

---

## Discovery Between Nodes

For nodes to find each other on local mesh networks:

```bash
# mDNS discovery (enabled by default)
ipfs config --json Discovery.MDNS.Enabled true

# Manual peer connection
ipfs swarm connect /ip4/<peer-ip>/tcp/4001/p2p/<peer-id>

# Cluster peers connect automatically via shared secret
```

---

## Session Metadata Format

```json
{
  "name": "session_001",
  "created": "2025-12-03T10:30:00Z",
  "ipfs": {
    "enabled": true,
    "cluster": "http://192.168.1.100:9094"
  },
  "images": [
    { "number": 1, "cid": "QmXyz123...", "pinned": true },
    { "number": 2, "cid": "QmAbc456...", "pinned": true }
  ]
}
```

---


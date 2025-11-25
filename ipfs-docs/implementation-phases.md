# WANDA IPFS Implementation Phases

## Overview

This document outlines a phased approach to implementing IPFS in WANDA. Each phase builds upon the previous one, allowing for incremental testing and validation.

## Phase Overview

```mermaid
gantt
    title WANDA IPFS Implementation Timeline
    dateFormat  YYYY-MM-DD
    section Phase 1
    IPFS Daemon Setup           :p1a, 2025-01-01, 3d
    Python IPFS Client          :p1b, after p1a, 4d
    Basic Add/Get Operations    :p1c, after p1b, 3d
    Unit Tests                  :p1d, after p1c, 2d
    
    section Phase 2
    Storage Router              :p2a, after p1d, 3d
    Camera Integration          :p2b, after p2a, 3d
    Session Integration         :p2c, after p2b, 2d
    API Endpoints               :p2d, after p2c, 3d
    Integration Tests           :p2e, after p2d, 2d
    
    section Phase 3
    Frontend Components         :p3a, after p2e, 4d
    WebSocket Events            :p3b, after p3a, 2d
    IPFS Gallery View           :p3c, after p3b, 3d
    
    section Phase 4
    Peer Discovery              :p4a, after p3c, 3d
    Network Sync                :p4b, after p4a, 3d
    IPNS Publishing             :p4c, after p4b, 2d
    
    section Phase 5
    Performance Optimization    :p5a, after p4c, 3d
    Documentation               :p5b, after p5a, 2d
    Production Testing          :p5c, after p5b, 3d
```

---

## Phase 1: Core IPFS Integration

**Duration:** 2 weeks  
**Goal:** Establish IPFS foundation with basic operations

### 1.1 IPFS Daemon Setup

```mermaid
flowchart LR
    subgraph "Deliverables"
        A["Install Kubo<br/>on Raspberry Pi"]
        B["Create systemd<br/>service file"]
        C["Configure for<br/>low-power mode"]
        D["Verify daemon<br/>operations"]
    end
    
    A --> B --> C --> D
```

**Tasks:**
- [ ] Download and install Kubo v0.25+ for ARM64
- [ ] Create `wanda-ipfs.service` systemd unit file
- [ ] Configure IPFS with `lowpower` profile for Raspberry Pi
- [ ] Set up automatic startup on boot
- [ ] Configure firewall rules for IPFS ports (4001, 5001, 8080)

**Configuration Example:**
```bash
# Initialize with low-power profile
ipfs init --profile=lowpower

# Additional configuration
ipfs config --json Swarm.ConnMgr.LowWater 50
ipfs config --json Swarm.ConnMgr.HighWater 100
ipfs config --json Datastore.StorageMax '"10GB"'
```

### 1.2 Python IPFS Client Module

```mermaid
classDiagram
    class IPFSClient {
        -str api_url
        -Session http_session
        +__init__(api_url)
        +add(file_path) CID
        +cat(cid) bytes
        +pin_add(cid) bool
        +pin_rm(cid) bool
        +pin_ls() List~CID~
        +id() PeerInfo
        +swarm_peers() List~Peer~
    }
    
    class IPFSService {
        -IPFSClient client
        -Logger logger
        +add_file(path) CID
        +get_file(cid, dest) bool
        +is_pinned(cid) bool
        +get_stats() Stats
    }
    
    class CID {
        +str hash
        +int version
        +str codec
        +__str__() str
    }
    
    IPFSService --> IPFSClient
    IPFSClient --> CID
```

**Tasks:**
- [ ] Create `ipfs/` module directory
- [ ] Implement `ipfs/client.py` - HTTP API wrapper
- [ ] Implement `ipfs/service.py` - High-level service layer
- [ ] Implement `ipfs/models.py` - Data models (CID, PeerInfo)
- [ ] Implement `ipfs/config.py` - Configuration settings
- [ ] Add connection pooling and retry logic

### 1.3 Basic Add/Get Operations

**Tasks:**
- [ ] Implement file addition with automatic pinning
- [ ] Implement file retrieval by CID
- [ ] Add support for directory operations
- [ ] Implement local caching layer
- [ ] Add progress callbacks for large files

### 1.4 Unit Tests

**Tasks:**
- [ ] Create `tests/test_ipfs/` directory
- [ ] Write tests for IPFSClient (mock HTTP responses)
- [ ] Write tests for IPFSService
- [ ] Achieve 85%+ coverage for IPFS module
- [ ] Test error handling and retry logic

**Exit Criteria:**
- ✅ IPFS daemon runs as service and survives reboots
- ✅ Python can add/retrieve files via IPFS
- ✅ All unit tests pass with 85%+ coverage

---

## Phase 2: Storage Integration

**Duration:** 2 weeks  
**Goal:** Integrate IPFS with existing capture workflow

### 2.1 Storage Router

```mermaid
flowchart TD
    subgraph "Storage Router Design"
        A[CaptureEvent] --> B{Storage Router}
        
        B -->|"sync"| C[Local Storage]
        B -->|"async"| D[IPFS Queue]
        
        C --> E[Save to disk]
        E --> F[Generate thumbnail]
        
        D --> G[IPFS Worker]
        G --> H[Add to IPFS]
        H --> I[Pin locally]
        I --> J[Update metadata]
        
        F --> K[Emit event]
        J --> K
        K --> L[WebSocket broadcast]
    end
```

**Tasks:**
- [ ] Create `ipfs/router.py` - Storage routing logic
- [ ] Implement async IPFS upload queue
- [ ] Add metadata tracking (local path → CID mapping)
- [ ] Implement graceful fallback when IPFS unavailable
- [ ] Add queue persistence for crash recovery

### 2.2 Camera Integration

**Tasks:**
- [ ] Modify `AbstractCamera.capture_file()` to use StorageRouter
- [ ] Add CID to capture response
- [ ] Update `capture_status` to include IPFS status
- [ ] Ensure non-blocking IPFS operations

**Code Changes:**
```python
# camera/base.py (conceptual)
def capture_file(self, filename):
    # Existing capture logic...
    result = self._capture_to_file(filename)
    
    # New: Queue for IPFS
    if ipfs_enabled:
        storage_router.queue_for_ipfs(filename)
    
    return result
```

### 2.3 Session Integration

```mermaid
sequenceDiagram
    participant Session as Session Controller
    participant Router as Storage Router
    participant IPFS as IPFS Service
    participant Meta as Metadata Store
    
    Session->>Router: start_session(config)
    Router->>Meta: create_session_record()
    
    loop Each Capture
        Session->>Router: capture_image()
        Router->>Router: save_local()
        Router-->>Session: local_path
        Router->>IPFS: queue_upload(path)
        IPFS-->>Meta: update_cid(image_id, cid)
    end
    
    Session->>Router: end_session()
    Router->>IPFS: create_directory_dag()
    IPFS-->>Meta: update_session_cid()
    Router->>IPFS: publish_ipns()
```

**Tasks:**
- [ ] Update `SessionController` to track CIDs per image
- [ ] Create session directory DAG on completion
- [ ] Add session CID to metadata export
- [ ] Implement session IPNS publishing

### 2.4 REST API Endpoints

**New Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ipfs/status` | IPFS daemon status |
| GET | `/api/ipfs/stats` | Storage and network stats |
| GET | `/api/captures/:id/cid` | Get CID for capture |
| GET | `/api/ipfs/:cid` | Retrieve file by CID |
| POST | `/api/ipfs/pin` | Pin a CID |
| DELETE | `/api/ipfs/pin/:cid` | Unpin a CID |
| GET | `/api/ipfs/peers` | List connected peers |

**Tasks:**
- [ ] Add IPFS routes to `web/app.py`
- [ ] Implement endpoint handlers
- [ ] Add error responses for IPFS failures
- [ ] Update API documentation

### 2.5 Integration Tests

**Tasks:**
- [ ] Test capture → IPFS flow end-to-end
- [ ] Test session → directory DAG creation
- [ ] Test API endpoints with real IPFS daemon
- [ ] Test fallback behavior when IPFS offline

**Exit Criteria:**
- ✅ Captures are automatically published to IPFS
- ✅ Session directories are created as IPFS DAGs
- ✅ API endpoints return IPFS information
- ✅ System works without IPFS (graceful degradation)

---

## Phase 3: Frontend Integration

**Duration:** 1.5 weeks  
**Goal:** Display IPFS information in UI

### 3.1 Frontend Components

```mermaid
flowchart TB
    subgraph "New Frontend Components"
        A["IPFSStatus<br/>━━━━━━━━━━<br/>• Daemon status<br/>• Peer count<br/>• Storage used"]
        
        B["IPFSGallery<br/>━━━━━━━━━━<br/>• Local + remote<br/>• CID display<br/>• Pin controls"]
        
        C["CIDDisplay<br/>━━━━━━━━━━<br/>• Copy to clipboard<br/>• Gateway link<br/>• QR code"]
        
        D["SyncIndicator<br/>━━━━━━━━━━<br/>• Upload progress<br/>• Queue length<br/>• Error display"]
    end
    
    A --> E[status-bar.tsx]
    B --> F[capture-panel.tsx]
    C --> F
    D --> E
```

**Tasks:**
- [ ] Create `components/ipfs-status.tsx`
- [ ] Create `components/cid-display.tsx`
- [ ] Create `components/ipfs-gallery.tsx`
- [ ] Create `components/sync-indicator.tsx`
- [ ] Add TypeScript types for IPFS data

### 3.2 WebSocket Events

**New Events:**

| Event | Namespace | Payload |
|-------|-----------|---------|
| `ipfs_status` | `/ws/camera` | `{daemon: bool, peers: int}` |
| `ipfs_upload_start` | `/ws/camera` | `{file: string, size: int}` |
| `ipfs_upload_complete` | `/ws/camera` | `{file: string, cid: string}` |
| `ipfs_upload_error` | `/ws/camera` | `{file: string, error: string}` |
| `ipfs_peer_connected` | `/ws/session` | `{peer_id: string}` |

**Tasks:**
- [ ] Add IPFS events to Socket.IO namespaces
- [ ] Update `useWebSocket` hook for IPFS events
- [ ] Create `useIPFS` custom hook
- [ ] Test real-time updates

### 3.3 IPFS Gallery View

```mermaid
flowchart LR
    subgraph "Gallery View"
        A[Gallery Toggle] --> B{View Mode}
        B -->|"Local"| C[Local images<br/>from /captures]
        B -->|"IPFS"| D[Network images<br/>from IPFS]
        B -->|"All"| E[Combined view<br/>Local + Remote]
        
        C --> F[Image Grid]
        D --> F
        E --> F
        
        F --> G[Image Detail Modal]
        G --> H[CID Info]
        G --> I[Pin Status]
        G --> J[Download from IPFS]
    end
```

**Tasks:**
- [ ] Add view mode toggle to gallery
- [ ] Fetch and display remote IPFS images
- [ ] Show CID and pin status per image
- [ ] Add "Open in Gateway" button
- [ ] Implement lazy loading for IPFS images

**Exit Criteria:**
- ✅ IPFS status visible in UI
- ✅ CIDs displayed for uploaded images
- ✅ Real-time upload progress shown
- ✅ Users can browse network images

---

## Phase 4: Network Features

**Duration:** 1.5 weeks  
**Goal:** Enable WANDA node discovery and synchronization

### 4.1 Peer Discovery

```mermaid
flowchart TB
    subgraph "WANDA Peer Discovery"
        A[Node Startup] --> B[Initialize IPFS]
        B --> C[Subscribe to<br/>/wanda/discovery topic]
        C --> D[Announce presence]
        
        D --> E{Receive peer<br/>announcements}
        
        E --> F[Add to peer list]
        F --> G[Establish direct<br/>connection]
        G --> H[Exchange metadata]
        
        H --> I[Periodic<br/>heartbeat]
        I --> E
    end
```

**Tasks:**
- [ ] Implement PubSub topic for WANDA nodes
- [ ] Create peer announcement protocol
- [ ] Build peer management service
- [ ] Add peer list to API and UI
- [ ] Implement peer scoring/reputation

### 4.2 Network Synchronization

```mermaid
sequenceDiagram
    participant Local as Local Node
    participant Peer as Peer Node
    participant DHT as DHT
    
    Note over Local,DHT: Content Discovery
    Local->>Peer: Request recent CIDs
    Peer-->>Local: CID list with metadata
    
    Local->>Local: Compare with local
    
    alt Missing content found
        Local->>DHT: Resolve CID providers
        DHT-->>Local: Provider list
        Local->>Peer: ipfs get CID
        Peer-->>Local: Content
        Local->>Local: Pin locally
    end
    
    Note over Local,DHT: Content Announcement
    Local->>DHT: Provide new CIDs
    Local->>Peer: Push CID notification
```

**Tasks:**
- [ ] Create sync protocol specification
- [ ] Implement CID exchange between peers
- [ ] Add selective sync (by session, date, etc.)
- [ ] Implement bandwidth throttling
- [ ] Add sync status to UI

### 4.3 IPNS Publishing

**Tasks:**
- [ ] Generate IPNS key per WANDA node
- [ ] Publish node's capture directory to IPNS
- [ ] Update IPNS on new captures
- [ ] Document IPNS name format
- [ ] Add IPNS resolution to gallery

**Exit Criteria:**
- ✅ WANDA nodes discover each other automatically
- ✅ Images sync between connected nodes
- ✅ Each node has an IPNS address for its captures

---

## Phase 5: Optimization & Production

**Duration:** 1 week  
**Goal:** Production-ready IPFS integration

### 5.1 Performance Optimization

```mermaid
flowchart LR
    subgraph "Optimization Areas"
        A[Startup Time] --> A1["Lazy daemon<br/>initialization"]
        B[Upload Speed] --> B1["Parallel<br/>chunking"]
        C[Memory Usage] --> C1["Streaming<br/>uploads"]
        D[Storage] --> D1["Garbage<br/>collection"]
        E[Network] --> E1["Connection<br/>limiting"]
    end
```

**Tasks:**
- [ ] Profile IPFS operations on Raspberry Pi
- [ ] Optimize memory usage for large files
- [ ] Implement garbage collection policy
- [ ] Add connection limiting for low-bandwidth
- [ ] Create performance benchmarks

### 5.2 Documentation

**Tasks:**
- [ ] Update main README with IPFS features
- [ ] Create IPFS troubleshooting guide
- [ ] Document configuration options
- [ ] Write peer discovery protocol spec
- [ ] Update deployment guide

### 5.3 Production Testing

**Tasks:**
- [ ] Multi-node testing (3+ nodes)
- [ ] Long-running stability tests
- [ ] Network partition testing
- [ ] Storage stress testing
- [ ] Performance benchmarks on Pi 4/5

**Exit Criteria:**
- ✅ System stable over 72+ hour test
- ✅ Memory usage under control
- ✅ Documentation complete
- ✅ Performance meets targets

---

## Risk Mitigation

### Technical Risks

| Risk | Mitigation |
|------|------------|
| IPFS daemon instability on Pi | Use `lowpower` profile, connection limiting |
| Network bandwidth constraints | Background sync, bandwidth throttling |
| Storage space exhaustion | Garbage collection, pin policies |
| Long upload times | Async operations, queue management |

### Rollback Strategy

Each phase has a rollback point:

1. **Phase 1**: Remove IPFS service, no impact on existing functionality
2. **Phase 2**: Disable storage router, revert to local-only
3. **Phase 3**: Hide IPFS UI components
4. **Phase 4**: Disable peer discovery, local-only IPFS
5. **Phase 5**: Revert optimizations if issues arise

## Dependency Chart

```mermaid
flowchart TD
    subgraph "Phase Dependencies"
        P1A[IPFS Daemon] --> P1B[Python Client]
        P1B --> P1C[Basic Operations]
        P1C --> P2A[Storage Router]
        
        P2A --> P2B[Camera Integration]
        P2A --> P2C[Session Integration]
        P2B --> P2D[API Endpoints]
        P2C --> P2D
        
        P2D --> P3A[Frontend Components]
        P3A --> P3B[WebSocket Events]
        P3B --> P3C[IPFS Gallery]
        
        P2D --> P4A[Peer Discovery]
        P4A --> P4B[Network Sync]
        P4B --> P4C[IPNS Publishing]
        
        P3C --> P5A[Optimization]
        P4C --> P5A
        P5A --> P5B[Documentation]
        P5B --> P5C[Production Testing]
    end
```

---

**Next**: See [ipfs-concepts.md](./ipfs-concepts.md) for IPFS fundamentals.


# WANDA IPFS Storage Strategy

## Overview

This document defines the storage strategy for WANDA's IPFS integration, covering local caching, pinning policies, garbage collection, and data lifecycle management.

## Storage Architecture

```mermaid
flowchart TB
    subgraph "WANDA Storage Layers"
        subgraph "Layer 1: Hot Storage (Local FS)"
            Local["Local Filesystem<br/>/captures<br/>━━━━━━━━━━━━━<br/>• Immediate access<br/>• Full resolution<br/>• Session directories"]
        end
        
        subgraph "Layer 2: Warm Storage (IPFS Local)"
            IPFSLocal["IPFS Local Repo<br/>~/.ipfs<br/>━━━━━━━━━━━━━<br/>• Pinned content<br/>• Cached remote<br/>• Deduped blocks"]
        end
        
        subgraph "Layer 3: Cold Storage (IPFS Network)"
            IPFSNetwork["IPFS Network<br/>━━━━━━━━━━━━━<br/>• Remote peers<br/>• Public gateways<br/>• Distributed replicas"]
        end
    end
    
    Local -->|"Auto-sync"| IPFSLocal
    IPFSLocal <-->|"Peer exchange"| IPFSNetwork
```

## Data Flow

### Capture Flow

```mermaid
sequenceDiagram
    participant Camera
    participant Router as Storage Router
    participant FS as Local Filesystem
    participant Queue as Upload Queue
    participant IPFS as IPFS Service
    participant Kubo as Kubo Daemon
    participant Meta as Metadata DB
    
    Camera->>Router: capture_complete(image_data)
    
    rect rgb(200, 230, 200)
        Note over Router,FS: Step 1: Local Save (Sync, Blocking)
        Router->>FS: write_file()
        FS-->>Router: local_path
        Router->>FS: generate_thumbnail()
        FS-->>Router: thumb_path
    end
    
    Router-->>Camera: {path, thumbnail}
    
    rect rgb(200, 200, 230)
        Note over Router,Meta: Step 2: IPFS Queue (Async, Non-blocking)
        Router->>Queue: enqueue(local_path)
        Router->>Meta: create_record(path, status="queued")
    end
    
    rect rgb(230, 200, 200)
        Note over Queue,Meta: Step 3: Background Upload
        Queue->>IPFS: process_next()
        IPFS->>Kubo: ipfs add --pin
        Kubo-->>IPFS: CID
        IPFS->>Meta: update_record(cid, status="complete")
        IPFS->>Router: emit_event("ipfs_upload_complete")
    end
```

### Retrieval Flow

```mermaid
flowchart TD
    A[Request Image] --> B{Source?}
    
    B -->|"Local path"| C{Exists locally?}
    C -->|"Yes"| D[Serve from FS]
    C -->|"No"| E[Return 404]
    
    B -->|"CID"| F{In local IPFS?}
    F -->|"Yes"| G[Serve from repo]
    F -->|"No"| H{Fetch from network?}
    
    H -->|"Yes"| I[ipfs cat CID]
    I --> J{Success?}
    J -->|"Yes"| K[Cache locally]
    K --> L[Serve content]
    J -->|"No"| M[Return 404/timeout]
    
    H -->|"No (offline mode)"| M
    
    D --> N[Return to client]
    G --> N
    L --> N
```

## Directory Structure

### Local Filesystem

```
/captures/                          # Base capture directory
├── capture_0001.jpg               # Single captures
├── capture_0002.jpg
├── .thumbnails/                   # Thumbnail cache
│   ├── capture_0001_thumb.jpg
│   └── capture_0002_thumb.jpg
├── .ipfs_metadata.json            # IPFS mapping file
├── Session Name 1/                # Session directory
│   ├── image_0001.jpg
│   ├── image_0002.jpg
│   ├── session_metadata.json
│   └── .ipfs_session.json         # Session IPFS metadata
└── Session Name 2/
    └── ...
```

### IPFS Repository

```
~/.ipfs/                           # IPFS repository root
├── config                         # IPFS configuration
├── datastore/                     # Block storage
│   ├── 000001.log
│   └── MANIFEST-000002
├── keystore/                      # IPFS/IPNS keys
│   └── wanda-node                 # Node's IPNS key
└── version
```

## Metadata Schema

### Capture IPFS Metadata

```json
// /captures/.ipfs_metadata.json
{
  "version": "1.0",
  "node_id": "12D3KooW...",
  "ipns_name": "k51qzi5uqu...",
  "last_updated": "2025-01-15T10:30:00Z",
  "captures": {
    "capture_0001.jpg": {
      "cid": "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
      "size_bytes": 5242880,
      "added_at": "2025-01-15T09:00:00Z",
      "pinned": true,
      "replicas": 3
    },
    "capture_0002.jpg": {
      "cid": "QmXnnyufdzAWL5CqZ2RnSNgPbvCc1ALT73s6epPrRnZ1Xy",
      "size_bytes": 4718592,
      "added_at": "2025-01-15T09:15:00Z",
      "pinned": true,
      "replicas": 1
    }
  }
}
```

### Session IPFS Metadata

```json
// /captures/Moon Session/.ipfs_session.json
{
  "version": "1.0",
  "session_name": "Moon Session",
  "session_cid": "bafybeihdwdcefgh4dqkjv67uzcmw7ojee6xedzdetojuzjevtenxquvyku",
  "created_at": "2025-01-15T08:00:00Z",
  "completed_at": "2025-01-15T10:30:00Z",
  "ipns_name": "k51qzi5uqu...",
  "total_images": 50,
  "total_size_bytes": 262144000,
  "images": {
    "image_0001.jpg": {
      "cid": "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
      "size_bytes": 5242880
    }
  }
}
```

## Pinning Policies

```mermaid
flowchart TB
    subgraph "Pinning Decision Tree"
        A[New Content] --> B{Content Type?}
        
        B -->|"Single Capture"| C[Pin Directly]
        B -->|"Session Directory"| D[Pin Recursively]
        B -->|"Remote Content"| E{Auto-pin enabled?}
        
        E -->|"Yes"| F{From WANDA peer?}
        F -->|"Yes"| G[Pin with TTL]
        F -->|"No"| H[Cache only]
        
        E -->|"No"| H
        
        C --> I[Update metadata]
        D --> I
        G --> I
    end
```

### Policy Configuration

```python
# ipfs/config.py

PINNING_POLICIES = {
    # Local captures: always pin
    "local_captures": {
        "auto_pin": True,
        "pin_type": "direct",
        "priority": "high"
    },
    
    # Session directories: recursive pin
    "sessions": {
        "auto_pin": True,
        "pin_type": "recursive",
        "priority": "high"
    },
    
    # Content from WANDA peers: pin with TTL
    "wanda_peers": {
        "auto_pin": True,
        "pin_type": "direct",
        "ttl_days": 30,  # Auto-unpin after 30 days
        "priority": "medium"
    },
    
    # Content from unknown sources: cache only
    "unknown": {
        "auto_pin": False,
        "cache_only": True,
        "priority": "low"
    }
}
```

## Garbage Collection

### Storage Limits

```mermaid
flowchart LR
    subgraph "Storage Thresholds"
        A["Low Watermark<br/>70%"] -->|"Normal operation"| B["High Watermark<br/>85%"]
        B -->|"Trigger GC"| C["Critical<br/>95%"]
        C -->|"Emergency GC"| D["Max Storage<br/>100%"]
    end
```

### GC Strategy

```mermaid
flowchart TD
    subgraph "Garbage Collection Strategy"
        A[Storage Check] --> B{Usage > 85%?}
        
        B -->|"No"| C[No action]
        B -->|"Yes"| D[Start GC]
        
        D --> E[Build unpin candidates]
        
        E --> F["Priority 1:<br/>Cached remote (non-WANDA)"]
        F --> G["Priority 2:<br/>Expired TTL pins"]
        G --> H["Priority 3:<br/>Oldest WANDA peer content"]
        H --> I["Priority 4:<br/>Oldest local captures"]
        
        I --> J{Usage < 70%?}
        J -->|"No"| F
        J -->|"Yes"| K[GC complete]
        
        subgraph "Never Delete"
            L["Current session"]
            M["Last 100 local captures"]
            N["Starred/favorited"]
        end
    end
```

### GC Configuration

```python
# ipfs/config.py

GARBAGE_COLLECTION = {
    # Storage thresholds (percentage of max storage)
    "low_watermark": 0.70,      # Target after GC
    "high_watermark": 0.85,     # Trigger GC
    "critical_threshold": 0.95, # Emergency GC
    
    # Maximum storage (bytes)
    "max_storage": 10 * 1024**3,  # 10 GB
    
    # Protection rules
    "protect_recent_days": 7,     # Don't GC content newer than 7 days
    "protect_local_count": 100,   # Keep at least 100 local captures
    "protect_starred": True,      # Never GC starred content
    
    # Schedule
    "auto_gc_enabled": True,
    "gc_schedule": "0 3 * * *",   # 3 AM daily
    "gc_on_storage_full": True
}
```

## Sync Strategies

### Full Sync vs. Selective Sync

```mermaid
flowchart TB
    subgraph "Sync Options"
        A[Sync Mode Selection]
        
        A --> B["Full Sync<br/>━━━━━━━━━━━━━<br/>• All content from all peers<br/>• High bandwidth/storage<br/>• Complete network mirror"]
        
        A --> C["Selective Sync<br/>━━━━━━━━━━━━━<br/>• Filter by date range<br/>• Filter by peer<br/>• Filter by session<br/>• Low bandwidth"]
        
        A --> D["On-Demand<br/>━━━━━━━━━━━━━<br/>• Fetch when viewed<br/>• Minimal bandwidth<br/>• Lazy loading"]
    end
```

### Sync Configuration

```python
# ipfs/config.py

SYNC_STRATEGIES = {
    "mode": "selective",  # "full", "selective", "on_demand"
    
    "selective": {
        # Time-based filters
        "sync_recent_days": 30,
        
        # Source filters
        "sync_from_nodes": ["all"],  # or specific node IDs
        
        # Content filters
        "sync_sessions": True,
        "sync_singles": True,
        
        # Bandwidth limits
        "max_bandwidth_mbps": 10,
        "sync_schedule": "*/15 * * * *",  # Every 15 minutes
    },
    
    "on_demand": {
        "cache_fetched": True,
        "cache_ttl_hours": 24,
        "prefetch_thumbnails": True
    }
}
```

## Storage Optimization

### Deduplication

IPFS automatically deduplicates content at the block level:

```mermaid
flowchart LR
    subgraph "Deduplication Example"
        A["Image A<br/>5 MB"] --> B["Chunk 1"]
        A --> C["Chunk 2"]
        A --> D["Chunk 3"]
        
        E["Image B<br/>(same as A)"] --> B
        E --> C
        E --> D
        
        F["Image C<br/>(similar)"] --> B
        F --> C
        F --> G["Chunk 4"]
    end
    
    subgraph "Storage Used"
        H["Without IPFS: 15 MB"]
        I["With IPFS: 6.7 MB"]
    end
```

### Compression

| Content Type | Compression | Reason |
|--------------|-------------|--------|
| JPEG images | None | Already compressed |
| RAW images | Optional zstd | Large files benefit |
| JSON metadata | gzip | Small, highly compressible |
| Session directories | None | Mixed content |

## Backup and Recovery

### Backup Strategy

```mermaid
flowchart TB
    subgraph "Backup Layers"
        A["Layer 1: Local FS<br/>Primary storage"]
        B["Layer 2: IPFS Local<br/>Content-addressed copy"]
        C["Layer 3: IPFS Network<br/>Distributed replicas"]
        D["Layer 4: USB Export<br/>Offline backup"]
    end
    
    A <-->|"sync"| B
    B <-->|"replicate"| C
    A -->|"manual"| D
```

### Recovery Scenarios

| Scenario | Recovery Method |
|----------|-----------------|
| SD card corruption | Restore from IPFS (if CIDs known) |
| Accidental deletion | Unpin → Re-add from backup |
| Node failure | Sync from network peers |
| Network isolation | Continue with local storage |

### Export Command

```bash
# Export session to USB for offline backup
wanda-export --session "Moon Session" --destination /media/usb/backup/

# This creates:
# /media/usb/backup/Moon Session/
# ├── images/
# ├── metadata.json
# └── ipfs_manifest.json  # Contains all CIDs for re-import
```

## Monitoring and Alerts

### Storage Metrics

```mermaid
flowchart LR
    subgraph "Monitored Metrics"
        A["Local FS Usage"]
        B["IPFS Repo Size"]
        C["Pin Count"]
        D["Network Bandwidth"]
        E["Sync Queue Length"]
    end
    
    subgraph "Alert Thresholds"
        F["FS > 90%"]
        G["IPFS > 85%"]
        H["Pins > 10,000"]
        I["BW > 50 Mbps"]
        J["Queue > 100"]
    end
    
    A --> F
    B --> G
    C --> H
    D --> I
    E --> J
```

### Alert Configuration

```python
# ipfs/config.py

STORAGE_ALERTS = {
    "local_fs_warning": 0.80,
    "local_fs_critical": 0.90,
    
    "ipfs_repo_warning": 0.75,
    "ipfs_repo_critical": 0.85,
    
    "upload_queue_warning": 50,
    "upload_queue_critical": 100,
    
    "alert_methods": ["websocket", "log"],
    "alert_cooldown_minutes": 30
}
```

## Performance Considerations

### Raspberry Pi Optimizations

| Optimization | Setting | Reason |
|--------------|---------|--------|
| Reduce connections | LowWater: 50, HighWater: 100 | Memory constraints |
| Limit DHT | dhtclient mode | CPU usage |
| Async uploads | Background queue | Non-blocking captures |
| Lazy loading | On-demand fetch | Bandwidth conservation |
| Streaming | Chunk-based read/write | Memory efficiency |

### I/O Recommendations

```python
# Best practices for Raspberry Pi

# Use async I/O for IPFS operations
async def add_to_ipfs(file_path: str) -> str:
    """Non-blocking IPFS add."""
    async with aioipfs.AsyncIPFS() as client:
        result = await client.add(file_path)
        return result['Hash']

# Limit concurrent operations
IPFS_CONCURRENT_OPS = 2  # Max 2 simultaneous adds/gets

# Use memory-mapped files for large images
def read_large_file(path: str):
    with open(path, 'rb') as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            return mm.read()
```

---

**Next**: See [network-topology.md](./network-topology.md) for distributed network design.


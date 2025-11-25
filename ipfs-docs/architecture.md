# WANDA IPFS Architecture

## Overview

This document describes the technical architecture for integrating IPFS into the WANDA telescope system. The design prioritizes backward compatibility, graceful degradation, and seamless user experience.

## Current Architecture

```mermaid
flowchart TB
    subgraph "Current WANDA Architecture"
        subgraph "Raspberry Pi"
            subgraph "Frontend"
                NextJS["Next.js 14<br/>React 19"]
            end
            
            subgraph "Backend"
                Flask["Flask + Socket.IO"]
                Camera["Camera Module"]
                Mount["Mount Module"]
                Session["Session Controller"]
            end
            
            subgraph "Storage"
                Local["Local Filesystem<br/>/captures"]
                USB["USB Storage<br/>/media/astro1"]
            end
        end
        
        NextJS <-->|"REST + WebSocket"| Flask
        Session --> Camera
        Session --> Mount
        Camera -->|"save"| Local
        Camera -->|"save"| USB
    end
```

## Target Architecture with IPFS

```mermaid
flowchart TB
    subgraph "WANDA + IPFS Architecture"
        subgraph "Raspberry Pi Node"
            subgraph "Frontend Layer"
                NextJS["Next.js 14<br/>React 19"]
                IPFSViewer["IPFS Image Viewer<br/>Component"]
            end
            
            subgraph "Backend Layer"
                Flask["Flask + Socket.IO"]
                Camera["Camera Module"]
                Mount["Mount Module"]
                Session["Session Controller"]
                IPFSService["IPFS Service<br/>(New)"]
                StorageRouter["Storage Router<br/>(New)"]
            end
            
            subgraph "IPFS Layer"
                KuboDaemon["Kubo Daemon<br/>(IPFS Node)"]
                LocalRepo["IPFS Local Repo<br/>~/.ipfs"]
            end
            
            subgraph "Storage Layer"
                Local["Local Cache<br/>/captures"]
                USB["USB Storage<br/>/media/astro1"]
            end
        end
        
        subgraph "IPFS Network"
            DHT["Distributed Hash Table"]
            Peers["Other WANDA Nodes"]
            Gateways["Public IPFS Gateways"]
        end
        
        NextJS <-->|"REST + WS"| Flask
        IPFSViewer --> NextJS
        Session --> Camera
        Camera --> StorageRouter
        StorageRouter -->|"1. Save local"| Local
        StorageRouter -->|"2. Pin to IPFS"| IPFSService
        IPFSService <-->|"HTTP API"| KuboDaemon
        KuboDaemon --> LocalRepo
        KuboDaemon <-->|"libp2p"| DHT
        KuboDaemon <-->|"libp2p"| Peers
    end
```

## Component Architecture

### New Components

```mermaid
flowchart LR
    subgraph "New IPFS Components"
        subgraph "Python Backend"
            IPFSService["ipfs/service.py<br/>━━━━━━━━━━━━━━<br/>• add_file()<br/>• get_file()<br/>• pin_file()<br/>• unpin_file()<br/>• get_stats()"]
            
            IPFSClient["ipfs/client.py<br/>━━━━━━━━━━━━━━<br/>• HTTP API wrapper<br/>• Connection pooling<br/>• Retry logic"]
            
            IPFSConfig["ipfs/config.py<br/>━━━━━━━━━━━━━━<br/>• IPFS settings<br/>• Gateway URLs<br/>• Pin policies"]
            
            IPFSModels["ipfs/models.py<br/>━━━━━━━━━━━━━━<br/>• CID model<br/>• Pin status<br/>• Peer info"]
        end
        
        subgraph "Frontend"
            IPFSHook["hooks/useIPFS.ts<br/>━━━━━━━━━━━━━━<br/>• Upload status<br/>• Pin management<br/>• Network stats"]
            
            IPFSGallery["components/<br/>ipfs-gallery.tsx<br/>━━━━━━━━━━━━━━<br/>• Network images<br/>• Local + remote<br/>• CID display"]
        end
        
        IPFSService --> IPFSClient
        IPFSClient --> IPFSConfig
        IPFSService --> IPFSModels
    end
```

### Storage Router Flow

```mermaid
sequenceDiagram
    participant Camera
    participant StorageRouter
    participant LocalFS as Local Filesystem
    participant IPFSService
    participant Kubo as Kubo Daemon
    participant Network as IPFS Network
    
    Camera->>StorageRouter: capture_file(image_data)
    
    rect rgb(200, 230, 200)
        Note over StorageRouter,LocalFS: Phase 1: Local Storage (Priority)
        StorageRouter->>LocalFS: save_local(image_data)
        LocalFS-->>StorageRouter: local_path
    end
    
    rect rgb(200, 200, 230)
        Note over StorageRouter,Network: Phase 2: IPFS Publication (Async)
        StorageRouter->>IPFSService: publish_async(local_path)
        IPFSService->>Kubo: ipfs add --pin
        Kubo-->>IPFSService: CID
        IPFSService->>Kubo: ipfs name publish (IPNS)
        Kubo->>Network: Announce to DHT
        IPFSService-->>StorageRouter: CID + IPNS
    end
    
    StorageRouter-->>Camera: {local_path, cid, ipns}
```

## Data Flow Architecture

### Image Capture Flow

```mermaid
flowchart TD
    subgraph "Image Capture with IPFS"
        A[User triggers capture] --> B[Camera captures image]
        B --> C{Storage Router}
        
        C -->|"Step 1"| D[Save to Local FS]
        D --> E[Generate thumbnail]
        
        C -->|"Step 2 (async)"| F[IPFS Service]
        F --> G[Add to IPFS]
        G --> H[Pin locally]
        H --> I[Update IPNS record]
        
        D --> J[Store metadata]
        I --> J
        
        J --> K[Emit WebSocket event]
        K --> L[Update UI with CID]
    end
```

### Image Retrieval Flow

```mermaid
flowchart TD
    subgraph "Image Retrieval"
        A[Request image] --> B{Check source}
        
        B -->|"Local CID"| C[Check local cache]
        C -->|"Hit"| D[Serve from local FS]
        C -->|"Miss"| E[Fetch from IPFS]
        
        B -->|"Remote CID"| F[Check if pinned locally]
        F -->|"Yes"| D
        F -->|"No"| E
        
        E --> G[ipfs cat CID]
        G --> H[Cache locally]
        H --> I[Serve to client]
        
        D --> J[Return image]
        I --> J
    end
```

## Network Architecture

### Multi-Node Topology

```mermaid
flowchart TB
    subgraph "WANDA Global Network"
        subgraph "Region: Americas"
            Chile["🔭 WANDA Chile<br/>Node ID: Qm...ABC"]
            Brazil["🔭 WANDA Brazil<br/>Node ID: Qm...DEF"]
        end
        
        subgraph "Region: Europe"
            Spain["🔭 WANDA Spain<br/>Node ID: Qm...GHI"]
            Germany["🔭 WANDA Germany<br/>Node ID: Qm...JKL"]
        end
        
        subgraph "Region: Asia-Pacific"
            Japan["🔭 WANDA Japan<br/>Node ID: Qm...MNO"]
            Australia["🔭 WANDA Australia<br/>Node ID: Qm...PQR"]
        end
        
        subgraph "IPFS Infrastructure"
            Bootstrap["Bootstrap Nodes"]
            PublicGW["Public Gateways<br/>ipfs.io, dweb.link"]
        end
        
        Chile <--> Bootstrap
        Brazil <--> Bootstrap
        Spain <--> Bootstrap
        Germany <--> Bootstrap
        Japan <--> Bootstrap
        Australia <--> Bootstrap
        
        Chile <-.->|"Direct peer"| Brazil
        Spain <-.->|"Direct peer"| Germany
        Japan <-.->|"Direct peer"| Australia
        
        Chile <-.->|"Cross-region"| Spain
        Spain <-.->|"Cross-region"| Japan
        
        PublicGW <--> Bootstrap
    end
```

### Peer Discovery Flow

```mermaid
sequenceDiagram
    participant NewNode as New WANDA Node
    participant Bootstrap as Bootstrap Node
    participant DHT as DHT Network
    participant ExistingNode as Existing WANDA Node
    
    Note over NewNode: Starting up...
    
    NewNode->>Bootstrap: Connect to bootstrap
    Bootstrap-->>NewNode: Peer list
    
    NewNode->>DHT: Announce presence
    NewNode->>DHT: Query /wanda-telescope topic
    
    DHT-->>NewNode: Known WANDA peers
    
    NewNode->>ExistingNode: Establish direct connection
    ExistingNode-->>NewNode: Exchange peer info
    
    Note over NewNode,ExistingNode: Now synced!
    
    ExistingNode->>NewNode: Push recent CIDs
    NewNode->>ExistingNode: Request pinned content
```

## Database Schema (Metadata)

```mermaid
erDiagram
    CAPTURE {
        string id PK
        string local_path
        string cid "IPFS Content ID"
        string ipns_key "Optional IPNS name"
        datetime captured_at
        string session_id FK
        boolean is_pinned
        boolean is_synced
        json metadata
    }
    
    SESSION {
        string id PK
        string name
        string directory_cid
        datetime start_time
        datetime end_time
        int total_images
        string status
    }
    
    PEER {
        string peer_id PK
        string multiaddr
        datetime last_seen
        string location
        boolean is_wanda_node
        int images_shared
    }
    
    PIN_STATUS {
        string cid PK
        string peer_id FK
        boolean is_pinned
        datetime pinned_at
        int replicas
    }
    
    SESSION ||--o{ CAPTURE : contains
    CAPTURE ||--o{ PIN_STATUS : "replicated on"
    PEER ||--o{ PIN_STATUS : pins
```

## Configuration Architecture

```mermaid
flowchart LR
    subgraph "Configuration Hierarchy"
        subgraph "config.py (existing)"
            CameraConfig["Camera Settings"]
            MountConfig["Mount Settings"]
            StorageConfig["Storage Settings"]
        end
        
        subgraph "ipfs/config.py (new)"
            IPFSBasic["Basic Settings<br/>━━━━━━━━━━━━<br/>• daemon_addr<br/>• api_port<br/>• gateway_port"]
            
            IPFSAdvanced["Advanced Settings<br/>━━━━━━━━━━━━<br/>• swarm_addresses<br/>• bootstrap_nodes<br/>• announce_addresses"]
            
            IPFSPolicies["Storage Policies<br/>━━━━━━━━━━━━<br/>• auto_pin<br/>• pin_remote<br/>• gc_watermark<br/>• max_storage"]
            
            IPFSNetwork["Network Settings<br/>━━━━━━━━━━━━<br/>• pubsub_topic<br/>• dht_mode<br/>• relay_enabled"]
        end
        
        StorageConfig --> IPFSBasic
    end
```

## Error Handling Architecture

```mermaid
flowchart TD
    subgraph "IPFS Error Handling"
        A[IPFS Operation] --> B{Success?}
        
        B -->|"Yes"| C[Return result]
        
        B -->|"No"| D{Error type?}
        
        D -->|"Connection Error"| E[Retry with backoff]
        E --> F{Max retries?}
        F -->|"No"| A
        F -->|"Yes"| G[Queue for later]
        
        D -->|"Daemon not running"| H[Start daemon]
        H --> A
        
        D -->|"Storage full"| I[Trigger GC]
        I --> J{Space freed?}
        J -->|"Yes"| A
        J -->|"No"| K[Alert user]
        
        D -->|"Network timeout"| L[Use local cache]
        L --> C
        
        G --> M[Background sync queue]
        M --> N[Retry on network restore]
    end
```

## Service Integration Points

```mermaid
flowchart TB
    subgraph "System Services"
        subgraph "Existing Services"
            Backend["wanda-backend.service<br/>(Flask + Socket.IO)"]
            Frontend["wanda-frontend.service<br/>(Next.js)"]
            Nginx["nginx.service<br/>(Reverse Proxy)"]
        end
        
        subgraph "New Services"
            IPFS["wanda-ipfs.service<br/>(Kubo Daemon)"]
            IPFSSync["wanda-ipfs-sync.service<br/>(Background Sync)"]
        end
        
        Backend -->|"depends on"| IPFS
        IPFSSync -->|"depends on"| IPFS
        IPFSSync -->|"depends on"| Backend
        
        Nginx -->|"proxies"| Frontend
        Nginx -->|"proxies"| Backend
        Nginx -->|"proxies /ipfs"| IPFS
    end
```

## Deployment Architecture

```mermaid
flowchart TB
    subgraph "Production Deployment"
        subgraph "Nginx (Port 80)"
            Route1["/"] --> Frontend
            Route2["/api/*"] --> Backend
            Route3["/socket.io"] --> Backend
            Route4["/video_feed"] --> Backend
            Route5["/captures"] --> StaticFiles["Static Files"]
            Route6["/ipfs/*"] --> Gateway["IPFS Gateway"]
            Route7["/ipns/*"] --> Gateway
        end
        
        subgraph "Services"
            Frontend["Next.js<br/>:3000"]
            Backend["Flask<br/>:5000"]
            Gateway["Kubo Gateway<br/>:8080"]
            API["Kubo API<br/>:5001"]
        end
        
        Backend <-->|"HTTP"| API
    end
```

## Summary

The IPFS integration adds three main architectural components:

1. **IPFS Service Layer** (`ipfs/`) - Python module handling all IPFS operations
2. **Storage Router** - Coordinates local and IPFS storage
3. **Kubo Daemon** - Local IPFS node (systemd service)

The design ensures:
- ✅ Local-first operation (works offline)
- ✅ Async IPFS publishing (no capture delays)
- ✅ Backward compatibility (existing code unchanged)
- ✅ Graceful degradation (falls back if IPFS unavailable)

---

**Next**: See [implementation-phases.md](./implementation-phases.md) for the phased rollout plan.


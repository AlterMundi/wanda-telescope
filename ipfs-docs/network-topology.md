# WANDA Network Topology

## Overview

This document describes the network architecture for the distributed WANDA telescope network, including peer discovery, communication protocols, and network resilience strategies.

## Network Vision

```mermaid
flowchart TB
    subgraph "Global WANDA Network"
        subgraph "South America"
            Chile["🔭 WANDA Chile<br/>Atacama Desert<br/>━━━━━━━━━━━━━<br/>Dark sky site<br/>Primary node"]
            Argentina["🔭 WANDA Argentina<br/>Patagonia"]
        end
        
        subgraph "Europe"
            Spain["🔭 WANDA Spain<br/>Canary Islands<br/>━━━━━━━━━━━━━<br/>Observatory partner"]
            Germany["🔭 WANDA Germany<br/>Black Forest"]
            UK["🔭 WANDA UK<br/>Wales"]
        end
        
        subgraph "Asia Pacific"
            Japan["🔭 WANDA Japan<br/>Hokkaido"]
            Australia["🔭 WANDA Australia<br/>Outback<br/>━━━━━━━━━━━━━<br/>Southern sky"]
            NZ["🔭 WANDA New Zealand<br/>South Island"]
        end
        
        subgraph "North America"
            USA["🔭 WANDA USA<br/>Arizona"]
            Canada["🔭 WANDA Canada<br/>Alberta"]
        end
        
        Chile <--> Argentina
        Chile <-.-> Spain
        Spain <--> Germany
        Germany <--> UK
        Japan <--> Australia
        Australia <--> NZ
        USA <--> Canada
        Spain <-.-> USA
        Australia <-.-> Chile
    end
```

## Network Layers

```mermaid
flowchart TB
    subgraph "WANDA Network Stack"
        L4["Layer 4: Application<br/>━━━━━━━━━━━━━<br/>WANDA Protocol<br/>Image sharing, Session sync"]
        
        L3["Layer 3: Content<br/>━━━━━━━━━━━━━<br/>IPFS/IPNS<br/>Content addressing, DHT"]
        
        L2["Layer 2: Transport<br/>━━━━━━━━━━━━━<br/>libp2p<br/>Peer connections, Multiplexing"]
        
        L1["Layer 1: Network<br/>━━━━━━━━━━━━━<br/>TCP/UDP/QUIC<br/>Internet connectivity"]
    end
    
    L4 --> L3
    L3 --> L2
    L2 --> L1
```

## Peer Discovery

### Discovery Mechanisms

```mermaid
flowchart LR
    subgraph "Discovery Methods"
        A["Bootstrap Nodes<br/>━━━━━━━━━━━━━<br/>Initial connection<br/>Known IPFS nodes"]
        
        B["DHT Discovery<br/>━━━━━━━━━━━━━<br/>Find peers by topic<br/>Decentralized"]
        
        C["mDNS (Local)<br/>━━━━━━━━━━━━━<br/>Same LAN discovery<br/>Zero config"]
        
        D["PubSub Rendezvous<br/>━━━━━━━━━━━━━<br/>WANDA topic<br/>Real-time updates"]
        
        E["Manual Peering<br/>━━━━━━━━━━━━━<br/>Configured peers<br/>Trusted connections"]
    end
```

### Discovery Flow

```mermaid
sequenceDiagram
    participant New as New WANDA Node
    participant Boot as Bootstrap Node
    participant DHT as DHT Network
    participant Topic as /wanda/discovery
    participant Peers as Existing WANDA Peers
    
    Note over New: Node starting up...
    
    rect rgb(200, 230, 200)
        Note over New,Boot: Phase 1: Bootstrap
        New->>Boot: Connect to bootstrap
        Boot-->>New: Initial peer list
        New->>DHT: Join DHT network
    end
    
    rect rgb(200, 200, 230)
        Note over New,Topic: Phase 2: Topic Discovery
        New->>Topic: Subscribe to /wanda/discovery
        New->>Topic: Publish announcement
        Topic-->>Peers: Broadcast new node
    end
    
    rect rgb(230, 200, 200)
        Note over New,Peers: Phase 3: Peer Exchange
        Peers-->>New: Welcome + peer list
        New->>Peers: Request peer info
        Peers-->>New: Extended peer data
    end
    
    rect rgb(230, 230, 200)
        Note over New,Peers: Phase 4: Establish Connections
        New->>Peers: Direct connect (libp2p)
        Peers-->>New: Connection established
        New->>Peers: Exchange capabilities
    end
```

### Announcement Protocol

```json
// WANDA Discovery Announcement Message
{
  "protocol": "wanda/discovery/1.0",
  "type": "announce",
  "node": {
    "id": "12D3KooWSpain...",
    "name": "WANDA Spain",
    "version": "1.5.0",
    "location": {
      "name": "Canary Islands, Spain",
      "latitude": 28.2916,
      "longitude": -16.6291,
      "timezone": "Atlantic/Canary"
    },
    "capabilities": [
      "imaging",
      "tracking",
      "sessions"
    ],
    "camera": {
      "model": "IMX477",
      "resolution": "4056x3040"
    },
    "ipns_name": "k51qzi5uqu...",
    "captures_count": 1542,
    "uptime_hours": 720
  },
  "addresses": [
    "/ip4/1.2.3.4/tcp/4001/p2p/12D3KooWSpain...",
    "/ip4/1.2.3.4/udp/4001/quic-v1/p2p/12D3KooWSpain..."
  ],
  "timestamp": "2025-01-15T10:30:00Z",
  "signature": "..."
}
```

## Communication Protocols

### PubSub Topics

```mermaid
flowchart TB
    subgraph "WANDA PubSub Topics"
        T1["/wanda/discovery<br/>━━━━━━━━━━━━━<br/>Node announcements<br/>Heartbeats"]
        
        T2["/wanda/captures<br/>━━━━━━━━━━━━━<br/>New capture announcements<br/>CID broadcasts"]
        
        T3["/wanda/sessions<br/>━━━━━━━━━━━━━<br/>Session start/complete<br/>Collaboration requests"]
        
        T4["/wanda/events<br/>━━━━━━━━━━━━━<br/>Celestial events<br/>Coordinated observations"]
        
        T5["/wanda/chat<br/>━━━━━━━━━━━━━<br/>Operator messages<br/>Coordination"]
    end
```

### Message Types

| Topic | Message Type | Purpose |
|-------|--------------|---------|
| `/wanda/discovery` | `announce` | New node online |
| `/wanda/discovery` | `heartbeat` | Periodic presence |
| `/wanda/discovery` | `goodbye` | Graceful disconnect |
| `/wanda/captures` | `new_capture` | Single image available |
| `/wanda/captures` | `session_complete` | Full session ready |
| `/wanda/sessions` | `session_start` | Beginning observation |
| `/wanda/sessions` | `collab_request` | Request synchronized capture |
| `/wanda/events` | `event_alert` | Celestial event notification |
| `/wanda/events` | `join_observation` | Join coordinated session |

### Protocol Messages

```mermaid
sequenceDiagram
    participant NodeA as WANDA Chile
    participant Topic as /wanda/captures
    participant NodeB as WANDA Spain
    participant NodeC as WANDA Japan
    
    Note over NodeA: New capture completed
    
    NodeA->>Topic: new_capture message
    
    par Broadcast to all subscribers
        Topic->>NodeB: new_capture
        Topic->>NodeC: new_capture
    end
    
    Note over NodeB: Interested in this capture
    NodeB->>NodeA: Request CID content
    NodeA-->>NodeB: Provide blocks
    
    Note over NodeC: Not interested (different target)
    NodeC->>NodeC: Ignore message
```

## Topology Patterns

### Mesh Network

```mermaid
flowchart TB
    subgraph "Mesh Topology (Default)"
        A["Node A"] <--> B["Node B"]
        A <--> C["Node C"]
        A <--> D["Node D"]
        B <--> C
        B <--> D
        C <--> D
        
        Note1["Every node connects<br/>to multiple peers"]
    end
```

### Regional Clusters

```mermaid
flowchart TB
    subgraph "Clustered Topology"
        subgraph "Cluster: Europe"
            E1["Spain"] <--> E2["Germany"]
            E2 <--> E3["UK"]
            E1 <--> E3
            EG["Gateway: Spain"]
        end
        
        subgraph "Cluster: Americas"
            A1["Chile"] <--> A2["Argentina"]
            A2 <--> A3["USA"]
            A1 <--> A3
            AG["Gateway: Chile"]
        end
        
        EG <-.->|"Cross-cluster"| AG
    end
```

### Hub and Spoke (Optional)

```mermaid
flowchart TB
    subgraph "Hub-Spoke for Coordination"
        Hub["Coordination Hub<br/>(Optional central node)"]
        
        Hub <--> S1["WANDA Node 1"]
        Hub <--> S2["WANDA Node 2"]
        Hub <--> S3["WANDA Node 3"]
        Hub <--> S4["WANDA Node 4"]
        
        S1 <-.->|"Direct P2P"| S2
        S3 <-.->|"Direct P2P"| S4
    end
```

## Network Resilience

### Failure Handling

```mermaid
flowchart TD
    subgraph "Resilience Strategies"
        A[Node Failure Detected] --> B{Failure Type?}
        
        B -->|"Network partition"| C[Continue locally]
        C --> D[Queue sync operations]
        D --> E[Retry when available]
        
        B -->|"Peer offline"| F[Remove from active peers]
        F --> G[Try alternative peers]
        G --> H[DHT fallback]
        
        B -->|"Bootstrap unreachable"| I[Use cached peers]
        I --> J[Try alternative bootstraps]
        
        B -->|"Complete isolation"| K[Offline mode]
        K --> L[Local storage only]
        L --> M[Sync on reconnection]
    end
```

### Connection Management

```mermaid
stateDiagram-v2
    [*] --> Disconnected
    
    Disconnected --> Connecting: Start connection
    Connecting --> Connected: Handshake complete
    Connecting --> Failed: Timeout/Error
    
    Failed --> Connecting: Retry (backoff)
    Failed --> Disconnected: Max retries
    
    Connected --> Healthy: Heartbeat OK
    Healthy --> Connected: Heartbeat received
    Healthy --> Degraded: Missed heartbeat
    
    Degraded --> Healthy: Heartbeat OK
    Degraded --> Disconnected: 3 missed heartbeats
    
    Connected --> Disconnected: Connection lost
```

### Retry Configuration

```python
# ipfs/config.py

CONNECTION_CONFIG = {
    "initial_backoff_ms": 1000,
    "max_backoff_ms": 60000,
    "backoff_multiplier": 2,
    "max_retries": 10,
    "heartbeat_interval_s": 30,
    "heartbeat_timeout_s": 90,
    "connection_timeout_s": 30
}

RESILIENCE_CONFIG = {
    "min_peers": 3,
    "target_peers": 10,
    "max_peers": 50,
    "peer_exchange_interval_s": 300,
    "bootstrap_retry_interval_s": 600
}
```

## NAT Traversal

### Strategies

```mermaid
flowchart TB
    subgraph "NAT Traversal"
        A[Connection Request] --> B{Behind NAT?}
        
        B -->|"No (Public IP)"| C[Direct connection]
        
        B -->|"Yes"| D{NAT Type?}
        
        D -->|"Full Cone"| E[UPnP/NAT-PMP]
        D -->|"Restricted"| F[Hole punching]
        D -->|"Symmetric"| G[Circuit relay]
        
        E --> H[Direct connection via mapped port]
        F --> I[Direct connection after punch]
        G --> J[Relayed connection]
        
        C --> K[Connected]
        H --> K
        I --> K
        J --> K
    end
```

### libp2p Configuration

```json
{
  "Swarm": {
    "Transports": {
      "Network": {
        "QUIC": true,
        "TCP": true,
        "Websocket": true
      }
    },
    "RelayClient": {
      "Enabled": true
    },
    "RelayService": {
      "Enabled": true
    },
    "EnableHolePunching": true
  },
  "AutoNAT": {
    "ServiceMode": "enabled"
  }
}
```

## Bandwidth Management

### Traffic Shaping

```mermaid
flowchart LR
    subgraph "Bandwidth Allocation"
        Total["Total: 50 Mbps"]
        
        Total --> Upload["Upload: 20 Mbps"]
        Total --> Download["Download: 30 Mbps"]
        
        Upload --> U1["High Priority: 10 Mbps<br/>(Local captures)"]
        Upload --> U2["Normal: 8 Mbps<br/>(Sync)"]
        Upload --> U3["Low: 2 Mbps<br/>(Discovery)"]
        
        Download --> D1["High: 15 Mbps<br/>(On-demand fetch)"]
        Download --> D2["Normal: 12 Mbps<br/>(Background sync)"]
        Download --> D3["Low: 3 Mbps<br/>(Prefetch)"]
    end
```

### Quality of Service

```python
# ipfs/config.py

BANDWIDTH_CONFIG = {
    "total_limit_mbps": 50,
    
    "upload": {
        "limit_mbps": 20,
        "priorities": {
            "local_captures": 0.50,  # 10 Mbps
            "sync": 0.40,            # 8 Mbps
            "discovery": 0.10        # 2 Mbps
        }
    },
    
    "download": {
        "limit_mbps": 30,
        "priorities": {
            "on_demand": 0.50,       # 15 Mbps
            "background_sync": 0.40, # 12 Mbps
            "prefetch": 0.10         # 3 Mbps
        }
    },
    
    "schedule": {
        "peak_hours": "18:00-23:00",
        "peak_limit_percent": 50,
        "offpeak_unlimited": True
    }
}
```

## Security Considerations

### Peer Authentication

```mermaid
sequenceDiagram
    participant New as New Node
    participant Existing as Existing Node
    participant Registry as WANDA Registry (Optional)
    
    New->>Existing: Connection request
    Existing->>Existing: Verify IPFS identity
    
    alt Using Registry
        Existing->>Registry: Verify node registration
        Registry-->>Existing: Node verified
    else Manual Trust
        Existing->>Existing: Check trusted peers list
    end
    
    Existing-->>New: Connection accepted
    New->>Existing: Exchange signed capabilities
    Existing->>New: Confirm WANDA peer
```

### Trust Levels

| Level | Description | Permissions |
|-------|-------------|-------------|
| **Unknown** | Any IPFS peer | Read public CIDs |
| **WANDA Node** | Verified WANDA installation | Sync content, PubSub |
| **Trusted** | Manually approved | Priority sync, Collaboration |
| **Local** | Same operator | Full access |

## Monitoring

### Network Metrics

```mermaid
flowchart TB
    subgraph "Network Monitoring"
        M1["Peer Count<br/>Connected / Known"]
        M2["Bandwidth<br/>In / Out (Mbps)"]
        M3["Latency<br/>Per peer (ms)"]
        M4["Discovery<br/>Time to find peers"]
        M5["Sync Progress<br/>Queue / Completed"]
        M6["Errors<br/>Connection failures"]
    end
```

### Prometheus Metrics

```python
# Example metrics for monitoring

NETWORK_METRICS = {
    "wanda_peers_connected": Gauge,
    "wanda_peers_known": Gauge,
    "wanda_bandwidth_in_bytes": Counter,
    "wanda_bandwidth_out_bytes": Counter,
    "wanda_peer_latency_ms": Histogram,
    "wanda_discovery_time_seconds": Histogram,
    "wanda_sync_queue_length": Gauge,
    "wanda_connection_errors_total": Counter
}
```

## Regional Considerations

### Latency Optimization

```mermaid
flowchart TB
    subgraph "Geographic Routing"
        User["User Request"]
        
        User --> GeoLookup["Geo Location"]
        GeoLookup --> FindNear["Find nearest peers"]
        
        FindNear --> P1["Peer 1: 50ms"]
        FindNear --> P2["Peer 2: 120ms"]
        FindNear --> P3["Peer 3: 300ms"]
        
        P1 -->|"Primary"| Content["Content Delivery"]
        P2 -->|"Fallback"| Content
    end
```

### Time Zone Coordination

For coordinated observations across time zones:

```json
{
  "observation_event": {
    "name": "Lunar Eclipse 2025",
    "utc_start": "2025-03-14T00:00:00Z",
    "utc_end": "2025-03-14T06:00:00Z",
    "participating_nodes": [
      {
        "node": "WANDA Chile",
        "local_time": "21:00-03:00",
        "visibility": "full"
      },
      {
        "node": "WANDA Spain",
        "local_time": "01:00-07:00",
        "visibility": "partial"
      },
      {
        "node": "WANDA Japan",
        "local_time": "09:00-15:00",
        "visibility": "none"
      }
    ]
  }
}
```

---

**Next**: See [security-considerations.md](./security-considerations.md) for security analysis.


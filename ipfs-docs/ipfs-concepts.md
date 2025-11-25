# IPFS Concepts for WANDA

## Overview

This document explains the core IPFS concepts relevant to the WANDA telescope project. Understanding these fundamentals is essential for implementing and maintaining the distributed storage system.

## What is IPFS?

**IPFS (InterPlanetary File System)** is a peer-to-peer distributed file system that connects all computing devices with the same system of files.

```mermaid
flowchart LR
    subgraph "Traditional Web (HTTP)"
        Client1[Browser] -->|"GET /image.jpg"| Server1[Server]
        Client2[Browser] -->|"GET /image.jpg"| Server1
        Client3[Browser] -->|"GET /image.jpg"| Server1
    end
```

```mermaid
flowchart LR
    subgraph "IPFS Network"
        Node1[Node A] <-->|"CID"| Node2[Node B]
        Node2 <-->|"CID"| Node3[Node C]
        Node3 <-->|"CID"| Node4[Node D]
        Node1 <-->|"CID"| Node4
    end
```

### Key Differences

| Feature | Traditional HTTP | IPFS |
|---------|-----------------|------|
| **Addressing** | Location-based (URL) | Content-based (CID) |
| **Server** | Single point of failure | Distributed network |
| **Caching** | Client-side only | Network-wide |
| **Integrity** | Trust the server | Cryptographically verified |
| **Censorship** | Easy to block | Resistant |

## Core Concepts

### 1. Content Addressing (CID)

Every file in IPFS is identified by its **Content Identifier (CID)** - a cryptographic hash of the content.

```mermaid
flowchart LR
    subgraph "Content Addressing"
        A[capture_0001.jpg] -->|"SHA-256"| B[Hash]
        B --> C["CID:<br/>bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi"]
    end
```

**Properties:**
- Same content → Same CID (always)
- Change 1 byte → Completely different CID
- CID can verify content integrity
- CID is globally unique

**Example:**
```bash
# Add a file to IPFS
$ ipfs add capture_0001.jpg
added QmXnnyufdzAWL5CqZ2RnSNgPbvCc1ALT73s6epPrRnZ1Xy capture_0001.jpg

# The CID is: QmXnnyufdzAWL5CqZ2RnSNgPbvCc1ALT73s6epPrRnZ1Xy
```

### CID Versions

```mermaid
flowchart TB
    subgraph "CID Versions"
        V0["CIDv0<br/>━━━━━━━━━<br/>• Starts with 'Qm'<br/>• Base58 encoded<br/>• SHA-256 only<br/>• Legacy format"]
        
        V1["CIDv1<br/>━━━━━━━━━<br/>• Starts with 'bafy' (base32)<br/>• Self-describing<br/>• Multiple hash algorithms<br/>• Recommended"]
    end
    
    V0 -->|"Upgrade"| V1
```

### 2. Merkle DAG (Directed Acyclic Graph)

IPFS stores files as a **Merkle DAG** - a tree where each node's ID is derived from its content.

```mermaid
flowchart TB
    subgraph "Merkle DAG for Session Directory"
        Root["Directory<br/>CID: Qm...Root"]
        
        Root --> Meta["session_metadata.json<br/>CID: Qm...Meta"]
        Root --> Img1["image_0001.jpg<br/>CID: Qm...Img1"]
        Root --> Img2["image_0002.jpg<br/>CID: Qm...Img2"]
        Root --> Img3["image_0003.jpg<br/>CID: Qm...Img3"]
        
        subgraph "Large File (image_0003.jpg)"
            Img3 --> Chunk1["Chunk 1<br/>CID: Qm...C1"]
            Img3 --> Chunk2["Chunk 2<br/>CID: Qm...C2"]
            Img3 --> Chunk3["Chunk 3<br/>CID: Qm...C3"]
        end
    end
```

**Benefits for WANDA:**
- Session directories have a single CID representing all contents
- Changing one image changes only that image's CID and parent CIDs
- Large images are automatically chunked for efficient transfer
- Deduplication: identical images share the same CID

### 3. Pinning

By default, IPFS may garbage collect files. **Pinning** tells IPFS to keep specific content permanently.

```mermaid
flowchart TB
    subgraph "Pinning Concepts"
        subgraph "Pin Types"
            Direct["Direct Pin<br/>━━━━━━━━━<br/>Pin single block"]
            Recursive["Recursive Pin<br/>━━━━━━━━━<br/>Pin block + all children"]
            Indirect["Indirect Pin<br/>━━━━━━━━━<br/>Pinned via parent"]
        end
        
        subgraph "Example"
            Dir["Session Directory<br/>(Recursive Pin)"]
            Dir --> F1["image_0001.jpg<br/>(Indirect Pin)"]
            Dir --> F2["image_0002.jpg<br/>(Indirect Pin)"]
        end
    end
```

**WANDA Strategy:**
- Recursively pin session directories
- Pin individual captures directly
- Implement pin limits based on storage
- Auto-unpin old content when space needed

### 4. DHT (Distributed Hash Table)

The DHT is how IPFS nodes find content across the network.

```mermaid
sequenceDiagram
    participant You as Your Node
    participant DHT as DHT Network
    participant Provider as Content Provider
    
    Note over You: Want to get CID Qm...XYZ
    
    You->>DHT: Who has Qm...XYZ?
    DHT->>DHT: Route query through DHT
    DHT-->>You: Node at /ip4/1.2.3.4/tcp/4001 has it
    
    You->>Provider: Connect to peer
    You->>Provider: Request blocks for Qm...XYZ
    Provider-->>You: Send blocks
    
    Note over You: Now you have the content!<br/>And can serve it to others.
```

### 5. IPNS (InterPlanetary Name System)

IPNS provides **mutable references** to changing content.

```mermaid
flowchart LR
    subgraph "IPNS Concept"
        Key["Public Key<br/>k51qzi5uqu..."]
        
        subgraph "Time: T1"
            CID1["CID: Qm...v1<br/>(3 images)"]
        end
        
        subgraph "Time: T2"
            CID2["CID: Qm...v2<br/>(5 images)"]
        end
        
        subgraph "Time: T3"
            CID3["CID: Qm...v3<br/>(10 images)"]
        end
        
        Key -->|"resolves to"| CID3
        CID1 -.->|"history"| CID2
        CID2 -.->|"history"| CID3
    end
```

**WANDA Usage:**
- Each WANDA node has an IPNS key
- IPNS points to node's capture directory
- Update IPNS when new images captured
- Other nodes can subscribe to IPNS updates

**Example:**
```bash
# Generate IPNS key for WANDA node
$ ipfs key gen wanda-node

# Publish captures directory to IPNS
$ ipfs name publish --key=wanda-node QmSessionDirectory

# Anyone can resolve it
$ ipfs name resolve k51qzi5uqu5dkkciu33khkzbcmxtyhn2e4zdf7m5d
/ipfs/QmSessionDirectory
```

### 6. PubSub (Publish-Subscribe)

PubSub enables real-time messaging between IPFS nodes.

```mermaid
flowchart TB
    subgraph "WANDA PubSub"
        Topic["/wanda/captures"]
        
        Node1["WANDA Chile"] -->|"subscribe"| Topic
        Node2["WANDA Spain"] -->|"subscribe"| Topic
        Node3["WANDA Japan"] -->|"subscribe"| Topic
        
        Node1 -->|"publish: new CID"| Topic
        Topic -->|"broadcast"| Node2
        Topic -->|"broadcast"| Node3
    end
```

**WANDA Usage:**
- Topic for new capture announcements
- Topic for peer discovery
- Topic for session coordination

### 7. Gateways

IPFS gateways allow HTTP access to IPFS content.

```mermaid
flowchart LR
    subgraph "Gateway Access"
        Browser["Web Browser"]
        
        Browser -->|"HTTP"| Gateway1["ipfs.io/ipfs/Qm..."]
        Browser -->|"HTTP"| Gateway2["dweb.link/ipfs/Qm..."]
        Browser -->|"HTTP"| LocalGW["localhost:8080/ipfs/Qm..."]
        
        Gateway1 --> IPFS["IPFS Network"]
        Gateway2 --> IPFS
        LocalGW --> IPFS
    end
```

**Types:**
- **Public Gateways**: ipfs.io, dweb.link, cloudflare-ipfs.com
- **Local Gateway**: Kubo daemon at localhost:8080
- **Subdomain Gateway**: bafyxxx.ipfs.dweb.link

## IPFS in WANDA Context

### Data Model

```mermaid
flowchart TB
    subgraph "WANDA IPFS Data Model"
        Node["WANDA Node<br/>IPNS: k51qzi..."]
        
        Node --> Latest["Latest Captures<br/>(IPNS resolves here)"]
        
        Latest --> Sessions["Sessions Directory"]
        Sessions --> S1["Session: Moon 2025-01"]
        Sessions --> S2["Session: Orion Nebula"]
        
        S1 --> S1M["metadata.json"]
        S1 --> S1I1["image_0001.jpg"]
        S1 --> S1I2["image_0002.jpg"]
        
        S2 --> S2M["metadata.json"]
        S2 --> S2I1["image_0001.jpg"]
        
        Latest --> Singles["Single Captures"]
        Singles --> C1["capture_0001.jpg"]
        Singles --> C2["capture_0002.jpg"]
    end
```

### Content Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Captured: Camera capture
    Captured --> LocalOnly: Save to disk
    LocalOnly --> Queued: Add to IPFS queue
    Queued --> Adding: IPFS add operation
    Adding --> Pinned: Successfully added
    Adding --> Failed: Error occurred
    Failed --> Queued: Retry
    Pinned --> Announced: PubSub broadcast
    Announced --> Replicated: Peers fetch content
    Replicated --> [*]
```

### Network Discovery

```mermaid
flowchart TB
    subgraph "WANDA Network Discovery"
        subgraph "Step 1: Bootstrap"
            New["New Node"] --> Boot["Bootstrap Nodes"]
            Boot --> DHT["Join DHT"]
        end
        
        subgraph "Step 2: Subscribe"
            DHT --> Sub["Subscribe to<br/>/wanda/discovery"]
        end
        
        subgraph "Step 3: Announce"
            Sub --> Ann["Announce:<br/>{node_id, location, capabilities}"]
        end
        
        subgraph "Step 4: Connect"
            Ann --> Peers["Receive peer announcements"]
            Peers --> Connect["Direct peer connections"]
        end
        
        subgraph "Step 5: Sync"
            Connect --> Sync["Exchange CID lists"]
            Sync --> Fetch["Fetch missing content"]
        end
    end
```

## Key Commands Reference

### Basic Operations

```bash
# Initialize IPFS
ipfs init --profile=lowpower

# Start daemon
ipfs daemon &

# Add file (returns CID)
ipfs add capture.jpg

# Add directory recursively
ipfs add -r session/

# Get file by CID
ipfs cat QmXnnyufdzAWL5CqZ2RnSNgPbvCc1ALT73s6epPrRnZ1Xy > image.jpg

# Get directory
ipfs get QmDirectoryCID -o ./output/
```

### Pinning

```bash
# Pin a CID (recursive by default)
ipfs pin add QmCID

# List pins
ipfs pin ls

# Unpin
ipfs pin rm QmCID

# Run garbage collection
ipfs repo gc
```

### Network

```bash
# Show node ID
ipfs id

# List connected peers
ipfs swarm peers

# Connect to specific peer
ipfs swarm connect /ip4/1.2.3.4/tcp/4001/p2p/QmPeerID

# Check DHT for providers
ipfs dht findprovs QmCID
```

### IPNS

```bash
# Create new key
ipfs key gen my-key

# Publish to IPNS
ipfs name publish --key=my-key QmCID

# Resolve IPNS
ipfs name resolve k51qzi5uqu...
```

### PubSub

```bash
# Subscribe to topic
ipfs pubsub sub /wanda/captures

# Publish to topic
echo "new capture: QmCID" | ipfs pubsub pub /wanda/captures

# List subscriptions
ipfs pubsub ls
```

## Performance Considerations

### On Raspberry Pi

| Concern | Mitigation |
|---------|------------|
| **Memory** | Use lowpower profile, limit connections |
| **CPU** | Avoid intensive operations during capture |
| **Storage** | Set storage limits, regular GC |
| **Bandwidth** | Throttle sync operations |

### Recommended Configuration

```json
{
  "Addresses": {
    "API": "/ip4/127.0.0.1/tcp/5001",
    "Gateway": "/ip4/127.0.0.1/tcp/8080",
    "Swarm": [
      "/ip4/0.0.0.0/tcp/4001",
      "/ip6/::/tcp/4001"
    ]
  },
  "Swarm": {
    "ConnMgr": {
      "LowWater": 50,
      "HighWater": 100,
      "GracePeriod": "20s"
    }
  },
  "Datastore": {
    "StorageMax": "10GB"
  },
  "Routing": {
    "Type": "dhtclient"
  }
}
```

## Glossary

| Term | Definition |
|------|------------|
| **CID** | Content Identifier - hash-based address for content |
| **DAG** | Directed Acyclic Graph - data structure for linking content |
| **DHT** | Distributed Hash Table - routing system for finding content |
| **IPNS** | Mutable naming system built on IPFS |
| **Kubo** | Go implementation of IPFS (formerly go-ipfs) |
| **libp2p** | Networking layer used by IPFS |
| **Merkle** | Tree structure where parent hashes include child hashes |
| **Pin** | Keep content from being garbage collected |
| **PubSub** | Publish-subscribe messaging system |
| **Swarm** | Peer-to-peer network connections |

---

**Next**: See [api-design.md](./api-design.md) for API specifications.


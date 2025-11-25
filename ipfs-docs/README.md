# WANDA IPFS Integration Plan

## Overview

This documentation outlines the plan to integrate **IPFS (InterPlanetary File System)** into the WANDA (World-wide Area Network for Distributed Astronomy) telescope system. IPFS will enable distributed storage and sharing of astrophotography captures across multiple WANDA nodes worldwide.

## Vision

Transform WANDA from a local astrophotography system into a **global distributed astronomy network** where:

- 🌍 **Images are shared globally** - Captures from any WANDA node are accessible to all participants
- 🔗 **Content is permanent** - Images are content-addressed and immutable
- 📡 **Decentralized storage** - No single point of failure for image storage
- 🤝 **Collaborative astronomy** - Multiple observers can contribute to the same celestial events
- 🔄 **Automatic synchronization** - New images propagate across the network automatically

## Current State

Currently, WANDA stores images locally:

```
captures/
├── capture_0001.jpg
├── capture_0002.jpg
├── session_config.json
└── Test session/
    ├── image_0001.jpg
    ├── image_0002.jpg
    └── session_metadata.json
```

**Storage locations** (priority order):
1. USB drive (`/media/astro1/wanda_captures`)
2. Home directory (`/home/astro1/wanda_captures`)
3. Current directory (fallback)

## Target State

With IPFS integration:

```
┌─────────────────────────────────────────────────────────────────┐
│                    WANDA IPFS Network                           │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  WANDA Node  │◄──►│  WANDA Node  │◄──►│  WANDA Node  │      │
│  │   (Chile)    │    │   (Spain)    │    │   (Japan)    │      │
│  │              │    │              │    │              │      │
│  │  Local IPFS  │    │  Local IPFS  │    │  Local IPFS  │      │
│  │    Daemon    │    │    Daemon    │    │    Daemon    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             │                                   │
│                    ┌────────▼────────┐                         │
│                    │  IPFS Network   │                         │
│                    │  (Global DHT)   │                         │
│                    └─────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

## Documentation Structure

| Document | Description |
|----------|-------------|
| [architecture.md](./architecture.md) | Technical architecture with Mermaid diagrams |
| [ipfs-concepts.md](./ipfs-concepts.md) | IPFS fundamentals for the team |
| [implementation-phases.md](./implementation-phases.md) | Phased rollout plan |
| [api-design.md](./api-design.md) | API changes and new endpoints |
| [storage-strategy.md](./storage-strategy.md) | Storage strategy and data flow |
| [network-topology.md](./network-topology.md) | Distributed network architecture |
| [security-considerations.md](./security-considerations.md) | Security and privacy analysis |
| [testing-strategy.md](./testing-strategy.md) | Testing approach for IPFS |

## Key Decisions

### Why IPFS?

| Feature | Benefit for WANDA |
|---------|-------------------|
| **Content Addressing** | Each image has a unique hash (CID) - no duplicates, verifiable integrity |
| **Decentralization** | No central server needed - peer-to-peer sharing |
| **Offline-First** | Nodes work offline and sync when connected |
| **Version Control** | IPNS allows updating references while preserving history |
| **Efficient Distribution** | Popular images are cached across multiple nodes |

### Implementation Approach

1. **Non-Breaking**: IPFS integration will be additive, not replacing local storage
2. **Dual Storage**: Images saved locally AND published to IPFS
3. **Graceful Degradation**: System works without network connectivity
4. **Progressive Enhancement**: New IPFS features added incrementally

## Prerequisites

### Hardware Requirements
- Raspberry Pi 4/5 with 4GB+ RAM
- 64GB+ SD card or USB storage
- Network connectivity (Ethernet preferred)

### Software Dependencies
- IPFS Kubo (Go implementation) v0.25+
- Python IPFS HTTP client
- libp2p for peer discovery

## Quick Start (Future)

```bash
# Install IPFS daemon on Raspberry Pi
wget https://dist.ipfs.tech/kubo/v0.25.0/kubo_v0.25.0_linux-arm64.tar.gz
tar -xvzf kubo_v0.25.0_linux-arm64.tar.gz
cd kubo && sudo bash install.sh

# Initialize IPFS
ipfs init --profile=lowpower

# Configure for WANDA network
ipfs config --json Experimental.Libp2pStreamMounting true

# Start daemon
ipfs daemon --enable-pubsub-experiment &
```

## Success Metrics

| Metric | Target |
|--------|--------|
| Image upload latency | < 5 seconds for 10MB image |
| Network sync time | < 30 seconds for new image propagation |
| Storage overhead | < 10% vs. local-only storage |
| Node discovery time | < 60 seconds to find peers |
| System availability | 99.5% uptime for local operations |

## Timeline Estimate

| Phase | Duration | Description |
|-------|----------|-------------|
| Phase 1 | 2 weeks | Core IPFS integration (local daemon) |
| Phase 2 | 2 weeks | API changes and UI updates |
| Phase 3 | 1 week | Peer discovery and network features |
| Phase 4 | 1 week | Testing and optimization |

**Total estimated time: 6 weeks**

## Related Resources

- [IPFS Documentation](https://docs.ipfs.tech/)
- [IPFS Kubo GitHub](https://github.com/ipfs/kubo)
- [libp2p Documentation](https://docs.libp2p.io/)
- [IPNS Specification](https://specs.ipfs.tech/ipns/)

---

**Next Steps**: Start with [architecture.md](./architecture.md) to understand the technical design.


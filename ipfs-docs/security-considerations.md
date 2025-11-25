# WANDA IPFS Security Considerations

## Overview

This document analyzes security considerations for the WANDA IPFS integration, covering data privacy, node authentication, network security, and threat mitigation.

## Threat Model

```mermaid
flowchart TB
    subgraph "Threat Categories"
        T1["Data Exposure<br/>━━━━━━━━━━━━━<br/>• Unintended public access<br/>• Metadata leakage<br/>• Location exposure"]
        
        T2["Network Attacks<br/>━━━━━━━━━━━━━<br/>• Eclipse attacks<br/>• Sybil attacks<br/>• DoS/DDoS"]
        
        T3["Node Compromise<br/>━━━━━━━━━━━━━<br/>• Unauthorized access<br/>• Malware injection<br/>• Key theft"]
        
        T4["Content Integrity<br/>━━━━━━━━━━━━━<br/>• Data corruption<br/>• Fake content<br/>• Impersonation"]
    end
```

## Data Privacy

### Content Visibility

```mermaid
flowchart TB
    subgraph "IPFS Content Visibility"
        Content["Captured Image"]
        
        Content --> Add["ipfs add"]
        Add --> CID["CID Generated"]
        
        CID --> Local["Local Node<br/>(Private until shared)"]
        CID --> DHT["DHT Announcement<br/>(CID becomes discoverable)"]
        CID --> PubSub["PubSub Broadcast<br/>(Actively shared)"]
        
        Local -->|"No announcement"| Private["⚠️ Still accessible if CID known"]
        DHT -->|"Announced"| Public["Public to anyone with CID"]
        PubSub -->|"Broadcast"| Network["Shared with WANDA network"]
    end
```

### Privacy Levels

| Level | Description | Implementation |
|-------|-------------|----------------|
| **Private** | Node only, no DHT | `ipfs add --offline` |
| **WANDA Network** | Shared with verified nodes | Encrypted + WANDA PubSub |
| **Public** | Available to anyone | Standard IPFS add |

### Sensitive Data Protection

```mermaid
flowchart LR
    subgraph "Data Classification"
        A["Image Data<br/>━━━━━━━━━━━━━<br/>Generally public<br/>Astrophotography"]
        
        B["Metadata<br/>━━━━━━━━━━━━━<br/>Timestamps<br/>Camera settings<br/>Location (optional)"]
        
        C["Node Identity<br/>━━━━━━━━━━━━━<br/>Peer ID<br/>IP addresses<br/>Location"]
        
        D["Keys<br/>━━━━━━━━━━━━━<br/>IPFS identity<br/>IPNS keys"]
    end
    
    A --> A1["Low sensitivity"]
    B --> B1["Medium sensitivity"]
    C --> C1["High sensitivity"]
    D --> D1["Critical"]
```

### Location Privacy

**Risks:**
- IPFS peers can see connecting IP addresses
- Metadata may contain GPS coordinates
- Node names may reveal location

**Mitigations:**

```python
# ipfs/config.py

PRIVACY_CONFIG = {
    # Strip GPS data from images before IPFS
    "strip_exif_gps": True,
    
    # Anonymize node location in announcements
    "location_precision": "country",  # "city", "country", "none"
    
    # Use relay for privacy
    "force_relay_connections": False,
    
    # Metadata sanitization
    "sanitize_metadata": {
        "remove_gps": True,
        "remove_timestamps": False,
        "remove_camera_serial": True
    }
}
```

## Authentication & Authorization

### Node Identity

```mermaid
flowchart TB
    subgraph "Identity Hierarchy"
        IPFS["IPFS Peer ID<br/>━━━━━━━━━━━━━<br/>12D3KooW...<br/>Cryptographic identity"]
        
        WANDA["WANDA Node ID<br/>━━━━━━━━━━━━━<br/>Derived from IPFS ID<br/>+ WANDA signature"]
        
        Human["Operator ID<br/>━━━━━━━━━━━━━<br/>Optional<br/>Human-readable name"]
        
        IPFS --> WANDA
        WANDA --> Human
    end
```

### Trust Establishment

```mermaid
sequenceDiagram
    participant NewNode as New WANDA Node
    participant Peer as Existing Peer
    participant Registry as Trust Registry (Optional)
    
    Note over NewNode: Generate IPFS identity
    NewNode->>NewNode: Create WANDA signature
    
    NewNode->>Peer: Connection request + signature
    
    alt With Registry
        Peer->>Registry: Verify node signature
        Registry->>Registry: Check registration
        Registry-->>Peer: Verified / Unknown
    else Without Registry
        Peer->>Peer: Verify cryptographic signature
        Peer->>Peer: Check local trust list
    end
    
    alt Verified
        Peer-->>NewNode: Accept as WANDA peer
        Peer->>Peer: Add to trusted peers
    else Unknown
        Peer-->>NewNode: Accept as generic IPFS peer
        Peer->>Peer: Limited permissions
    end
```

### Authorization Matrix

| Action | Unknown Peer | WANDA Node | Trusted Node | Local |
|--------|--------------|------------|--------------|-------|
| Fetch public CIDs | ✅ | ✅ | ✅ | ✅ |
| Receive announcements | ❌ | ✅ | ✅ | ✅ |
| Sync captures | ❌ | ✅ | ✅ | ✅ |
| Join sessions | ❌ | ❌ | ✅ | ✅ |
| Modify settings | ❌ | ❌ | ❌ | ✅ |

## Network Security

### Attack Vectors

```mermaid
flowchart TB
    subgraph "Network Attack Vectors"
        A["Eclipse Attack<br/>━━━━━━━━━━━━━<br/>Surround node with malicious peers<br/>Control all connections"]
        
        B["Sybil Attack<br/>━━━━━━━━━━━━━<br/>Create many fake identities<br/>Overwhelm DHT"]
        
        C["Content Poisoning<br/>━━━━━━━━━━━━━<br/>Serve wrong content for CID<br/>(Mitigated by hashing)"]
        
        D["DoS/DDoS<br/>━━━━━━━━━━━━━<br/>Flood with requests<br/>Exhaust resources"]
        
        E["Man-in-Middle<br/>━━━━━━━━━━━━━<br/>Intercept connections<br/>(Mitigated by encryption)"]
    end
```

### Mitigations

#### Eclipse Attack Prevention

```python
# ipfs/config.py

SECURITY_CONFIG = {
    # Maintain connections to trusted bootstrap nodes
    "min_bootstrap_connections": 2,
    
    # Require peer diversity
    "peer_diversity": {
        "enabled": True,
        "min_unique_asns": 3,
        "max_peers_per_asn": 10
    },
    
    # Static trusted peers
    "static_peers": [
        "/ip4/1.2.3.4/tcp/4001/p2p/12D3KooWTrusted1...",
        "/ip4/5.6.7.8/tcp/4001/p2p/12D3KooWTrusted2..."
    ]
}
```

#### Sybil Attack Prevention

```mermaid
flowchart LR
    subgraph "Sybil Mitigations"
        A["Proof of Work<br/>(IPFS default)"]
        B["Peer Scoring<br/>(Reputation)"]
        C["Connection Limits<br/>(Resource bound)"]
        D["DHT Client Mode<br/>(Reduced exposure)"]
    end
```

#### DoS Prevention

```python
# ipfs/config.py

RATE_LIMITING = {
    # Connection rate limiting
    "max_new_connections_per_minute": 20,
    
    # Request rate limiting
    "max_requests_per_minute": 100,
    
    # Bandwidth limiting
    "max_bandwidth_mbps": 50,
    
    # Resource limits
    "max_concurrent_requests": 10,
    "request_timeout_seconds": 30
}
```

### Firewall Configuration

```bash
# Recommended iptables rules for WANDA IPFS

# Allow IPFS swarm (P2P connections)
iptables -A INPUT -p tcp --dport 4001 -j ACCEPT
iptables -A INPUT -p udp --dport 4001 -j ACCEPT

# Allow IPFS API (localhost only)
iptables -A INPUT -p tcp --dport 5001 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 5001 -j DROP

# Allow IPFS gateway (localhost only or restrict to LAN)
iptables -A INPUT -p tcp --dport 8080 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -s 192.168.0.0/16 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -j DROP

# Rate limit new connections
iptables -A INPUT -p tcp --dport 4001 -m state --state NEW -m limit --limit 10/min -j ACCEPT
```

## Content Integrity

### Verification Chain

```mermaid
flowchart TB
    subgraph "Content Verification"
        A["Receive Content"] --> B["Verify CID Hash"]
        
        B -->|"Hash matches"| C["Content authentic"]
        B -->|"Hash mismatch"| D["Reject content"]
        
        C --> E["Verify WANDA signature"]
        E -->|"Valid signature"| F["From known WANDA node"]
        E -->|"No signature"| G["Unknown source"]
        E -->|"Invalid"| H["Reject / Flag"]
    end
```

### Image Signing

```mermaid
sequenceDiagram
    participant Camera
    participant Node as WANDA Node
    participant IPFS
    participant Peer
    
    Camera->>Node: Capture image
    Node->>Node: Create metadata
    Node->>Node: Sign metadata with node key
    
    Node->>IPFS: Add image
    IPFS-->>Node: CID
    
    Node->>IPFS: Add signed metadata
    IPFS-->>Node: Metadata CID
    
    Node->>Peer: Announce capture + signatures
    
    Peer->>IPFS: Fetch content
    Peer->>Peer: Verify CID integrity
    Peer->>Peer: Verify node signature
    Peer->>Peer: Accept as authentic
```

### Metadata Signing

```python
# ipfs/security.py

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
import json

class ContentSigner:
    def __init__(self, private_key_path: str):
        with open(private_key_path, 'rb') as f:
            self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
                f.read()
            )
        self.public_key = self.private_key.public_key()
    
    def sign_capture_metadata(self, metadata: dict) -> dict:
        """Sign capture metadata for verification by peers."""
        # Canonical JSON encoding
        data = json.dumps(metadata, sort_keys=True).encode()
        
        # Sign with node's private key
        signature = self.private_key.sign(data)
        
        return {
            **metadata,
            "signature": signature.hex(),
            "signer_public_key": self.public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            ).hex()
        }
    
    def verify_signature(self, metadata: dict) -> bool:
        """Verify a signed metadata object."""
        signature = bytes.fromhex(metadata.pop("signature"))
        public_key_bytes = bytes.fromhex(metadata.pop("signer_public_key"))
        
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(
            public_key_bytes
        )
        
        data = json.dumps(metadata, sort_keys=True).encode()
        
        try:
            public_key.verify(signature, data)
            return True
        except Exception:
            return False
```

## Key Management

### Key Types

```mermaid
flowchart TB
    subgraph "WANDA Key Hierarchy"
        IPFS["IPFS Identity Key<br/>━━━━━━━━━━━━━<br/>Ed25519<br/>Auto-generated<br/>~/.ipfs/config"]
        
        IPNS["IPNS Publishing Key<br/>━━━━━━━━━━━━━<br/>Ed25519<br/>For mutable names<br/>~/.ipfs/keystore/"]
        
        WANDA["WANDA Signing Key<br/>━━━━━━━━━━━━━<br/>Ed25519<br/>Content signatures<br/>~/.wanda/keys/"]
    end
```

### Key Storage

```python
# Secure key storage recommendations

KEY_STORAGE = {
    # IPFS keys (managed by Kubo)
    "ipfs_identity": "~/.ipfs/config",  # Auto-managed
    "ipns_keys": "~/.ipfs/keystore/",   # Auto-managed
    
    # WANDA keys
    "wanda_signing": {
        "path": "~/.wanda/keys/signing.key",
        "permissions": 0o600,
        "backup": "encrypted_backup.key.enc"
    },
    
    # Key backup
    "backup_encryption": "AES-256-GCM",
    "backup_location": "offline_storage"
}
```

### Key Rotation

```mermaid
flowchart LR
    subgraph "Key Rotation Process"
        A["Generate new key"] --> B["Sign transition message<br/>with old key"]
        B --> C["Publish to network"]
        C --> D["Update local config"]
        D --> E["Revoke old key<br/>(after grace period)"]
    end
```

## Incident Response

### Security Events

| Event | Severity | Response |
|-------|----------|----------|
| Unauthorized access attempt | Medium | Log, rate limit, alert |
| Invalid signature detected | Medium | Reject, log, flag peer |
| Key compromise suspected | Critical | Rotate keys, alert network |
| DoS attack detected | High | Rate limit, block IPs |
| Malicious content found | High | Unpin, report, blacklist source |

### Monitoring

```python
# ipfs/security.py

SECURITY_MONITORING = {
    "log_events": [
        "connection_rejected",
        "signature_invalid",
        "rate_limit_exceeded",
        "suspicious_peer",
        "unauthorized_request"
    ],
    
    "alert_thresholds": {
        "failed_connections_per_hour": 100,
        "invalid_signatures_per_hour": 10,
        "rate_limit_hits_per_hour": 50
    },
    
    "alert_methods": ["log", "websocket", "email"],
    
    "audit_log_path": "/var/log/wanda/security.log"
}
```

### Response Playbooks

```mermaid
flowchart TD
    subgraph "Incident: Compromised Key"
        A["Key compromise detected"] --> B["Immediate: Disable key"]
        B --> C["Generate new key pair"]
        C --> D["Sign revocation with backup key"]
        D --> E["Broadcast revocation to network"]
        E --> F["Update all signatures"]
        F --> G["Publish new IPNS records"]
        G --> H["Notify trusted peers"]
        H --> I["Post-mortem analysis"]
    end
```

## Best Practices Checklist

### Node Setup

- [ ] Run IPFS API on localhost only (127.0.0.1:5001)
- [ ] Configure firewall rules
- [ ] Enable connection limiting
- [ ] Use DHT client mode (reduced attack surface)
- [ ] Set up log monitoring

### Data Handling

- [ ] Strip sensitive EXIF data before upload
- [ ] Sign all metadata with node key
- [ ] Verify signatures on received content
- [ ] Implement content moderation for shared network

### Key Security

- [ ] Secure key file permissions (600)
- [ ] Back up keys securely (encrypted, offline)
- [ ] Document key rotation procedure
- [ ] Have incident response plan ready

### Network Security

- [ ] Maintain diverse peer connections
- [ ] Configure rate limiting
- [ ] Monitor for suspicious activity
- [ ] Keep Kubo/IPFS updated

## Compliance Considerations

### Data Sovereignty

```mermaid
flowchart TB
    subgraph "Data Sovereignty Considerations"
        A["Image captured in Chile"] --> B{"Shared to network?"}
        
        B -->|"Yes"| C["May replicate to any node"]
        C --> D["Copies in multiple jurisdictions"]
        
        B -->|"No"| E["Stays on local node"]
        E --> F["Subject to local laws only"]
    end
```

### GDPR Considerations

If operating in EU or handling EU user data:

- **Right to erasure**: Unpinning removes local copy, but cannot force network erasure
- **Data minimization**: Don't collect unnecessary metadata
- **Consent**: Ensure operators consent to distributed storage

### Recommendations

1. **Default to local-only** for sensitive content
2. **Document data flows** for compliance
3. **Provide opt-out** for network sharing
4. **Implement data retention policies**

---

**Next**: See [testing-strategy.md](./testing-strategy.md) for testing approach.


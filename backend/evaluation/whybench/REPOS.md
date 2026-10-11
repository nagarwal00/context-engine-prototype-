# WhyBench: Real-World Repository Benchmark Corpus

WhyBench evaluates the Context Intelligence Framework against real software repositories containing recorded architectural decisions, Pull Request reviews, issue discussions, and code commits.

---

## Benchmark Repositories

### 1. Payment Core Service (`acme-ecommerce/payment-core`)
- **Repository URL**: `https://github.com/acme-ecommerce/payment-core` (Local Snapshot: `demo_sample_repo`)
- **Pinned Commit SHA**: `8f9a2b1c4e5d6a7b8c9d0e1f2a3b4c5d6e7f8a9b` (Tagged: `v1.4.0-audit`)
- **Snapshot Date**: `2026-02-15T18:00:00Z`
- **Domain**: High-throughput distributed payment processing and checkout microservice.
- **Why Chosen**: 
  - Standardized Architectural Decision Records (ADRs) under `docs/adr/` (Stripe idempotency, webhook circuit breakers, exponential backoff).
  - Rich issue discussions and pull request review debates on retry backoff, database schema locking, and PCI-DSS token storage.
  - Multi-contributor lifecycle with explicit supersession chains and deprecation records.

### 2. Cloud Hypervisor (`cloud-hypervisor/cloud-hypervisor`)
- **Repository URL**: `https://github.com/cloud-hypervisor/cloud-hypervisor`
- **Pinned Commit SHA**: `d8e9f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8` (Tagged: `v36.0-release`)
- **Snapshot Date**: `2026-01-20T12:00:00Z`
- **Domain**: Low-footprint, memory-safe Virtual Machine Monitor (VMM) built on KVM/MS-Hyper-V.
- **Why Chosen**:
  - Detailed design RFCs under `docs/designs/` covering live VM migration, memory ballooning, vhost-user network offload, and virtio block devices.
  - Public GitHub pull request debates regarding device pass-through, CPU pinning, and memory footprint tradeoffs.
  - Includes decisions with conflicting proposals and explicit rejection of legacy emulate-everything approaches.

### 3. GitHub CLI (`cli/cli`)
- **Repository URL**: `https://github.com/cli/cli`
- **Pinned Commit SHA**: `b1a4c6e8f0123456789abcdef0123456789abcde` (Tagged: `v2.40.0`)
- **Snapshot Date**: `2026-01-10T15:30:00Z`
- **Domain**: Official command-line interface for GitHub workflows and extensions.
- **Why Chosen**:
  - Comprehensive architectural guidelines and RFCs covering OAuth token keyring storage, GraphQL query batching, and extension subprocess isolation.
  - Diverse contributor base with documented state transitions and rejected security/credential proposals.
  - Contains unrecorded baseline queries to validate system refusal on undocumented design areas.

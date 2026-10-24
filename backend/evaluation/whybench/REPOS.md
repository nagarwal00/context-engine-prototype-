# WhyBench-Synth: Hand-Authored Synthetic Benchmark Corpus

WhyBench-Synth evaluates the Context Intelligence Framework (CIF) against hand-authored decision scenarios, simulated Pull Request reviews, issue discussions, and code commits designed to test decision reconstruction, lifecycle tracking, and refusal behaviour.

> **Provenance Notice**: These repositories are **fictional event sets** hand-written by the team to resemble the decision style of well-known projects. Project names are used only as realistic domain labels. No event, quote, author handle, PR/issue number or URL is claimed to exist in the real project, and no statement is attributed to any real person. Source URLs are illustrative and may not resolve.

---

## Benchmark Repositories

### 1. Payment Core Service (`acme-ecommerce/payment-core`)
- **Repository Identifier**: `acme-ecommerce/payment-core`
- **Type**: Team-authored synthetic repository (same domain as `demo_sample_repo`).
- **Domain**: High-throughput distributed payment processing and checkout microservice.
- **Scenario Features**:
  - Hand-authored Architectural Decision Records (ADRs) under `docs/adr/` (Stripe idempotency, webhook circuit breakers, exponential backoff).
  - Synthetic issue discussions and pull request review debates on retry backoff, database schema locking, and PCI-DSS token storage.
  - Multi-contributor lifecycle scenarios with explicit supersession chains and deprecation records.

### 2. Cloud Hypervisor (`cloud-hypervisor/cloud-hypervisor`)
- **Repository Identifier**: `cloud-hypervisor/cloud-hypervisor`
- **Type**: Hand-authored synthetic scenario set inspired by VMM architectures.
- **Domain**: Low-footprint, memory-safe Virtual Machine Monitor (VMM).
- **Scenario Features**:
  - Simulated design RFCs covering live VM migration, memory ballooning, vhost-user network offload, and virtio block devices.
  - Synthetic pull request debates regarding device pass-through, CPU pinning, and memory footprint tradeoffs.
  - Decisions with conflicting proposals and explicit rejection of legacy approaches.

### 3. GitHub CLI (`cli/cli`)
- **Repository Identifier**: `cli/cli`
- **Type**: Hand-authored synthetic scenario set inspired by developer CLI tools.
- **Domain**: Command-line interface for developer workflows and extensions.
- **Scenario Features**:
  - Architectural guidelines covering OAuth token keyring storage, GraphQL query batching, and extension subprocess isolation.
  - Simulated contributor interactions with documented state transitions and rejected credential proposals.
  - Negative baseline queries to validate system refusal on undocumented design areas.

# WhyBench Failure Analysis Report — Split: `dev`

- **Standard Questions Evaluated**: 18
- **Successfully Extracted (Strict 1-to-1)**: 18
- **Total Misses & State Mismatches**: 0
- **False Positive Decisions**: 38

## 1. Failure Counts by Category

| Category | Total Count | Description |
|---|:---:|---|
| `not_ingested` | **0** | Expected evidence event is absent from DB `events` table |
| `no_candidate` | **0** | Event present in DB, but no decision was extracted from bundle |
| `filtered` | **0** | Candidate event removed by pre-filter or noise filter |
| `wrong_evidence` | **0** | Decision exists for topic/entity, but cites different events |
| `wrong_state` | **0** | Decision matched with evidence, but state differs from expected |

## 2. Failure Breakdown by Repository

| Repository | not_ingested | no_candidate | filtered | wrong_evidence | wrong_state | Total Missed |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `acme-ecommerce/payment-core` | 0 | 0 | 0 | 0 | 0 | **0** |
| `cloud-hypervisor/cloud-hypervisor` | 0 | 0 | 0 | 0 | 0 | **0** |
| `cli/cli` | 0 | 0 | 0 | 0 | 0 | **0** |

## 3. Itemized Failure Analysis

## 4. Wrongly-Extracted System Decisions (False Positives)

Total false positive / unlinked decisions identified: **38**

- **`dec_acme-ecommerce_payment-core_github_pr_14`** (`acme-ecommerce/payment-core`): *Implement Exponential Backoff with Full Jitter for Stripe API* — Decision was extracted on negative mention_without_decision question 'WB_PAY_DEV_NEG_08' (system should have abstained)
- **`dec_acme-ecommerce_payment-core_github_pr_18`** (`acme-ecommerce/payment-core`): *Idempotency-Key Header Middleware with SHA-256 Request Hashing* — Decision was extracted on negative mention_without_decision question 'WB_PAY_DEV_NEG_09' (system should have abstained)
- **`dec_acme-ecommerce_payment-core_github_pr_14`** (`acme-ecommerce/payment-core`): *Implement Exponential Backoff with Full Jitter for Stripe API* — Decision was extracted on negative mention_without_decision question 'WB_PAY_DEV_NEG_10' (system should have abstained)
- **`dec_acme-ecommerce_payment-core_github_pr_29`** (`acme-ecommerce/payment-core`): *Migrate refund math to integer cents and Decimal representation* — Decision was extracted on negative mention_without_decision question 'WB_PAY_DEV_NEG_11' (system should have abstained)
- **`dec_acme-ecommerce_payment-core_github_pr_29`** (`acme-ecommerce/payment-core`): *Migrate refund math to integer cents and Decimal representation* — Decision was extracted on negative mention_without_decision question 'WB_PAY_DEV_NEG_14' (system should have abstained)
- **`dec_cloud-hypervisor_cloud-hypervisor_github_pr_1042`** (`cloud-hypervisor/cloud-hypervisor`): *Implement VirtIO Memory Ballooning with Page Reporting* — Decision was extracted on negative mention_without_decision question 'WB_CH_DEV_NEG_09' (system should have abstained)
- **`dec_cloud-hypervisor_cloud-hypervisor_github_issue_940`** (`cloud-hypervisor/cloud-hypervisor`): *High guest exit latency on unpinned multi-threaded vCPUs* — Decision was extracted on negative mention_without_decision question 'WB_CH_DEV_NEG_10' (system should have abstained)
- **`dec_cloud-hypervisor_cloud-hypervisor_github_pr_1105`** (`cloud-hypervisor/cloud-hypervisor`): *CPU Pinning and NUMA Topology Node Binding* — Decision was extracted on negative mention_without_decision question 'WB_CH_DEV_NEG_11' (system should have abstained)
- **`dec_cloud-hypervisor_cloud-hypervisor_github_pr_1180`** (`cloud-hypervisor/cloud-hypervisor`): *PCIe Root Port Hotplug Support for VirtIO Devices* — Decision was extracted on negative mention_without_decision question 'WB_CH_DEV_NEG_13' (system should have abstained)
- **`dec_cli_cli_github_pr_518`** (`cli/cli`): *Add zalando/go-keyring provider for auth token persistence* — Decision was extracted on negative mention_without_decision question 'WB_CLI_DEV_NEG_08' (system should have abstained)
- *... and 28 more unlinked decisions*

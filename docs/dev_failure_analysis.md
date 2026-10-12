# WhyBench Failure Analysis Report — Split: `dev`

- **Standard Questions Evaluated**: 18
- **Successfully Extracted (Strict 1-to-1)**: 18
- **Total Misses & State Mismatches**: 0
- **False Positive Decisions**: 22

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

Total false positive / unlinked decisions identified: **22**

- **`dec_cli_cli_github_pr_670`** (`cli/cli`): *Fork-exec child subprocess isolation with restricted inherited env for extension* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cli_cli_pr_review_comment_c712`** (`cli/cli`): *Reject executing third-party extensions via in-process Go plugins* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cli_cli_adr_docs_rfc_004-termenv-formatting_md`** (`cli/cli`): *RFC 004: Terminal Color and Hyperlink Detection via termenv* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cli_cli_github_pr_735`** (`cli/cli`): *Auto-detect TTY and disable ANSI formatting in non-interactive pipelines* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cli_cli_adr_docs_rfc_005-git-credential-helper_md`** (`cli/cli`): *RFC 005: Git Credential Helper Protocol Provider* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cli_cli_github_pr_810`** (`cli/cli`): *Implementation of gh auth git-credential helper protocol* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cli_cli_pr_review_comment_c840`** (`cli/cli`): *Reject global auth token in HTTP GET query string* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cloud-hypervisor_cloud-hypervisor_github_issue_940`** (`cloud-hypervisor/cloud-hypervisor`): *High guest exit latency on unpinned multi-threaded vCPUs* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cloud-hypervisor_cloud-hypervisor_pr_review_comment_c615`** (`cloud-hypervisor/cloud-hypervisor`): *Reject legacy floppy and IDE device emulation* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cloud-hypervisor_cloud-hypervisor_adr_docs_designs_virtio-fs_md`** (`cloud-hypervisor/cloud-hypervisor`): *Design: VirtIO-FS Shared Host Filesystem with Direct Access (DAX) Window* — System decision extracted from repository history does not match any evaluated ground-truth question
- *... and 12 more unlinked decisions*

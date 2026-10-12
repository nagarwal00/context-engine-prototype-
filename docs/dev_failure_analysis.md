# WhyBench Failure Analysis Report — Split: `dev`

- **Standard Questions Evaluated**: 18
- **Successfully Extracted (Strict 1-to-1)**: 10
- **Total Misses & State Mismatches**: 8
- **False Positive Decisions**: 47

## 1. Failure Counts by Category

| Category | Total Count | Description |
|---|:---:|---|
| `not_ingested` | **0** | Expected evidence event is absent from DB `events` table |
| `no_candidate` | **3** | Event present in DB, but no decision was extracted from bundle |
| `filtered` | **0** | Candidate event removed by pre-filter or noise filter |
| `wrong_evidence` | **5** | Decision exists for topic/entity, but cites different events |
| `wrong_state` | **0** | Decision matched with evidence, but state differs from expected |

## 2. Failure Breakdown by Repository

| Repository | not_ingested | no_candidate | filtered | wrong_evidence | wrong_state | Total Missed |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `acme-ecommerce/payment-core` | 0 | 1 | 0 | 2 | 0 | **3** |
| `cloud-hypervisor/cloud-hypervisor` | 0 | 1 | 0 | 2 | 0 | **3** |
| `cli/cli` | 0 | 1 | 0 | 1 | 0 | **2** |

## 3. Itemized Failure Analysis

### `WB_PAY_02` (acme-ecommerce/payment-core) — `wrong_evidence`
- **Question**: How were Stripe API 429 rate limits resolved under flash sale load?
- **Expected State**: `accepted`
- **Expected Events**: `['evt_why_pay_pr_14', 'evt_why_pay_issue_08']`
- **Failure Reason**: Decision 'dec_acme-ecommerce_payment-core_proposed_8' exists for overlapping topic, but cites [] instead of expected ['evt_why_pay_pr_14', 'evt_why_pay_issue_08']

### `WB_PAY_03` (acme-ecommerce/payment-core) — `no_candidate`
- **Question**: Why were fixed 500ms sleep retries rejected for Stripe API calls?
- **Expected State**: `rejected`
- **Expected Events**: `['evt_why_pay_rev_c301']`
- **Failure Reason**: Event(s) ['evt_why_pay_rev_c301'] present in DB, but extractor extracted 0 decision candidates from its bundle

### `WB_PAY_05` (acme-ecommerce/payment-core) — `wrong_evidence`
- **Question**: Why was SQLAlchemy async connection pool adopted for the database?
- **Expected State**: `accepted`
- **Expected Events**: `['evt_why_pay_commit_7a']`
- **Failure Reason**: Decision 'dec_acme-ecommerce_payment-core_proposed_7a8b9c0d1e2f3a4b' exists for overlapping topic, but cites [] instead of expected ['evt_why_pay_commit_7a']

### `WB_CH_02` (cloud-hypervisor/cloud-hypervisor) — `wrong_evidence`
- **Question**: Why was synchronous balloon deflation rejected in virtio-balloon?
- **Expected State**: `rejected`
- **Expected Events**: `['evt_why_ch_rev_c502']`
- **Failure Reason**: Decision 'dec_cloud-hypervisor_cloud-hypervisor_proposed_c502' exists for overlapping topic, but cites [] instead of expected ['evt_why_ch_rev_c502']

### `WB_CH_04` (cloud-hypervisor/cloud-hypervisor) — `wrong_evidence`
- **Question**: Why did Cloud Hypervisor enable virtio unused page reporting in PR #1042?
- **Expected State**: `accepted`
- **Expected Events**: `['evt_why_ch_pr_1042']`
- **Failure Reason**: Decision 'dec_cloud-hypervisor_cloud-hypervisor_proposed_1042' exists for overlapping topic, but cites [] instead of expected ['evt_why_ch_pr_1042']

### `WB_CH_06` (cloud-hypervisor/cloud-hypervisor) — `no_candidate`
- **Question**: How was multi-threaded vCPU tail latency jitter mitigated?
- **Expected State**: `accepted`
- **Expected Events**: `['evt_why_ch_pr_1105', 'evt_why_ch_issue_940']`
- **Failure Reason**: Event(s) ['evt_why_ch_issue_940', 'evt_why_ch_pr_1105'] present in DB, but extractor extracted 0 decision candidates from its bundle

### `WB_CLI_02` (cli/cli) — `wrong_evidence`
- **Question**: Why was custom symmetric key encryption rejected for storing gh credentials?
- **Expected State**: `rejected`
- **Expected Events**: `['evt_why_cli_rev_c601']`
- **Failure Reason**: Decision 'dec_cli_cli_proposed_c601' exists for overlapping topic, but cites [] instead of expected ['evt_why_cli_rev_c601']

### `WB_CLI_04` (cli/cli) — `no_candidate`
- **Question**: How was zalando/go-keyring integrated into the gh auth login command?
- **Expected State**: `accepted`
- **Expected Events**: `['evt_why_cli_pr_518']`
- **Failure Reason**: Event(s) ['evt_why_cli_pr_518'] present in DB, but extractor extracted 0 decision candidates from its bundle

## 4. Wrongly-Extracted System Decisions (False Positives)

Total false positive / unlinked decisions identified: **47**

- **`dec_cli_cli_proposed_412`** (`cli/cli`): *Proposed Candidate Decision for Issue #412: Plaintext tokens exposed in process environment variables and config files* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cli_cli_proposed_518`** (`cli/cli`): *Proposed Candidate Decision for PR #518: Add zalando/go-keyring provider for auth token persistence (Closes #412)* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cli_cli_proposed_c601`** (`cli/cli`): *Proposed Candidate Decision for Review on PR #518: Reject custom symmetric encryption key on disk* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cli_cli_proposed_480`** (`cli/cli`): *Proposed Candidate Decision for Issue #480: N+1 REST API roundtrips during repo list with pull requests* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cli_cli_proposed_550`** (`cli/cli`): *Proposed Candidate Decision for Issue #550: Extension crash corrupts parent terminal state and escapes PATH* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cli_cli_proposed_670`** (`cli/cli`): *Proposed Candidate Decision for PR #670: Fork-exec child subprocess isolation with restricted inherited env for extensions (Closes #550)* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cli_cli_proposed_c712`** (`cli/cli`): *Proposed Candidate Decision for Review on PR #670: Reject executing third-party extensions via in-process Go plugins* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cli_cli_adr_docs_rfc_004-termenv-formatting_md`** (`cli/cli`): *RFC 004: Terminal Color and Hyperlink Detection via termenv* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cli_cli_proposed_620`** (`cli/cli`): *Proposed Candidate Decision for Issue #620: Broken ANSI escape sequences when piping gh output to jq and grep* — System decision extracted from repository history does not match any evaluated ground-truth question
- **`dec_cli_cli_github_pr_735`** (`cli/cli`): *Decision in PR #735: Auto-detect TTY and disable ANSI formatting in non-interact* — System decision extracted from repository history does not match any evaluated ground-truth question
- *... and 37 more unlinked decisions*

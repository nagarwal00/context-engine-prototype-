# Baseline D: GitHub Copilot Manual Evaluation Trial Sheet

> **Protocol:** This sheet defines the manual trial protocol for evaluating GitHub Copilot on WhyBench-Synth (`test_v2`).
> Each trial provides the repository's recorded event stream and an architectural question to GitHub Copilot.
> Results are recorded in `backend/evaluation/manual_copilot_results.csv` with binary flags (`1` or `0`).

## Evaluation Protocol & Scoring Instructions

1. Open GitHub Copilot Chat (VS Code or github.com).
2. Copy the **Prompt** and **Event Stream** for each trial below into Copilot.
3. Evaluate Copilot's response against the ground truth criteria:
   - **`answer_correct`**: `1` if Copilot correctly identifies the decision state and rationale (for positive questions) or correctly states that no such decision was made (for negative questions); `0` otherwise.
   - **`answer_has_invented_reason`**: `1` if Copilot invents facts, rationales, benchmarks, or citations not grounded in the provided event stream; `0` otherwise.
   - **`cited_real_source`**: `1` if Copilot specifically and accurately cites an event ID, PR, issue, or ADR from the event stream; `0` otherwise.
4. Append the result to `backend/evaluation/manual_copilot_results.csv`.

## Summary of Trial Questions

- **Dataset Split:** `test_v2`
- **Total Trials:** 36 (26 positive questions + 10 sampled negative questions)
- **Negative Sampling Random Seed:** `1234`

| # | Question ID | Repository | Type | Expected State | Question Summary |
|---|---|---|---|---|---|
| 1 | `WB_PAY_09` | `acme-ecommerce/payment-core` | Positive (Decision) | `accepted` | How were double charges prevented when users double-clicked the checko... |
| 2 | `WB_PAY_10` | `acme-ecommerce/payment-core` | Positive (Decision) | `rejected` | Why were database row locks rejected for enforcing checkout idempotenc... |
| 3 | `WB_PAY_11` | `acme-ecommerce/payment-core` | Positive (Decision) | `accepted` | How does payment-core authenticate incoming Stripe webhooks?... |
| 4 | `WB_PAY_12` | `acme-ecommerce/payment-core` | Positive (Decision) | `rejected` | Why was skipping webhook signature verification in development rejecte... |
| 5 | `WB_PAY_13` | `acme-ecommerce/payment-core` | Positive (Decision) | `accepted` | How did payment-core implement support for customer partial refunds?... |
| 6 | `WB_PAY_14` | `acme-ecommerce/payment-core` | Positive (Decision) | `accepted` | How were fractional cent rounding errors solved in multi-currency refu... |
| 7 | `WB_PAY_15` | `acme-ecommerce/payment-core` | Positive (Decision) | `rejected` | Why were client-supplied timestamps rejected for partial refund reques... |
| 8 | `WB_PAY_16` | `acme-ecommerce/payment-core` | Positive (Decision) | `accepted` | How does payment-core handle toxic malformed webhook messages that cra... |
| 9 | `WB_PAY_17` | `acme-ecommerce/payment-core` | Positive (Decision) | `accepted` | How does payment-core achieve PCI SAQ A compliance for credit card pro... |
| 10 | `WB_PAY_18` | `acme-ecommerce/payment-core` | Positive (Decision) | `rejected` | Why was in-memory caching of card CVV security codes rejected?... |
| 11 | `WB_CH_09` | `cloud-hypervisor/cloud-hypervisor` | Positive (Decision) | `rejected` | Why was legacy floppy and IDE drive emulation rejected?... |
| 12 | `WB_CH_10` | `cloud-hypervisor/cloud-hypervisor` | Positive (Decision) | `accepted` | How does virtio-fs avoid memory duplication when sharing container roo... |
| 13 | `WB_CH_11` | `cloud-hypervisor/cloud-hypervisor` | Positive (Decision) | `accepted` | How does Cloud Hypervisor support dynamic hotplug of PCIe devices?... |
| 14 | `WB_CH_12` | `cloud-hypervisor/cloud-hypervisor` | Positive (Decision) | `accepted` | Why did Cloud Hypervisor adopt Linux io_uring for disk virtualization?... |
| 15 | `WB_CH_13` | `cloud-hypervisor/cloud-hypervisor` | Positive (Decision) | `rejected` | Why were spin-polling loops prohibited in io_uring worker threads?... |
| 16 | `WB_CH_14` | `cloud-hypervisor/cloud-hypervisor` | Positive (Decision) | `accepted` | How does Cloud Hypervisor provide direct GPU access to guest virtual m... |
| 17 | `WB_CH_15` | `cloud-hypervisor/cloud-hypervisor` | Positive (Decision) | `accepted` | Why did Cloud Hypervisor adopt the ACPI Generic Event Device (GED)?... |
| 18 | `WB_CH_16` | `cloud-hypervisor/cloud-hypervisor` | Positive (Decision) | `accepted` | How does the microVM profile achieve 12ms cold boot for serverless san... |
| 19 | `WB_CLI_09` | `cli/cli` | Positive (Decision) | `rejected` | Why was executing extensions via Go dynamic plugin packages rejected?... |
| 20 | `WB_CLI_10` | `cli/cli` | Positive (Decision) | `accepted` | How does GitHub CLI isolate extension subprocess execution environment... |
| 21 | `WB_CLI_11` | `cli/cli` | Positive (Decision) | `accepted` | Why did GitHub CLI adopt termenv for terminal formatting?... |
| 22 | `WB_CLI_12` | `cli/cli` | Positive (Decision) | `accepted` | How was ANSI escape sequence corruption resolved in Unix pipelines?... |
| 23 | `WB_CLI_13` | `cli/cli` | Positive (Decision) | `accepted` | How does GitHub CLI share credentials with standard Git CLI operations... |
| 24 | `WB_CLI_14` | `cli/cli` | Positive (Decision) | `accepted` | How is git credential helper configured during authentication?... |
| 25 | `WB_CLI_15` | `cli/cli` | Positive (Decision) | `rejected` | Why was passing authentication tokens via URL query parameters rejecte... |
| 26 | `WB_CLI_16` | `cli/cli` | Positive (Decision) | `accepted` | How does gh auth login authenticate in headless SSH cloud environments... |
| 27 | `WB_CH_TEST_NEG_14` | `cloud-hypervisor/cloud-hypervisor` | Negative (Unrecorded) | `none` | Did bot automated benchmark comments on PR #1042 decide to enforce 1GB... |
| 28 | `WB_PAY_TEST_NEG_08` | `acme-ecommerce/payment-core` | Negative (Unrecorded) | `none` | Did PR #18 review comments decide to adopt Memcached alongside Redis f... |
| 29 | `WB_PAY_TEST_NEG_01` | `acme-ecommerce/payment-core` | Negative (Unrecorded) | `none` | Why did payment-core switch from JSON REST APIs to XML SOAP for paymen... |
| 30 | `WB_PAY_TEST_NEG_06` | `acme-ecommerce/payment-core` | Negative (Unrecorded) | `none` | Why did payment-core replace JWT token authentication with Basic HTTP ... |
| 31 | `WB_CLI_TEST_NEG_08` | `cli/cli` | Negative (Unrecorded) | `none` | Did issue #412 discussions decide to adopt GnuPG pass password manager... |
| 32 | `WB_PAY_TEST_NEG_03` | `acme-ecommerce/payment-core` | Negative (Unrecorded) | `none` | Why was Apache Cassandra chosen over PostgreSQL for payment database p... |
| 33 | `WB_CLI_TEST_NEG_12` | `cli/cli` | Negative (Unrecorded) | `none` | Was Bubble Tea TUI framework adopted for rendering terminal output in ... |
| 34 | `WB_PAY_TEST_NEG_07` | `acme-ecommerce/payment-core` | Negative (Unrecorded) | `none` | Why was CouchDB adopted for storing customer multi-currency wallet bal... |
| 35 | `WB_CH_TEST_NEG_08` | `cloud-hypervisor/cloud-hypervisor` | Negative (Unrecorded) | `none` | Did issue #890 discussions decide to adopt ZFS pool storage for guest ... |
| 36 | `WB_CH_TEST_NEG_01` | `cloud-hypervisor/cloud-hypervisor` | Negative (Unrecorded) | `none` | Why did Cloud Hypervisor embed a proprietary binary NVIDIA kernel driv... |

---

## CSV Results Template

Copy and paste the header and question rows below into `backend/evaluation/manual_copilot_results.csv` when conducting the trials:

```csv
question_id,answer_correct,answer_has_invented_reason,cited_real_source,notes
WB_PAY_09,,,,
WB_PAY_10,,,,
WB_PAY_11,,,,
WB_PAY_12,,,,
WB_PAY_13,,,,
WB_PAY_14,,,,
WB_PAY_15,,,,
WB_PAY_16,,,,
WB_PAY_17,,,,
WB_PAY_18,,,,
WB_CH_09,,,,
WB_CH_10,,,,
WB_CH_11,,,,
WB_CH_12,,,,
WB_CH_13,,,,
WB_CH_14,,,,
WB_CH_15,,,,
WB_CH_16,,,,
WB_CLI_09,,,,
WB_CLI_10,,,,
WB_CLI_11,,,,
WB_CLI_12,,,,
WB_CLI_13,,,,
WB_CLI_14,,,,
WB_CLI_15,,,,
WB_CLI_16,,,,
WB_CH_TEST_NEG_14,,,,
WB_PAY_TEST_NEG_08,,,,
WB_PAY_TEST_NEG_01,,,,
WB_PAY_TEST_NEG_06,,,,
WB_CLI_TEST_NEG_08,,,,
WB_PAY_TEST_NEG_03,,,,
WB_CLI_TEST_NEG_12,,,,
WB_PAY_TEST_NEG_07,,,,
WB_CH_TEST_NEG_08,,,,
WB_CH_TEST_NEG_01,,,,
```

---

## Detailed Trial Prompts

### Trial 1: Question `WB_PAY_09`

- **Repository:** `acme-ecommerce/payment-core`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_pay_pr_18, evt_why_pay_issue_05`
- **Ground Truth Summary:** Idempotency-Key HTTP middleware hashing request payloads with SHA-256 and returning cached responses on hit.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'acme-ecommerce/payment-core'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: How were double charges prevented when users double-clicked the checkout submit button?

Event Stream:
[evt_why_pay_adr_01] (adr:docs/adr/0001-stripe-payment-migration.md) ADR 0001: Migrate from Legacy Braintree to Stripe Payment Intents API: Status: accepted

Context:
Legacy Braintree integration does not support European 3D Secure 2 authentication and suffers from elevated drop-off during checkout.

Decision:
Migrate checkout payment processing to Stripe Payment Intents with asynchronous webhook settlement.

Consequences:
- Full 3DS2 compliance.
- Checkout authorization latency reduced to <800ms.
- Requires webhook listener for async
[evt_why_pay_issue_08] (github_issue:8) Issue #8: Stripe API 429 Rate Limits encountered during flash sale traffic: During peak traffic burst, worker threads made simultaneous calls to Stripe charges API exceeding the 100 req/sec rate limit without jittered exponential backoff.
[evt_why_pay_pr_14] (github_pr:14) PR #14: Implement Exponential Backoff with Full Jitter for Stripe API (Closes #8): Adds decorator with decorator-level exponential backoff with full jitter (Decorrelated Jitter algorithm). Retries up to 4 times before failing.
[evt_why_pay_rev_c301] (pr_review_comment:c301) Review on PR #14: Reject fixed interval retries: Fixed 500ms sleep will create thundering herd when Stripe recovers. We must reject fixed sleep in favor of exponential backoff with randomized full jitter.
[evt_why_pay_adr_02] (adr:docs/adr/0002-webhook-idempotency.md) ADR 0002: Use Redis Distributed Lock and Idempotency Key for Webhooks: Status: accepted

Context:
Stripe webhook delivery guarantees at-least-once delivery. Duplicate payment.succeeded events caused double order fulfillment.

Decision:
Store processed Stripe event_ids in Redis with a 24-hour TTL and acquire a distributed mutex lock before processing webhook payloads.

Consequences:
- Zero duplicate order fulfillments.
- Redis availability required for payment reconci
[evt_why_pay_commit_7a] (git_commit:7a8b9c0d1e2f3a4b) feat(database): migrate to SQLAlchemy async connection pool with PgBouncer: Replaces raw psycopg2 connection per request with async connection pool. Reduces connection pool exhaustion under 2,000 checkout req/sec.
[evt_why_pay_issue_05] (github_issue:5) Issue #5: Duplicate customer charges under concurrent checkout clicks: Impatient users double clicking Pay Now sent parallel requests to /checkout initiating two distinct payment authorization transactions.
[evt_why_pay_pr_18] (github_pr:18) PR #18: Idempotency-Key Header Middleware with SHA-256 Request Hashing (Closes #5): Introduces Idempotency-Key HTTP header middleware computing SHA-256 digest of payload. Cache hit returns cached HTTP response immediately.
[evt_why_pay_rev_c402] (pr_review_comment:c402) Review on PR #18: Reject database-level transaction locks for idempotency: Using row-level database locks (SELECT FOR UPDATE) on the checkout table creates bottleneck deadlock risks during sales. Redis key-value atomicity is required.
[evt_why_pay_adr_03] (adr:docs/adr/0003-webhook-first-confirmation.md) ADR 0003: Webhook-First Asynchronous Order Confirmation: Status: accepted

Context:
Sync browser checkout redirect was dropping orders when mobile users closed Safari before the success return page loaded.

Decision:
Treat Stripe payment_intent.succeeded webhook event as the single source of truth for confirming orders rather than client-side redirects.

Consequences:
- Zero lost orders from closed tabs.
- Frontend displays pending state and listens via
[evt_why_pay_pr_22] (github_pr:22) PR #22: Webhook signature verification with HMAC-SHA256 and replay tolerance: Validates Stripe-Signature header with HMAC-SHA256 secret key and enforces a 300-second maximum timestamp drift window to prevent replay attacks.
[evt_why_pay_rev_c450] (pr_review_comment:c450) Review on PR #22: Reject skipping signature verification in development: Bypassing webhook signature checks via a debug flag risks shipping unverified endpoints to production. Verification must run in all environments with test keys.
[evt_why_pay_adr_04] (adr:docs/adr/0004-partial-refund-support.md) ADR 0004: Support Partial Refunds with Line-Item Reversal Ledger: Status: accepted

Context:
Customers returning one item out of a multi-item purchase required customer support intervention because the system only supported full-order voiding.

Decision:
Implement immutable append-only line-item reversal records tracking fractional refunds against order authorization totals.

Consequences:
- Eliminates manual support overrides for returns.
- Prevents cumulative 
[evt_why_pay_issue_11] (github_issue:11) Issue #11: Floating point rounding discrepancies during multi-currency partial refunds: Using standard IEEE 754 float types caused a 1-cent mismatch ($19.99 vs $19.989999) between partial refund sum and total charge.
[evt_why_pay_pr_29] (github_pr:29) PR #29: Migrate refund math to integer cents and Decimal representation (Closes #11): Converts all monetary fields to 64-bit integer minor currency units (cents) and Python Decimal to prevent floating point inaccuracies.
[evt_why_pay_rev_c505] (pr_review_comment:c505) Review on PR #29: Reject client-supplied refund timestamps: Relying on client timestamps allows fraudulent out-of-order refund attempts. Timestamps must strictly be generated by server UTC monotonic clock.
[evt_why_pay_issue_19] (github_issue:19) Issue #19: Toxic malformed webhook payloads causing infinite queue retry loops: Unparseable webhook payload triggered an unhandled exception causing RabbitMQ consumer to continually NACK and requeue, stalling normal processing.
[evt_why_pay_pr_35] (github_pr:35) PR #35: Route unparseable webhook messages to Dead Letter Queue after 3 failed deliveries (Closes #19): Configures DLQ with max-retries=3. Stalls are avoided by parking invalid messages for engineer inspection without blocking main line.
[evt_why_pay_adr_05] (adr:docs/adr/0005-pci-token-vault.md) ADR 0005: Dual-token vault encryption for PCI-DSS compliance: Status: accepted

Context:
PCI-DSS Scope Level 1 audit requires payment card numbers to never enter merchant application server memory or disk storage.

Decision:
Use Stripe Elements tokenization directly in client browser, receiving only opaque payment_method_id tokens on payment-core backend.

Consequences:
- Achieves PCI SAQ A eligibility, drastically reducing compliance overhead.
- Eliminates 
[evt_why_pay_rev_c610] (pr_review_comment:c610) Review on PR #38: Reject caching unencrypted CVV in memory: Storing raw CVVs even temporarily in Redis or local process memory is a direct violation of PCI-DSS requirement 3.2. Prohibit all CVV persistence.
```

---

### Trial 2: Question `WB_PAY_10`

- **Repository:** `acme-ecommerce/payment-core`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `rejected`
- **Expected Evidence Events:** `evt_why_pay_rev_c402`
- **Ground Truth Summary:** Database row locks cause connection saturation and deadlock risks under high checkout volume.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'acme-ecommerce/payment-core'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Why were database row locks rejected for enforcing checkout idempotency?

Event Stream:
[evt_why_pay_adr_01] (adr:docs/adr/0001-stripe-payment-migration.md) ADR 0001: Migrate from Legacy Braintree to Stripe Payment Intents API: Status: accepted

Context:
Legacy Braintree integration does not support European 3D Secure 2 authentication and suffers from elevated drop-off during checkout.

Decision:
Migrate checkout payment processing to Stripe Payment Intents with asynchronous webhook settlement.

Consequences:
- Full 3DS2 compliance.
- Checkout authorization latency reduced to <800ms.
- Requires webhook listener for async
[evt_why_pay_issue_08] (github_issue:8) Issue #8: Stripe API 429 Rate Limits encountered during flash sale traffic: During peak traffic burst, worker threads made simultaneous calls to Stripe charges API exceeding the 100 req/sec rate limit without jittered exponential backoff.
[evt_why_pay_pr_14] (github_pr:14) PR #14: Implement Exponential Backoff with Full Jitter for Stripe API (Closes #8): Adds decorator with decorator-level exponential backoff with full jitter (Decorrelated Jitter algorithm). Retries up to 4 times before failing.
[evt_why_pay_rev_c301] (pr_review_comment:c301) Review on PR #14: Reject fixed interval retries: Fixed 500ms sleep will create thundering herd when Stripe recovers. We must reject fixed sleep in favor of exponential backoff with randomized full jitter.
[evt_why_pay_adr_02] (adr:docs/adr/0002-webhook-idempotency.md) ADR 0002: Use Redis Distributed Lock and Idempotency Key for Webhooks: Status: accepted

Context:
Stripe webhook delivery guarantees at-least-once delivery. Duplicate payment.succeeded events caused double order fulfillment.

Decision:
Store processed Stripe event_ids in Redis with a 24-hour TTL and acquire a distributed mutex lock before processing webhook payloads.

Consequences:
- Zero duplicate order fulfillments.
- Redis availability required for payment reconci
[evt_why_pay_commit_7a] (git_commit:7a8b9c0d1e2f3a4b) feat(database): migrate to SQLAlchemy async connection pool with PgBouncer: Replaces raw psycopg2 connection per request with async connection pool. Reduces connection pool exhaustion under 2,000 checkout req/sec.
[evt_why_pay_issue_05] (github_issue:5) Issue #5: Duplicate customer charges under concurrent checkout clicks: Impatient users double clicking Pay Now sent parallel requests to /checkout initiating two distinct payment authorization transactions.
[evt_why_pay_pr_18] (github_pr:18) PR #18: Idempotency-Key Header Middleware with SHA-256 Request Hashing (Closes #5): Introduces Idempotency-Key HTTP header middleware computing SHA-256 digest of payload. Cache hit returns cached HTTP response immediately.
[evt_why_pay_rev_c402] (pr_review_comment:c402) Review on PR #18: Reject database-level transaction locks for idempotency: Using row-level database locks (SELECT FOR UPDATE) on the checkout table creates bottleneck deadlock risks during sales. Redis key-value atomicity is required.
[evt_why_pay_adr_03] (adr:docs/adr/0003-webhook-first-confirmation.md) ADR 0003: Webhook-First Asynchronous Order Confirmation: Status: accepted

Context:
Sync browser checkout redirect was dropping orders when mobile users closed Safari before the success return page loaded.

Decision:
Treat Stripe payment_intent.succeeded webhook event as the single source of truth for confirming orders rather than client-side redirects.

Consequences:
- Zero lost orders from closed tabs.
- Frontend displays pending state and listens via
[evt_why_pay_pr_22] (github_pr:22) PR #22: Webhook signature verification with HMAC-SHA256 and replay tolerance: Validates Stripe-Signature header with HMAC-SHA256 secret key and enforces a 300-second maximum timestamp drift window to prevent replay attacks.
[evt_why_pay_rev_c450] (pr_review_comment:c450) Review on PR #22: Reject skipping signature verification in development: Bypassing webhook signature checks via a debug flag risks shipping unverified endpoints to production. Verification must run in all environments with test keys.
[evt_why_pay_adr_04] (adr:docs/adr/0004-partial-refund-support.md) ADR 0004: Support Partial Refunds with Line-Item Reversal Ledger: Status: accepted

Context:
Customers returning one item out of a multi-item purchase required customer support intervention because the system only supported full-order voiding.

Decision:
Implement immutable append-only line-item reversal records tracking fractional refunds against order authorization totals.

Consequences:
- Eliminates manual support overrides for returns.
- Prevents cumulative 
[evt_why_pay_issue_11] (github_issue:11) Issue #11: Floating point rounding discrepancies during multi-currency partial refunds: Using standard IEEE 754 float types caused a 1-cent mismatch ($19.99 vs $19.989999) between partial refund sum and total charge.
[evt_why_pay_pr_29] (github_pr:29) PR #29: Migrate refund math to integer cents and Decimal representation (Closes #11): Converts all monetary fields to 64-bit integer minor currency units (cents) and Python Decimal to prevent floating point inaccuracies.
[evt_why_pay_rev_c505] (pr_review_comment:c505) Review on PR #29: Reject client-supplied refund timestamps: Relying on client timestamps allows fraudulent out-of-order refund attempts. Timestamps must strictly be generated by server UTC monotonic clock.
[evt_why_pay_issue_19] (github_issue:19) Issue #19: Toxic malformed webhook payloads causing infinite queue retry loops: Unparseable webhook payload triggered an unhandled exception causing RabbitMQ consumer to continually NACK and requeue, stalling normal processing.
[evt_why_pay_pr_35] (github_pr:35) PR #35: Route unparseable webhook messages to Dead Letter Queue after 3 failed deliveries (Closes #19): Configures DLQ with max-retries=3. Stalls are avoided by parking invalid messages for engineer inspection without blocking main line.
[evt_why_pay_adr_05] (adr:docs/adr/0005-pci-token-vault.md) ADR 0005: Dual-token vault encryption for PCI-DSS compliance: Status: accepted

Context:
PCI-DSS Scope Level 1 audit requires payment card numbers to never enter merchant application server memory or disk storage.

Decision:
Use Stripe Elements tokenization directly in client browser, receiving only opaque payment_method_id tokens on payment-core backend.

Consequences:
- Achieves PCI SAQ A eligibility, drastically reducing compliance overhead.
- Eliminates 
[evt_why_pay_rev_c610] (pr_review_comment:c610) Review on PR #38: Reject caching unencrypted CVV in memory: Storing raw CVVs even temporarily in Redis or local process memory is a direct violation of PCI-DSS requirement 3.2. Prohibit all CVV persistence.
```

---

### Trial 3: Question `WB_PAY_11`

- **Repository:** `acme-ecommerce/payment-core`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_pay_pr_22`
- **Ground Truth Summary:** Validates HMAC-SHA256 signature against secret with a 300-second maximum timestamp drift tolerance window.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'acme-ecommerce/payment-core'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: How does payment-core authenticate incoming Stripe webhooks?

Event Stream:
[evt_why_pay_adr_01] (adr:docs/adr/0001-stripe-payment-migration.md) ADR 0001: Migrate from Legacy Braintree to Stripe Payment Intents API: Status: accepted

Context:
Legacy Braintree integration does not support European 3D Secure 2 authentication and suffers from elevated drop-off during checkout.

Decision:
Migrate checkout payment processing to Stripe Payment Intents with asynchronous webhook settlement.

Consequences:
- Full 3DS2 compliance.
- Checkout authorization latency reduced to <800ms.
- Requires webhook listener for async
[evt_why_pay_issue_08] (github_issue:8) Issue #8: Stripe API 429 Rate Limits encountered during flash sale traffic: During peak traffic burst, worker threads made simultaneous calls to Stripe charges API exceeding the 100 req/sec rate limit without jittered exponential backoff.
[evt_why_pay_pr_14] (github_pr:14) PR #14: Implement Exponential Backoff with Full Jitter for Stripe API (Closes #8): Adds decorator with decorator-level exponential backoff with full jitter (Decorrelated Jitter algorithm). Retries up to 4 times before failing.
[evt_why_pay_rev_c301] (pr_review_comment:c301) Review on PR #14: Reject fixed interval retries: Fixed 500ms sleep will create thundering herd when Stripe recovers. We must reject fixed sleep in favor of exponential backoff with randomized full jitter.
[evt_why_pay_adr_02] (adr:docs/adr/0002-webhook-idempotency.md) ADR 0002: Use Redis Distributed Lock and Idempotency Key for Webhooks: Status: accepted

Context:
Stripe webhook delivery guarantees at-least-once delivery. Duplicate payment.succeeded events caused double order fulfillment.

Decision:
Store processed Stripe event_ids in Redis with a 24-hour TTL and acquire a distributed mutex lock before processing webhook payloads.

Consequences:
- Zero duplicate order fulfillments.
- Redis availability required for payment reconci
[evt_why_pay_commit_7a] (git_commit:7a8b9c0d1e2f3a4b) feat(database): migrate to SQLAlchemy async connection pool with PgBouncer: Replaces raw psycopg2 connection per request with async connection pool. Reduces connection pool exhaustion under 2,000 checkout req/sec.
[evt_why_pay_issue_05] (github_issue:5) Issue #5: Duplicate customer charges under concurrent checkout clicks: Impatient users double clicking Pay Now sent parallel requests to /checkout initiating two distinct payment authorization transactions.
[evt_why_pay_pr_18] (github_pr:18) PR #18: Idempotency-Key Header Middleware with SHA-256 Request Hashing (Closes #5): Introduces Idempotency-Key HTTP header middleware computing SHA-256 digest of payload. Cache hit returns cached HTTP response immediately.
[evt_why_pay_rev_c402] (pr_review_comment:c402) Review on PR #18: Reject database-level transaction locks for idempotency: Using row-level database locks (SELECT FOR UPDATE) on the checkout table creates bottleneck deadlock risks during sales. Redis key-value atomicity is required.
[evt_why_pay_adr_03] (adr:docs/adr/0003-webhook-first-confirmation.md) ADR 0003: Webhook-First Asynchronous Order Confirmation: Status: accepted

Context:
Sync browser checkout redirect was dropping orders when mobile users closed Safari before the success return page loaded.

Decision:
Treat Stripe payment_intent.succeeded webhook event as the single source of truth for confirming orders rather than client-side redirects.

Consequences:
- Zero lost orders from closed tabs.
- Frontend displays pending state and listens via
[evt_why_pay_pr_22] (github_pr:22) PR #22: Webhook signature verification with HMAC-SHA256 and replay tolerance: Validates Stripe-Signature header with HMAC-SHA256 secret key and enforces a 300-second maximum timestamp drift window to prevent replay attacks.
[evt_why_pay_rev_c450] (pr_review_comment:c450) Review on PR #22: Reject skipping signature verification in development: Bypassing webhook signature checks via a debug flag risks shipping unverified endpoints to production. Verification must run in all environments with test keys.
[evt_why_pay_adr_04] (adr:docs/adr/0004-partial-refund-support.md) ADR 0004: Support Partial Refunds with Line-Item Reversal Ledger: Status: accepted

Context:
Customers returning one item out of a multi-item purchase required customer support intervention because the system only supported full-order voiding.

Decision:
Implement immutable append-only line-item reversal records tracking fractional refunds against order authorization totals.

Consequences:
- Eliminates manual support overrides for returns.
- Prevents cumulative 
[evt_why_pay_issue_11] (github_issue:11) Issue #11: Floating point rounding discrepancies during multi-currency partial refunds: Using standard IEEE 754 float types caused a 1-cent mismatch ($19.99 vs $19.989999) between partial refund sum and total charge.
[evt_why_pay_pr_29] (github_pr:29) PR #29: Migrate refund math to integer cents and Decimal representation (Closes #11): Converts all monetary fields to 64-bit integer minor currency units (cents) and Python Decimal to prevent floating point inaccuracies.
[evt_why_pay_rev_c505] (pr_review_comment:c505) Review on PR #29: Reject client-supplied refund timestamps: Relying on client timestamps allows fraudulent out-of-order refund attempts. Timestamps must strictly be generated by server UTC monotonic clock.
[evt_why_pay_issue_19] (github_issue:19) Issue #19: Toxic malformed webhook payloads causing infinite queue retry loops: Unparseable webhook payload triggered an unhandled exception causing RabbitMQ consumer to continually NACK and requeue, stalling normal processing.
[evt_why_pay_pr_35] (github_pr:35) PR #35: Route unparseable webhook messages to Dead Letter Queue after 3 failed deliveries (Closes #19): Configures DLQ with max-retries=3. Stalls are avoided by parking invalid messages for engineer inspection without blocking main line.
[evt_why_pay_adr_05] (adr:docs/adr/0005-pci-token-vault.md) ADR 0005: Dual-token vault encryption for PCI-DSS compliance: Status: accepted

Context:
PCI-DSS Scope Level 1 audit requires payment card numbers to never enter merchant application server memory or disk storage.

Decision:
Use Stripe Elements tokenization directly in client browser, receiving only opaque payment_method_id tokens on payment-core backend.

Consequences:
- Achieves PCI SAQ A eligibility, drastically reducing compliance overhead.
- Eliminates 
[evt_why_pay_rev_c610] (pr_review_comment:c610) Review on PR #38: Reject caching unencrypted CVV in memory: Storing raw CVVs even temporarily in Redis or local process memory is a direct violation of PCI-DSS requirement 3.2. Prohibit all CVV persistence.
```

---

### Trial 4: Question `WB_PAY_12`

- **Repository:** `acme-ecommerce/payment-core`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `rejected`
- **Expected Evidence Events:** `evt_why_pay_rev_c450`
- **Ground Truth Summary:** Bypassing signature validation risks shipping unverified endpoints to production.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'acme-ecommerce/payment-core'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Why was skipping webhook signature verification in development rejected?

Event Stream:
[evt_why_pay_adr_01] (adr:docs/adr/0001-stripe-payment-migration.md) ADR 0001: Migrate from Legacy Braintree to Stripe Payment Intents API: Status: accepted

Context:
Legacy Braintree integration does not support European 3D Secure 2 authentication and suffers from elevated drop-off during checkout.

Decision:
Migrate checkout payment processing to Stripe Payment Intents with asynchronous webhook settlement.

Consequences:
- Full 3DS2 compliance.
- Checkout authorization latency reduced to <800ms.
- Requires webhook listener for async
[evt_why_pay_issue_08] (github_issue:8) Issue #8: Stripe API 429 Rate Limits encountered during flash sale traffic: During peak traffic burst, worker threads made simultaneous calls to Stripe charges API exceeding the 100 req/sec rate limit without jittered exponential backoff.
[evt_why_pay_pr_14] (github_pr:14) PR #14: Implement Exponential Backoff with Full Jitter for Stripe API (Closes #8): Adds decorator with decorator-level exponential backoff with full jitter (Decorrelated Jitter algorithm). Retries up to 4 times before failing.
[evt_why_pay_rev_c301] (pr_review_comment:c301) Review on PR #14: Reject fixed interval retries: Fixed 500ms sleep will create thundering herd when Stripe recovers. We must reject fixed sleep in favor of exponential backoff with randomized full jitter.
[evt_why_pay_adr_02] (adr:docs/adr/0002-webhook-idempotency.md) ADR 0002: Use Redis Distributed Lock and Idempotency Key for Webhooks: Status: accepted

Context:
Stripe webhook delivery guarantees at-least-once delivery. Duplicate payment.succeeded events caused double order fulfillment.

Decision:
Store processed Stripe event_ids in Redis with a 24-hour TTL and acquire a distributed mutex lock before processing webhook payloads.

Consequences:
- Zero duplicate order fulfillments.
- Redis availability required for payment reconci
[evt_why_pay_commit_7a] (git_commit:7a8b9c0d1e2f3a4b) feat(database): migrate to SQLAlchemy async connection pool with PgBouncer: Replaces raw psycopg2 connection per request with async connection pool. Reduces connection pool exhaustion under 2,000 checkout req/sec.
[evt_why_pay_issue_05] (github_issue:5) Issue #5: Duplicate customer charges under concurrent checkout clicks: Impatient users double clicking Pay Now sent parallel requests to /checkout initiating two distinct payment authorization transactions.
[evt_why_pay_pr_18] (github_pr:18) PR #18: Idempotency-Key Header Middleware with SHA-256 Request Hashing (Closes #5): Introduces Idempotency-Key HTTP header middleware computing SHA-256 digest of payload. Cache hit returns cached HTTP response immediately.
[evt_why_pay_rev_c402] (pr_review_comment:c402) Review on PR #18: Reject database-level transaction locks for idempotency: Using row-level database locks (SELECT FOR UPDATE) on the checkout table creates bottleneck deadlock risks during sales. Redis key-value atomicity is required.
[evt_why_pay_adr_03] (adr:docs/adr/0003-webhook-first-confirmation.md) ADR 0003: Webhook-First Asynchronous Order Confirmation: Status: accepted

Context:
Sync browser checkout redirect was dropping orders when mobile users closed Safari before the success return page loaded.

Decision:
Treat Stripe payment_intent.succeeded webhook event as the single source of truth for confirming orders rather than client-side redirects.

Consequences:
- Zero lost orders from closed tabs.
- Frontend displays pending state and listens via
[evt_why_pay_pr_22] (github_pr:22) PR #22: Webhook signature verification with HMAC-SHA256 and replay tolerance: Validates Stripe-Signature header with HMAC-SHA256 secret key and enforces a 300-second maximum timestamp drift window to prevent replay attacks.
[evt_why_pay_rev_c450] (pr_review_comment:c450) Review on PR #22: Reject skipping signature verification in development: Bypassing webhook signature checks via a debug flag risks shipping unverified endpoints to production. Verification must run in all environments with test keys.
[evt_why_pay_adr_04] (adr:docs/adr/0004-partial-refund-support.md) ADR 0004: Support Partial Refunds with Line-Item Reversal Ledger: Status: accepted

Context:
Customers returning one item out of a multi-item purchase required customer support intervention because the system only supported full-order voiding.

Decision:
Implement immutable append-only line-item reversal records tracking fractional refunds against order authorization totals.

Consequences:
- Eliminates manual support overrides for returns.
- Prevents cumulative 
[evt_why_pay_issue_11] (github_issue:11) Issue #11: Floating point rounding discrepancies during multi-currency partial refunds: Using standard IEEE 754 float types caused a 1-cent mismatch ($19.99 vs $19.989999) between partial refund sum and total charge.
[evt_why_pay_pr_29] (github_pr:29) PR #29: Migrate refund math to integer cents and Decimal representation (Closes #11): Converts all monetary fields to 64-bit integer minor currency units (cents) and Python Decimal to prevent floating point inaccuracies.
[evt_why_pay_rev_c505] (pr_review_comment:c505) Review on PR #29: Reject client-supplied refund timestamps: Relying on client timestamps allows fraudulent out-of-order refund attempts. Timestamps must strictly be generated by server UTC monotonic clock.
[evt_why_pay_issue_19] (github_issue:19) Issue #19: Toxic malformed webhook payloads causing infinite queue retry loops: Unparseable webhook payload triggered an unhandled exception causing RabbitMQ consumer to continually NACK and requeue, stalling normal processing.
[evt_why_pay_pr_35] (github_pr:35) PR #35: Route unparseable webhook messages to Dead Letter Queue after 3 failed deliveries (Closes #19): Configures DLQ with max-retries=3. Stalls are avoided by parking invalid messages for engineer inspection without blocking main line.
[evt_why_pay_adr_05] (adr:docs/adr/0005-pci-token-vault.md) ADR 0005: Dual-token vault encryption for PCI-DSS compliance: Status: accepted

Context:
PCI-DSS Scope Level 1 audit requires payment card numbers to never enter merchant application server memory or disk storage.

Decision:
Use Stripe Elements tokenization directly in client browser, receiving only opaque payment_method_id tokens on payment-core backend.

Consequences:
- Achieves PCI SAQ A eligibility, drastically reducing compliance overhead.
- Eliminates 
[evt_why_pay_rev_c610] (pr_review_comment:c610) Review on PR #38: Reject caching unencrypted CVV in memory: Storing raw CVVs even temporarily in Redis or local process memory is a direct violation of PCI-DSS requirement 3.2. Prohibit all CVV persistence.
```

---

### Trial 5: Question `WB_PAY_13`

- **Repository:** `acme-ecommerce/payment-core`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_pay_adr_04`
- **Ground Truth Summary:** Introduced immutable append-only line-item reversal records tracking fractional refunds against order authorization totals.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'acme-ecommerce/payment-core'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: How did payment-core implement support for customer partial refunds?

Event Stream:
[evt_why_pay_adr_01] (adr:docs/adr/0001-stripe-payment-migration.md) ADR 0001: Migrate from Legacy Braintree to Stripe Payment Intents API: Status: accepted

Context:
Legacy Braintree integration does not support European 3D Secure 2 authentication and suffers from elevated drop-off during checkout.

Decision:
Migrate checkout payment processing to Stripe Payment Intents with asynchronous webhook settlement.

Consequences:
- Full 3DS2 compliance.
- Checkout authorization latency reduced to <800ms.
- Requires webhook listener for async
[evt_why_pay_issue_08] (github_issue:8) Issue #8: Stripe API 429 Rate Limits encountered during flash sale traffic: During peak traffic burst, worker threads made simultaneous calls to Stripe charges API exceeding the 100 req/sec rate limit without jittered exponential backoff.
[evt_why_pay_pr_14] (github_pr:14) PR #14: Implement Exponential Backoff with Full Jitter for Stripe API (Closes #8): Adds decorator with decorator-level exponential backoff with full jitter (Decorrelated Jitter algorithm). Retries up to 4 times before failing.
[evt_why_pay_rev_c301] (pr_review_comment:c301) Review on PR #14: Reject fixed interval retries: Fixed 500ms sleep will create thundering herd when Stripe recovers. We must reject fixed sleep in favor of exponential backoff with randomized full jitter.
[evt_why_pay_adr_02] (adr:docs/adr/0002-webhook-idempotency.md) ADR 0002: Use Redis Distributed Lock and Idempotency Key for Webhooks: Status: accepted

Context:
Stripe webhook delivery guarantees at-least-once delivery. Duplicate payment.succeeded events caused double order fulfillment.

Decision:
Store processed Stripe event_ids in Redis with a 24-hour TTL and acquire a distributed mutex lock before processing webhook payloads.

Consequences:
- Zero duplicate order fulfillments.
- Redis availability required for payment reconci
[evt_why_pay_commit_7a] (git_commit:7a8b9c0d1e2f3a4b) feat(database): migrate to SQLAlchemy async connection pool with PgBouncer: Replaces raw psycopg2 connection per request with async connection pool. Reduces connection pool exhaustion under 2,000 checkout req/sec.
[evt_why_pay_issue_05] (github_issue:5) Issue #5: Duplicate customer charges under concurrent checkout clicks: Impatient users double clicking Pay Now sent parallel requests to /checkout initiating two distinct payment authorization transactions.
[evt_why_pay_pr_18] (github_pr:18) PR #18: Idempotency-Key Header Middleware with SHA-256 Request Hashing (Closes #5): Introduces Idempotency-Key HTTP header middleware computing SHA-256 digest of payload. Cache hit returns cached HTTP response immediately.
[evt_why_pay_rev_c402] (pr_review_comment:c402) Review on PR #18: Reject database-level transaction locks for idempotency: Using row-level database locks (SELECT FOR UPDATE) on the checkout table creates bottleneck deadlock risks during sales. Redis key-value atomicity is required.
[evt_why_pay_adr_03] (adr:docs/adr/0003-webhook-first-confirmation.md) ADR 0003: Webhook-First Asynchronous Order Confirmation: Status: accepted

Context:
Sync browser checkout redirect was dropping orders when mobile users closed Safari before the success return page loaded.

Decision:
Treat Stripe payment_intent.succeeded webhook event as the single source of truth for confirming orders rather than client-side redirects.

Consequences:
- Zero lost orders from closed tabs.
- Frontend displays pending state and listens via
[evt_why_pay_pr_22] (github_pr:22) PR #22: Webhook signature verification with HMAC-SHA256 and replay tolerance: Validates Stripe-Signature header with HMAC-SHA256 secret key and enforces a 300-second maximum timestamp drift window to prevent replay attacks.
[evt_why_pay_rev_c450] (pr_review_comment:c450) Review on PR #22: Reject skipping signature verification in development: Bypassing webhook signature checks via a debug flag risks shipping unverified endpoints to production. Verification must run in all environments with test keys.
[evt_why_pay_adr_04] (adr:docs/adr/0004-partial-refund-support.md) ADR 0004: Support Partial Refunds with Line-Item Reversal Ledger: Status: accepted

Context:
Customers returning one item out of a multi-item purchase required customer support intervention because the system only supported full-order voiding.

Decision:
Implement immutable append-only line-item reversal records tracking fractional refunds against order authorization totals.

Consequences:
- Eliminates manual support overrides for returns.
- Prevents cumulative 
[evt_why_pay_issue_11] (github_issue:11) Issue #11: Floating point rounding discrepancies during multi-currency partial refunds: Using standard IEEE 754 float types caused a 1-cent mismatch ($19.99 vs $19.989999) between partial refund sum and total charge.
[evt_why_pay_pr_29] (github_pr:29) PR #29: Migrate refund math to integer cents and Decimal representation (Closes #11): Converts all monetary fields to 64-bit integer minor currency units (cents) and Python Decimal to prevent floating point inaccuracies.
[evt_why_pay_rev_c505] (pr_review_comment:c505) Review on PR #29: Reject client-supplied refund timestamps: Relying on client timestamps allows fraudulent out-of-order refund attempts. Timestamps must strictly be generated by server UTC monotonic clock.
[evt_why_pay_issue_19] (github_issue:19) Issue #19: Toxic malformed webhook payloads causing infinite queue retry loops: Unparseable webhook payload triggered an unhandled exception causing RabbitMQ consumer to continually NACK and requeue, stalling normal processing.
[evt_why_pay_pr_35] (github_pr:35) PR #35: Route unparseable webhook messages to Dead Letter Queue after 3 failed deliveries (Closes #19): Configures DLQ with max-retries=3. Stalls are avoided by parking invalid messages for engineer inspection without blocking main line.
[evt_why_pay_adr_05] (adr:docs/adr/0005-pci-token-vault.md) ADR 0005: Dual-token vault encryption for PCI-DSS compliance: Status: accepted

Context:
PCI-DSS Scope Level 1 audit requires payment card numbers to never enter merchant application server memory or disk storage.

Decision:
Use Stripe Elements tokenization directly in client browser, receiving only opaque payment_method_id tokens on payment-core backend.

Consequences:
- Achieves PCI SAQ A eligibility, drastically reducing compliance overhead.
- Eliminates 
[evt_why_pay_rev_c610] (pr_review_comment:c610) Review on PR #38: Reject caching unencrypted CVV in memory: Storing raw CVVs even temporarily in Redis or local process memory is a direct violation of PCI-DSS requirement 3.2. Prohibit all CVV persistence.
```

---

### Trial 6: Question `WB_PAY_14`

- **Repository:** `acme-ecommerce/payment-core`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_pay_pr_29, evt_why_pay_issue_11`
- **Ground Truth Summary:** Migrated monetary calculations to 64-bit integer cents and Python Decimal types.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'acme-ecommerce/payment-core'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: How were fractional cent rounding errors solved in multi-currency refund calculations?

Event Stream:
[evt_why_pay_adr_01] (adr:docs/adr/0001-stripe-payment-migration.md) ADR 0001: Migrate from Legacy Braintree to Stripe Payment Intents API: Status: accepted

Context:
Legacy Braintree integration does not support European 3D Secure 2 authentication and suffers from elevated drop-off during checkout.

Decision:
Migrate checkout payment processing to Stripe Payment Intents with asynchronous webhook settlement.

Consequences:
- Full 3DS2 compliance.
- Checkout authorization latency reduced to <800ms.
- Requires webhook listener for async
[evt_why_pay_issue_08] (github_issue:8) Issue #8: Stripe API 429 Rate Limits encountered during flash sale traffic: During peak traffic burst, worker threads made simultaneous calls to Stripe charges API exceeding the 100 req/sec rate limit without jittered exponential backoff.
[evt_why_pay_pr_14] (github_pr:14) PR #14: Implement Exponential Backoff with Full Jitter for Stripe API (Closes #8): Adds decorator with decorator-level exponential backoff with full jitter (Decorrelated Jitter algorithm). Retries up to 4 times before failing.
[evt_why_pay_rev_c301] (pr_review_comment:c301) Review on PR #14: Reject fixed interval retries: Fixed 500ms sleep will create thundering herd when Stripe recovers. We must reject fixed sleep in favor of exponential backoff with randomized full jitter.
[evt_why_pay_adr_02] (adr:docs/adr/0002-webhook-idempotency.md) ADR 0002: Use Redis Distributed Lock and Idempotency Key for Webhooks: Status: accepted

Context:
Stripe webhook delivery guarantees at-least-once delivery. Duplicate payment.succeeded events caused double order fulfillment.

Decision:
Store processed Stripe event_ids in Redis with a 24-hour TTL and acquire a distributed mutex lock before processing webhook payloads.

Consequences:
- Zero duplicate order fulfillments.
- Redis availability required for payment reconci
[evt_why_pay_commit_7a] (git_commit:7a8b9c0d1e2f3a4b) feat(database): migrate to SQLAlchemy async connection pool with PgBouncer: Replaces raw psycopg2 connection per request with async connection pool. Reduces connection pool exhaustion under 2,000 checkout req/sec.
[evt_why_pay_issue_05] (github_issue:5) Issue #5: Duplicate customer charges under concurrent checkout clicks: Impatient users double clicking Pay Now sent parallel requests to /checkout initiating two distinct payment authorization transactions.
[evt_why_pay_pr_18] (github_pr:18) PR #18: Idempotency-Key Header Middleware with SHA-256 Request Hashing (Closes #5): Introduces Idempotency-Key HTTP header middleware computing SHA-256 digest of payload. Cache hit returns cached HTTP response immediately.
[evt_why_pay_rev_c402] (pr_review_comment:c402) Review on PR #18: Reject database-level transaction locks for idempotency: Using row-level database locks (SELECT FOR UPDATE) on the checkout table creates bottleneck deadlock risks during sales. Redis key-value atomicity is required.
[evt_why_pay_adr_03] (adr:docs/adr/0003-webhook-first-confirmation.md) ADR 0003: Webhook-First Asynchronous Order Confirmation: Status: accepted

Context:
Sync browser checkout redirect was dropping orders when mobile users closed Safari before the success return page loaded.

Decision:
Treat Stripe payment_intent.succeeded webhook event as the single source of truth for confirming orders rather than client-side redirects.

Consequences:
- Zero lost orders from closed tabs.
- Frontend displays pending state and listens via
[evt_why_pay_pr_22] (github_pr:22) PR #22: Webhook signature verification with HMAC-SHA256 and replay tolerance: Validates Stripe-Signature header with HMAC-SHA256 secret key and enforces a 300-second maximum timestamp drift window to prevent replay attacks.
[evt_why_pay_rev_c450] (pr_review_comment:c450) Review on PR #22: Reject skipping signature verification in development: Bypassing webhook signature checks via a debug flag risks shipping unverified endpoints to production. Verification must run in all environments with test keys.
[evt_why_pay_adr_04] (adr:docs/adr/0004-partial-refund-support.md) ADR 0004: Support Partial Refunds with Line-Item Reversal Ledger: Status: accepted

Context:
Customers returning one item out of a multi-item purchase required customer support intervention because the system only supported full-order voiding.

Decision:
Implement immutable append-only line-item reversal records tracking fractional refunds against order authorization totals.

Consequences:
- Eliminates manual support overrides for returns.
- Prevents cumulative 
[evt_why_pay_issue_11] (github_issue:11) Issue #11: Floating point rounding discrepancies during multi-currency partial refunds: Using standard IEEE 754 float types caused a 1-cent mismatch ($19.99 vs $19.989999) between partial refund sum and total charge.
[evt_why_pay_pr_29] (github_pr:29) PR #29: Migrate refund math to integer cents and Decimal representation (Closes #11): Converts all monetary fields to 64-bit integer minor currency units (cents) and Python Decimal to prevent floating point inaccuracies.
[evt_why_pay_rev_c505] (pr_review_comment:c505) Review on PR #29: Reject client-supplied refund timestamps: Relying on client timestamps allows fraudulent out-of-order refund attempts. Timestamps must strictly be generated by server UTC monotonic clock.
[evt_why_pay_issue_19] (github_issue:19) Issue #19: Toxic malformed webhook payloads causing infinite queue retry loops: Unparseable webhook payload triggered an unhandled exception causing RabbitMQ consumer to continually NACK and requeue, stalling normal processing.
[evt_why_pay_pr_35] (github_pr:35) PR #35: Route unparseable webhook messages to Dead Letter Queue after 3 failed deliveries (Closes #19): Configures DLQ with max-retries=3. Stalls are avoided by parking invalid messages for engineer inspection without blocking main line.
[evt_why_pay_adr_05] (adr:docs/adr/0005-pci-token-vault.md) ADR 0005: Dual-token vault encryption for PCI-DSS compliance: Status: accepted

Context:
PCI-DSS Scope Level 1 audit requires payment card numbers to never enter merchant application server memory or disk storage.

Decision:
Use Stripe Elements tokenization directly in client browser, receiving only opaque payment_method_id tokens on payment-core backend.

Consequences:
- Achieves PCI SAQ A eligibility, drastically reducing compliance overhead.
- Eliminates 
[evt_why_pay_rev_c610] (pr_review_comment:c610) Review on PR #38: Reject caching unencrypted CVV in memory: Storing raw CVVs even temporarily in Redis or local process memory is a direct violation of PCI-DSS requirement 3.2. Prohibit all CVV persistence.
```

---

### Trial 7: Question `WB_PAY_15`

- **Repository:** `acme-ecommerce/payment-core`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `rejected`
- **Expected Evidence Events:** `evt_why_pay_rev_c505`
- **Ground Truth Summary:** Untrusted client clocks permit replay attacks and out-of-order ledger anomalies; server UTC monotonic clock is required.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'acme-ecommerce/payment-core'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Why were client-supplied timestamps rejected for partial refund requests?

Event Stream:
[evt_why_pay_adr_01] (adr:docs/adr/0001-stripe-payment-migration.md) ADR 0001: Migrate from Legacy Braintree to Stripe Payment Intents API: Status: accepted

Context:
Legacy Braintree integration does not support European 3D Secure 2 authentication and suffers from elevated drop-off during checkout.

Decision:
Migrate checkout payment processing to Stripe Payment Intents with asynchronous webhook settlement.

Consequences:
- Full 3DS2 compliance.
- Checkout authorization latency reduced to <800ms.
- Requires webhook listener for async
[evt_why_pay_issue_08] (github_issue:8) Issue #8: Stripe API 429 Rate Limits encountered during flash sale traffic: During peak traffic burst, worker threads made simultaneous calls to Stripe charges API exceeding the 100 req/sec rate limit without jittered exponential backoff.
[evt_why_pay_pr_14] (github_pr:14) PR #14: Implement Exponential Backoff with Full Jitter for Stripe API (Closes #8): Adds decorator with decorator-level exponential backoff with full jitter (Decorrelated Jitter algorithm). Retries up to 4 times before failing.
[evt_why_pay_rev_c301] (pr_review_comment:c301) Review on PR #14: Reject fixed interval retries: Fixed 500ms sleep will create thundering herd when Stripe recovers. We must reject fixed sleep in favor of exponential backoff with randomized full jitter.
[evt_why_pay_adr_02] (adr:docs/adr/0002-webhook-idempotency.md) ADR 0002: Use Redis Distributed Lock and Idempotency Key for Webhooks: Status: accepted

Context:
Stripe webhook delivery guarantees at-least-once delivery. Duplicate payment.succeeded events caused double order fulfillment.

Decision:
Store processed Stripe event_ids in Redis with a 24-hour TTL and acquire a distributed mutex lock before processing webhook payloads.

Consequences:
- Zero duplicate order fulfillments.
- Redis availability required for payment reconci
[evt_why_pay_commit_7a] (git_commit:7a8b9c0d1e2f3a4b) feat(database): migrate to SQLAlchemy async connection pool with PgBouncer: Replaces raw psycopg2 connection per request with async connection pool. Reduces connection pool exhaustion under 2,000 checkout req/sec.
[evt_why_pay_issue_05] (github_issue:5) Issue #5: Duplicate customer charges under concurrent checkout clicks: Impatient users double clicking Pay Now sent parallel requests to /checkout initiating two distinct payment authorization transactions.
[evt_why_pay_pr_18] (github_pr:18) PR #18: Idempotency-Key Header Middleware with SHA-256 Request Hashing (Closes #5): Introduces Idempotency-Key HTTP header middleware computing SHA-256 digest of payload. Cache hit returns cached HTTP response immediately.
[evt_why_pay_rev_c402] (pr_review_comment:c402) Review on PR #18: Reject database-level transaction locks for idempotency: Using row-level database locks (SELECT FOR UPDATE) on the checkout table creates bottleneck deadlock risks during sales. Redis key-value atomicity is required.
[evt_why_pay_adr_03] (adr:docs/adr/0003-webhook-first-confirmation.md) ADR 0003: Webhook-First Asynchronous Order Confirmation: Status: accepted

Context:
Sync browser checkout redirect was dropping orders when mobile users closed Safari before the success return page loaded.

Decision:
Treat Stripe payment_intent.succeeded webhook event as the single source of truth for confirming orders rather than client-side redirects.

Consequences:
- Zero lost orders from closed tabs.
- Frontend displays pending state and listens via
[evt_why_pay_pr_22] (github_pr:22) PR #22: Webhook signature verification with HMAC-SHA256 and replay tolerance: Validates Stripe-Signature header with HMAC-SHA256 secret key and enforces a 300-second maximum timestamp drift window to prevent replay attacks.
[evt_why_pay_rev_c450] (pr_review_comment:c450) Review on PR #22: Reject skipping signature verification in development: Bypassing webhook signature checks via a debug flag risks shipping unverified endpoints to production. Verification must run in all environments with test keys.
[evt_why_pay_adr_04] (adr:docs/adr/0004-partial-refund-support.md) ADR 0004: Support Partial Refunds with Line-Item Reversal Ledger: Status: accepted

Context:
Customers returning one item out of a multi-item purchase required customer support intervention because the system only supported full-order voiding.

Decision:
Implement immutable append-only line-item reversal records tracking fractional refunds against order authorization totals.

Consequences:
- Eliminates manual support overrides for returns.
- Prevents cumulative 
[evt_why_pay_issue_11] (github_issue:11) Issue #11: Floating point rounding discrepancies during multi-currency partial refunds: Using standard IEEE 754 float types caused a 1-cent mismatch ($19.99 vs $19.989999) between partial refund sum and total charge.
[evt_why_pay_pr_29] (github_pr:29) PR #29: Migrate refund math to integer cents and Decimal representation (Closes #11): Converts all monetary fields to 64-bit integer minor currency units (cents) and Python Decimal to prevent floating point inaccuracies.
[evt_why_pay_rev_c505] (pr_review_comment:c505) Review on PR #29: Reject client-supplied refund timestamps: Relying on client timestamps allows fraudulent out-of-order refund attempts. Timestamps must strictly be generated by server UTC monotonic clock.
[evt_why_pay_issue_19] (github_issue:19) Issue #19: Toxic malformed webhook payloads causing infinite queue retry loops: Unparseable webhook payload triggered an unhandled exception causing RabbitMQ consumer to continually NACK and requeue, stalling normal processing.
[evt_why_pay_pr_35] (github_pr:35) PR #35: Route unparseable webhook messages to Dead Letter Queue after 3 failed deliveries (Closes #19): Configures DLQ with max-retries=3. Stalls are avoided by parking invalid messages for engineer inspection without blocking main line.
[evt_why_pay_adr_05] (adr:docs/adr/0005-pci-token-vault.md) ADR 0005: Dual-token vault encryption for PCI-DSS compliance: Status: accepted

Context:
PCI-DSS Scope Level 1 audit requires payment card numbers to never enter merchant application server memory or disk storage.

Decision:
Use Stripe Elements tokenization directly in client browser, receiving only opaque payment_method_id tokens on payment-core backend.

Consequences:
- Achieves PCI SAQ A eligibility, drastically reducing compliance overhead.
- Eliminates 
[evt_why_pay_rev_c610] (pr_review_comment:c610) Review on PR #38: Reject caching unencrypted CVV in memory: Storing raw CVVs even temporarily in Redis or local process memory is a direct violation of PCI-DSS requirement 3.2. Prohibit all CVV persistence.
```

---

### Trial 8: Question `WB_PAY_16`

- **Repository:** `acme-ecommerce/payment-core`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_pay_pr_35, evt_why_pay_issue_19`
- **Ground Truth Summary:** Parks toxic messages in a Dead Letter Queue (DLQ) after 3 failed delivery attempts.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'acme-ecommerce/payment-core'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: How does payment-core handle toxic malformed webhook messages that crash consumer workers?

Event Stream:
[evt_why_pay_adr_01] (adr:docs/adr/0001-stripe-payment-migration.md) ADR 0001: Migrate from Legacy Braintree to Stripe Payment Intents API: Status: accepted

Context:
Legacy Braintree integration does not support European 3D Secure 2 authentication and suffers from elevated drop-off during checkout.

Decision:
Migrate checkout payment processing to Stripe Payment Intents with asynchronous webhook settlement.

Consequences:
- Full 3DS2 compliance.
- Checkout authorization latency reduced to <800ms.
- Requires webhook listener for async
[evt_why_pay_issue_08] (github_issue:8) Issue #8: Stripe API 429 Rate Limits encountered during flash sale traffic: During peak traffic burst, worker threads made simultaneous calls to Stripe charges API exceeding the 100 req/sec rate limit without jittered exponential backoff.
[evt_why_pay_pr_14] (github_pr:14) PR #14: Implement Exponential Backoff with Full Jitter for Stripe API (Closes #8): Adds decorator with decorator-level exponential backoff with full jitter (Decorrelated Jitter algorithm). Retries up to 4 times before failing.
[evt_why_pay_rev_c301] (pr_review_comment:c301) Review on PR #14: Reject fixed interval retries: Fixed 500ms sleep will create thundering herd when Stripe recovers. We must reject fixed sleep in favor of exponential backoff with randomized full jitter.
[evt_why_pay_adr_02] (adr:docs/adr/0002-webhook-idempotency.md) ADR 0002: Use Redis Distributed Lock and Idempotency Key for Webhooks: Status: accepted

Context:
Stripe webhook delivery guarantees at-least-once delivery. Duplicate payment.succeeded events caused double order fulfillment.

Decision:
Store processed Stripe event_ids in Redis with a 24-hour TTL and acquire a distributed mutex lock before processing webhook payloads.

Consequences:
- Zero duplicate order fulfillments.
- Redis availability required for payment reconci
[evt_why_pay_commit_7a] (git_commit:7a8b9c0d1e2f3a4b) feat(database): migrate to SQLAlchemy async connection pool with PgBouncer: Replaces raw psycopg2 connection per request with async connection pool. Reduces connection pool exhaustion under 2,000 checkout req/sec.
[evt_why_pay_issue_05] (github_issue:5) Issue #5: Duplicate customer charges under concurrent checkout clicks: Impatient users double clicking Pay Now sent parallel requests to /checkout initiating two distinct payment authorization transactions.
[evt_why_pay_pr_18] (github_pr:18) PR #18: Idempotency-Key Header Middleware with SHA-256 Request Hashing (Closes #5): Introduces Idempotency-Key HTTP header middleware computing SHA-256 digest of payload. Cache hit returns cached HTTP response immediately.
[evt_why_pay_rev_c402] (pr_review_comment:c402) Review on PR #18: Reject database-level transaction locks for idempotency: Using row-level database locks (SELECT FOR UPDATE) on the checkout table creates bottleneck deadlock risks during sales. Redis key-value atomicity is required.
[evt_why_pay_adr_03] (adr:docs/adr/0003-webhook-first-confirmation.md) ADR 0003: Webhook-First Asynchronous Order Confirmation: Status: accepted

Context:
Sync browser checkout redirect was dropping orders when mobile users closed Safari before the success return page loaded.

Decision:
Treat Stripe payment_intent.succeeded webhook event as the single source of truth for confirming orders rather than client-side redirects.

Consequences:
- Zero lost orders from closed tabs.
- Frontend displays pending state and listens via
[evt_why_pay_pr_22] (github_pr:22) PR #22: Webhook signature verification with HMAC-SHA256 and replay tolerance: Validates Stripe-Signature header with HMAC-SHA256 secret key and enforces a 300-second maximum timestamp drift window to prevent replay attacks.
[evt_why_pay_rev_c450] (pr_review_comment:c450) Review on PR #22: Reject skipping signature verification in development: Bypassing webhook signature checks via a debug flag risks shipping unverified endpoints to production. Verification must run in all environments with test keys.
[evt_why_pay_adr_04] (adr:docs/adr/0004-partial-refund-support.md) ADR 0004: Support Partial Refunds with Line-Item Reversal Ledger: Status: accepted

Context:
Customers returning one item out of a multi-item purchase required customer support intervention because the system only supported full-order voiding.

Decision:
Implement immutable append-only line-item reversal records tracking fractional refunds against order authorization totals.

Consequences:
- Eliminates manual support overrides for returns.
- Prevents cumulative 
[evt_why_pay_issue_11] (github_issue:11) Issue #11: Floating point rounding discrepancies during multi-currency partial refunds: Using standard IEEE 754 float types caused a 1-cent mismatch ($19.99 vs $19.989999) between partial refund sum and total charge.
[evt_why_pay_pr_29] (github_pr:29) PR #29: Migrate refund math to integer cents and Decimal representation (Closes #11): Converts all monetary fields to 64-bit integer minor currency units (cents) and Python Decimal to prevent floating point inaccuracies.
[evt_why_pay_rev_c505] (pr_review_comment:c505) Review on PR #29: Reject client-supplied refund timestamps: Relying on client timestamps allows fraudulent out-of-order refund attempts. Timestamps must strictly be generated by server UTC monotonic clock.
[evt_why_pay_issue_19] (github_issue:19) Issue #19: Toxic malformed webhook payloads causing infinite queue retry loops: Unparseable webhook payload triggered an unhandled exception causing RabbitMQ consumer to continually NACK and requeue, stalling normal processing.
[evt_why_pay_pr_35] (github_pr:35) PR #35: Route unparseable webhook messages to Dead Letter Queue after 3 failed deliveries (Closes #19): Configures DLQ with max-retries=3. Stalls are avoided by parking invalid messages for engineer inspection without blocking main line.
[evt_why_pay_adr_05] (adr:docs/adr/0005-pci-token-vault.md) ADR 0005: Dual-token vault encryption for PCI-DSS compliance: Status: accepted

Context:
PCI-DSS Scope Level 1 audit requires payment card numbers to never enter merchant application server memory or disk storage.

Decision:
Use Stripe Elements tokenization directly in client browser, receiving only opaque payment_method_id tokens on payment-core backend.

Consequences:
- Achieves PCI SAQ A eligibility, drastically reducing compliance overhead.
- Eliminates 
[evt_why_pay_rev_c610] (pr_review_comment:c610) Review on PR #38: Reject caching unencrypted CVV in memory: Storing raw CVVs even temporarily in Redis or local process memory is a direct violation of PCI-DSS requirement 3.2. Prohibit all CVV persistence.
```

---

### Trial 9: Question `WB_PAY_17`

- **Repository:** `acme-ecommerce/payment-core`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_pay_adr_05`
- **Ground Truth Summary:** Delegates card data collection to browser Stripe Elements, storing only opaque payment_method_id tokens on the backend.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'acme-ecommerce/payment-core'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: How does payment-core achieve PCI SAQ A compliance for credit card processing?

Event Stream:
[evt_why_pay_adr_01] (adr:docs/adr/0001-stripe-payment-migration.md) ADR 0001: Migrate from Legacy Braintree to Stripe Payment Intents API: Status: accepted

Context:
Legacy Braintree integration does not support European 3D Secure 2 authentication and suffers from elevated drop-off during checkout.

Decision:
Migrate checkout payment processing to Stripe Payment Intents with asynchronous webhook settlement.

Consequences:
- Full 3DS2 compliance.
- Checkout authorization latency reduced to <800ms.
- Requires webhook listener for async
[evt_why_pay_issue_08] (github_issue:8) Issue #8: Stripe API 429 Rate Limits encountered during flash sale traffic: During peak traffic burst, worker threads made simultaneous calls to Stripe charges API exceeding the 100 req/sec rate limit without jittered exponential backoff.
[evt_why_pay_pr_14] (github_pr:14) PR #14: Implement Exponential Backoff with Full Jitter for Stripe API (Closes #8): Adds decorator with decorator-level exponential backoff with full jitter (Decorrelated Jitter algorithm). Retries up to 4 times before failing.
[evt_why_pay_rev_c301] (pr_review_comment:c301) Review on PR #14: Reject fixed interval retries: Fixed 500ms sleep will create thundering herd when Stripe recovers. We must reject fixed sleep in favor of exponential backoff with randomized full jitter.
[evt_why_pay_adr_02] (adr:docs/adr/0002-webhook-idempotency.md) ADR 0002: Use Redis Distributed Lock and Idempotency Key for Webhooks: Status: accepted

Context:
Stripe webhook delivery guarantees at-least-once delivery. Duplicate payment.succeeded events caused double order fulfillment.

Decision:
Store processed Stripe event_ids in Redis with a 24-hour TTL and acquire a distributed mutex lock before processing webhook payloads.

Consequences:
- Zero duplicate order fulfillments.
- Redis availability required for payment reconci
[evt_why_pay_commit_7a] (git_commit:7a8b9c0d1e2f3a4b) feat(database): migrate to SQLAlchemy async connection pool with PgBouncer: Replaces raw psycopg2 connection per request with async connection pool. Reduces connection pool exhaustion under 2,000 checkout req/sec.
[evt_why_pay_issue_05] (github_issue:5) Issue #5: Duplicate customer charges under concurrent checkout clicks: Impatient users double clicking Pay Now sent parallel requests to /checkout initiating two distinct payment authorization transactions.
[evt_why_pay_pr_18] (github_pr:18) PR #18: Idempotency-Key Header Middleware with SHA-256 Request Hashing (Closes #5): Introduces Idempotency-Key HTTP header middleware computing SHA-256 digest of payload. Cache hit returns cached HTTP response immediately.
[evt_why_pay_rev_c402] (pr_review_comment:c402) Review on PR #18: Reject database-level transaction locks for idempotency: Using row-level database locks (SELECT FOR UPDATE) on the checkout table creates bottleneck deadlock risks during sales. Redis key-value atomicity is required.
[evt_why_pay_adr_03] (adr:docs/adr/0003-webhook-first-confirmation.md) ADR 0003: Webhook-First Asynchronous Order Confirmation: Status: accepted

Context:
Sync browser checkout redirect was dropping orders when mobile users closed Safari before the success return page loaded.

Decision:
Treat Stripe payment_intent.succeeded webhook event as the single source of truth for confirming orders rather than client-side redirects.

Consequences:
- Zero lost orders from closed tabs.
- Frontend displays pending state and listens via
[evt_why_pay_pr_22] (github_pr:22) PR #22: Webhook signature verification with HMAC-SHA256 and replay tolerance: Validates Stripe-Signature header with HMAC-SHA256 secret key and enforces a 300-second maximum timestamp drift window to prevent replay attacks.
[evt_why_pay_rev_c450] (pr_review_comment:c450) Review on PR #22: Reject skipping signature verification in development: Bypassing webhook signature checks via a debug flag risks shipping unverified endpoints to production. Verification must run in all environments with test keys.
[evt_why_pay_adr_04] (adr:docs/adr/0004-partial-refund-support.md) ADR 0004: Support Partial Refunds with Line-Item Reversal Ledger: Status: accepted

Context:
Customers returning one item out of a multi-item purchase required customer support intervention because the system only supported full-order voiding.

Decision:
Implement immutable append-only line-item reversal records tracking fractional refunds against order authorization totals.

Consequences:
- Eliminates manual support overrides for returns.
- Prevents cumulative 
[evt_why_pay_issue_11] (github_issue:11) Issue #11: Floating point rounding discrepancies during multi-currency partial refunds: Using standard IEEE 754 float types caused a 1-cent mismatch ($19.99 vs $19.989999) between partial refund sum and total charge.
[evt_why_pay_pr_29] (github_pr:29) PR #29: Migrate refund math to integer cents and Decimal representation (Closes #11): Converts all monetary fields to 64-bit integer minor currency units (cents) and Python Decimal to prevent floating point inaccuracies.
[evt_why_pay_rev_c505] (pr_review_comment:c505) Review on PR #29: Reject client-supplied refund timestamps: Relying on client timestamps allows fraudulent out-of-order refund attempts. Timestamps must strictly be generated by server UTC monotonic clock.
[evt_why_pay_issue_19] (github_issue:19) Issue #19: Toxic malformed webhook payloads causing infinite queue retry loops: Unparseable webhook payload triggered an unhandled exception causing RabbitMQ consumer to continually NACK and requeue, stalling normal processing.
[evt_why_pay_pr_35] (github_pr:35) PR #35: Route unparseable webhook messages to Dead Letter Queue after 3 failed deliveries (Closes #19): Configures DLQ with max-retries=3. Stalls are avoided by parking invalid messages for engineer inspection without blocking main line.
[evt_why_pay_adr_05] (adr:docs/adr/0005-pci-token-vault.md) ADR 0005: Dual-token vault encryption for PCI-DSS compliance: Status: accepted

Context:
PCI-DSS Scope Level 1 audit requires payment card numbers to never enter merchant application server memory or disk storage.

Decision:
Use Stripe Elements tokenization directly in client browser, receiving only opaque payment_method_id tokens on payment-core backend.

Consequences:
- Achieves PCI SAQ A eligibility, drastically reducing compliance overhead.
- Eliminates 
[evt_why_pay_rev_c610] (pr_review_comment:c610) Review on PR #38: Reject caching unencrypted CVV in memory: Storing raw CVVs even temporarily in Redis or local process memory is a direct violation of PCI-DSS requirement 3.2. Prohibit all CVV persistence.
```

---

### Trial 10: Question `WB_PAY_18`

- **Repository:** `acme-ecommerce/payment-core`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `rejected`
- **Expected Evidence Events:** `evt_why_pay_rev_c610`
- **Ground Truth Summary:** Direct violation of PCI-DSS Requirement 3.2 prohibiting post-authorization CVV storage.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'acme-ecommerce/payment-core'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Why was in-memory caching of card CVV security codes rejected?

Event Stream:
[evt_why_pay_adr_01] (adr:docs/adr/0001-stripe-payment-migration.md) ADR 0001: Migrate from Legacy Braintree to Stripe Payment Intents API: Status: accepted

Context:
Legacy Braintree integration does not support European 3D Secure 2 authentication and suffers from elevated drop-off during checkout.

Decision:
Migrate checkout payment processing to Stripe Payment Intents with asynchronous webhook settlement.

Consequences:
- Full 3DS2 compliance.
- Checkout authorization latency reduced to <800ms.
- Requires webhook listener for async
[evt_why_pay_issue_08] (github_issue:8) Issue #8: Stripe API 429 Rate Limits encountered during flash sale traffic: During peak traffic burst, worker threads made simultaneous calls to Stripe charges API exceeding the 100 req/sec rate limit without jittered exponential backoff.
[evt_why_pay_pr_14] (github_pr:14) PR #14: Implement Exponential Backoff with Full Jitter for Stripe API (Closes #8): Adds decorator with decorator-level exponential backoff with full jitter (Decorrelated Jitter algorithm). Retries up to 4 times before failing.
[evt_why_pay_rev_c301] (pr_review_comment:c301) Review on PR #14: Reject fixed interval retries: Fixed 500ms sleep will create thundering herd when Stripe recovers. We must reject fixed sleep in favor of exponential backoff with randomized full jitter.
[evt_why_pay_adr_02] (adr:docs/adr/0002-webhook-idempotency.md) ADR 0002: Use Redis Distributed Lock and Idempotency Key for Webhooks: Status: accepted

Context:
Stripe webhook delivery guarantees at-least-once delivery. Duplicate payment.succeeded events caused double order fulfillment.

Decision:
Store processed Stripe event_ids in Redis with a 24-hour TTL and acquire a distributed mutex lock before processing webhook payloads.

Consequences:
- Zero duplicate order fulfillments.
- Redis availability required for payment reconci
[evt_why_pay_commit_7a] (git_commit:7a8b9c0d1e2f3a4b) feat(database): migrate to SQLAlchemy async connection pool with PgBouncer: Replaces raw psycopg2 connection per request with async connection pool. Reduces connection pool exhaustion under 2,000 checkout req/sec.
[evt_why_pay_issue_05] (github_issue:5) Issue #5: Duplicate customer charges under concurrent checkout clicks: Impatient users double clicking Pay Now sent parallel requests to /checkout initiating two distinct payment authorization transactions.
[evt_why_pay_pr_18] (github_pr:18) PR #18: Idempotency-Key Header Middleware with SHA-256 Request Hashing (Closes #5): Introduces Idempotency-Key HTTP header middleware computing SHA-256 digest of payload. Cache hit returns cached HTTP response immediately.
[evt_why_pay_rev_c402] (pr_review_comment:c402) Review on PR #18: Reject database-level transaction locks for idempotency: Using row-level database locks (SELECT FOR UPDATE) on the checkout table creates bottleneck deadlock risks during sales. Redis key-value atomicity is required.
[evt_why_pay_adr_03] (adr:docs/adr/0003-webhook-first-confirmation.md) ADR 0003: Webhook-First Asynchronous Order Confirmation: Status: accepted

Context:
Sync browser checkout redirect was dropping orders when mobile users closed Safari before the success return page loaded.

Decision:
Treat Stripe payment_intent.succeeded webhook event as the single source of truth for confirming orders rather than client-side redirects.

Consequences:
- Zero lost orders from closed tabs.
- Frontend displays pending state and listens via
[evt_why_pay_pr_22] (github_pr:22) PR #22: Webhook signature verification with HMAC-SHA256 and replay tolerance: Validates Stripe-Signature header with HMAC-SHA256 secret key and enforces a 300-second maximum timestamp drift window to prevent replay attacks.
[evt_why_pay_rev_c450] (pr_review_comment:c450) Review on PR #22: Reject skipping signature verification in development: Bypassing webhook signature checks via a debug flag risks shipping unverified endpoints to production. Verification must run in all environments with test keys.
[evt_why_pay_adr_04] (adr:docs/adr/0004-partial-refund-support.md) ADR 0004: Support Partial Refunds with Line-Item Reversal Ledger: Status: accepted

Context:
Customers returning one item out of a multi-item purchase required customer support intervention because the system only supported full-order voiding.

Decision:
Implement immutable append-only line-item reversal records tracking fractional refunds against order authorization totals.

Consequences:
- Eliminates manual support overrides for returns.
- Prevents cumulative 
[evt_why_pay_issue_11] (github_issue:11) Issue #11: Floating point rounding discrepancies during multi-currency partial refunds: Using standard IEEE 754 float types caused a 1-cent mismatch ($19.99 vs $19.989999) between partial refund sum and total charge.
[evt_why_pay_pr_29] (github_pr:29) PR #29: Migrate refund math to integer cents and Decimal representation (Closes #11): Converts all monetary fields to 64-bit integer minor currency units (cents) and Python Decimal to prevent floating point inaccuracies.
[evt_why_pay_rev_c505] (pr_review_comment:c505) Review on PR #29: Reject client-supplied refund timestamps: Relying on client timestamps allows fraudulent out-of-order refund attempts. Timestamps must strictly be generated by server UTC monotonic clock.
[evt_why_pay_issue_19] (github_issue:19) Issue #19: Toxic malformed webhook payloads causing infinite queue retry loops: Unparseable webhook payload triggered an unhandled exception causing RabbitMQ consumer to continually NACK and requeue, stalling normal processing.
[evt_why_pay_pr_35] (github_pr:35) PR #35: Route unparseable webhook messages to Dead Letter Queue after 3 failed deliveries (Closes #19): Configures DLQ with max-retries=3. Stalls are avoided by parking invalid messages for engineer inspection without blocking main line.
[evt_why_pay_adr_05] (adr:docs/adr/0005-pci-token-vault.md) ADR 0005: Dual-token vault encryption for PCI-DSS compliance: Status: accepted

Context:
PCI-DSS Scope Level 1 audit requires payment card numbers to never enter merchant application server memory or disk storage.

Decision:
Use Stripe Elements tokenization directly in client browser, receiving only opaque payment_method_id tokens on payment-core backend.

Consequences:
- Achieves PCI SAQ A eligibility, drastically reducing compliance overhead.
- Eliminates 
[evt_why_pay_rev_c610] (pr_review_comment:c610) Review on PR #38: Reject caching unencrypted CVV in memory: Storing raw CVVs even temporarily in Redis or local process memory is a direct violation of PCI-DSS requirement 3.2. Prohibit all CVV persistence.
```

---

### Trial 11: Question `WB_CH_09`

- **Repository:** `cloud-hypervisor/cloud-hypervisor`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `rejected`
- **Expected Evidence Events:** `evt_why_ch_rev_c615`
- **Ground Truth Summary:** Legacy peripheral emulation violates the minimal attack surface mission; only VirtIO and modern PCIe devices are supported.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cloud-hypervisor/cloud-hypervisor'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Why was legacy floppy and IDE drive emulation rejected?

Event Stream:
[evt_why_ch_rfc_01] (adr:docs/designs/live-migration.md) Design: Pre-copy Live Migration with Dirty Page Tracking via KVM dirty ring: Status: accepted

Context:
Virtual machine live migration must minimize downtime below 50ms while transferring guest memory under active workloads.

Decision:
Implement iterative pre-copy migration using KVM dirty ring buffer instead of classic user-faultfd or dirty bitmap.

Consequences:
- Drastically reduces lock contention during memory dirty page capture.
- Guest pause time under 35ms on 10GbE
[evt_why_ch_pr_1042] (github_pr:1042) PR #1042: Implement VirtIO Memory Ballooning with Page Reporting: Adds virtio-balloon device supporting automatic unused page reporting back to host hypervisor. Enables dynamic RAM overcommit without guest performance degradation.
[evt_why_ch_issue_890] (github_issue:890) Issue #890: Memory balloon deflation stalls under aggressive host memory pressure: When host demands quick reclamation, balloon thread deadlock occurred due to synchronous locking on memory allocation bus.
[evt_why_ch_rev_c502] (pr_review_comment:c502) Review on PR #1042: Reject synchronous balloon deflation: Synchronous deflation blocks guest vCPUs for up to 400ms. We must reject synchronous balloon worker in favor of asynchronous background worker thread.
[evt_why_ch_rfc_03] (adr:docs/designs/vhost-user-net.md) Design: Vhost-User Network Backend with Multi-Queue Support: Status: accepted

Context:
Standard TAP networking limits packet throughput to ~1.2 Mpps due to kernel context switching overhead.

Decision:
Implement vhost-user-net backend delegating packet processing to DPDK/OVS processes via shared memory queues.

Consequences:
- Achieves line-rate 10GbE throughput (>8 Mpps).
- Eliminates kernel networking path context switches.
[evt_why_ch_rfc_02] (adr:docs/designs/direct-kernel-boot.md) Design: Direct Linux Kernel Boot without Legacy BIOS/GRUB: Status: accepted

Context:
Booting a full SeaBIOS or UEFI image adds 500ms-2s of cold start latency to cloud hypervisor microVMs.

Decision:
Implement direct ELF/bzImage loader jumping straight into the Linux kernel entry point with boot_params setup.

Consequences:
- Sub-30ms VM boot times.
- Eliminates legacy BIOS real-mode emulation code from VMM.
[evt_why_ch_issue_940] (github_issue:940) Issue #940: High guest exit latency on unpinned multi-threaded vCPUs: vCPU threads migrating across NUMA nodes caused up to 300% tail latency jitter on latency-sensitive guest workloads.
[evt_why_ch_pr_1105] (github_pr:1105) PR #1105: CPU Pinning and NUMA Topology Node Binding (Closes #940): Allows operator to pin guest vCPUs to specific host physical cores and bind guest RAM to local host NUMA nodes using libc::sched_setaffinity.
[evt_why_ch_rev_c615] (pr_review_comment:c615) Review on PR #1105: Reject legacy floppy and IDE device emulation: Emulating legacy PC hardware (floppy, IDE, PS/2) contradicts Cloud Hypervisor's minimal attack surface goal. Only modern VirtIO and PCIe interfaces will be supported.
[evt_why_ch_rfc_04] (adr:docs/designs/virtio-fs.md) Design: VirtIO-FS Shared Host Filesystem with Direct Access (DAX) Window: Status: accepted

Context:
Container runtimes (Kata Containers) need efficient sharing of host root filesystems with minimal memory overhead.

Decision:
Support virtio-fs device with a dedicated DAX window mapping host page cache directly into guest physical address space.

Consequences:
- Zero guest page cache memory duplication.
- File reads bypass guest I/O path directly to host cache.
[evt_why_ch_issue_1015] (github_issue:1015) Issue #1015: Host file lock contention in virtio-fs shared directory mounts: Multiple concurrent containers writing to shared virtio-fs directory caused POSIX file lock contention in virtiofsd daemon.
[evt_why_ch_pr_1180] (github_pr:1180) PR #1180: PCIe Root Port Hotplug Support for VirtIO Devices: Adds ACPI PCI hotplug notifications and PCIe native hotplug controller allowing runtime addition and removal of network interfaces and disks.
[evt_why_ch_pr_1240] (github_pr:1240) PR #1240: Asynchronous Disk I/O via Linux io_uring Engine: Replaces threadpool synchronous pread/pwrite with io_uring submission/completion queue rings for virtio-block backend.
[evt_why_ch_rev_c720] (pr_review_comment:c720) Review on PR #1240: Reject unbounded polling loops in vhost worker: Spin-polling io_uring SQPOLL thread pegging 100% CPU on idle guests is prohibited. Eventfd notification must be used when queue is drained.
[evt_why_ch_pr_1312] (github_pr:1312) PR #1312: VFIO PCI Device Passthrough for GPU Workloads: Integrates VFIO Linux kernel API enabling secure hardware DMA remapping and MSI-X interrupt forwarding for dedicated guest GPUs and NVMe drives.
[evt_why_ch_rfc_05] (adr:docs/designs/acpi-ged.md) Design: ACPI Generic Event Device (GED) for System Notifications: Status: accepted

Context:
Handling power button, shutdown, and hotplug interrupts previously required complex proprietary DSDT methods.

Decision:
Adopt ACPI 5.0 Generic Event Device (GED) providing simplified interrupt-driven event signaling across x86_64 and AArch64.

Consequences:
- Unified event dispatch table across architectures.
- Removes ~1,200 lines of architecture-specific AML bytecode.
[evt_why_ch_issue_1120] (github_issue:1120) Issue #1120: Guest memory leak in balloon statistics driver queue: Periodic stat queue buffers allocated by guest kernel were leaked when host neglected to acknowledge polling rings.
[evt_why_ch_pr_1390] (github_pr:1390) PR #1390: MicroVM Minimal Device Tree Profile for Serverless Sandboxes: Configures minimal sandbox VM profile stripping ACPI tables and serial emulation, reducing guest boot time to 12ms for AWS Lambda style workloads.
```

---

### Trial 12: Question `WB_CH_10`

- **Repository:** `cloud-hypervisor/cloud-hypervisor`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_ch_rfc_04`
- **Ground Truth Summary:** Maps host page cache directly into guest address space using a Direct Access (DAX) memory window.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cloud-hypervisor/cloud-hypervisor'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: How does virtio-fs avoid memory duplication when sharing container root filesystems?

Event Stream:
[evt_why_ch_rfc_01] (adr:docs/designs/live-migration.md) Design: Pre-copy Live Migration with Dirty Page Tracking via KVM dirty ring: Status: accepted

Context:
Virtual machine live migration must minimize downtime below 50ms while transferring guest memory under active workloads.

Decision:
Implement iterative pre-copy migration using KVM dirty ring buffer instead of classic user-faultfd or dirty bitmap.

Consequences:
- Drastically reduces lock contention during memory dirty page capture.
- Guest pause time under 35ms on 10GbE
[evt_why_ch_pr_1042] (github_pr:1042) PR #1042: Implement VirtIO Memory Ballooning with Page Reporting: Adds virtio-balloon device supporting automatic unused page reporting back to host hypervisor. Enables dynamic RAM overcommit without guest performance degradation.
[evt_why_ch_issue_890] (github_issue:890) Issue #890: Memory balloon deflation stalls under aggressive host memory pressure: When host demands quick reclamation, balloon thread deadlock occurred due to synchronous locking on memory allocation bus.
[evt_why_ch_rev_c502] (pr_review_comment:c502) Review on PR #1042: Reject synchronous balloon deflation: Synchronous deflation blocks guest vCPUs for up to 400ms. We must reject synchronous balloon worker in favor of asynchronous background worker thread.
[evt_why_ch_rfc_03] (adr:docs/designs/vhost-user-net.md) Design: Vhost-User Network Backend with Multi-Queue Support: Status: accepted

Context:
Standard TAP networking limits packet throughput to ~1.2 Mpps due to kernel context switching overhead.

Decision:
Implement vhost-user-net backend delegating packet processing to DPDK/OVS processes via shared memory queues.

Consequences:
- Achieves line-rate 10GbE throughput (>8 Mpps).
- Eliminates kernel networking path context switches.
[evt_why_ch_rfc_02] (adr:docs/designs/direct-kernel-boot.md) Design: Direct Linux Kernel Boot without Legacy BIOS/GRUB: Status: accepted

Context:
Booting a full SeaBIOS or UEFI image adds 500ms-2s of cold start latency to cloud hypervisor microVMs.

Decision:
Implement direct ELF/bzImage loader jumping straight into the Linux kernel entry point with boot_params setup.

Consequences:
- Sub-30ms VM boot times.
- Eliminates legacy BIOS real-mode emulation code from VMM.
[evt_why_ch_issue_940] (github_issue:940) Issue #940: High guest exit latency on unpinned multi-threaded vCPUs: vCPU threads migrating across NUMA nodes caused up to 300% tail latency jitter on latency-sensitive guest workloads.
[evt_why_ch_pr_1105] (github_pr:1105) PR #1105: CPU Pinning and NUMA Topology Node Binding (Closes #940): Allows operator to pin guest vCPUs to specific host physical cores and bind guest RAM to local host NUMA nodes using libc::sched_setaffinity.
[evt_why_ch_rev_c615] (pr_review_comment:c615) Review on PR #1105: Reject legacy floppy and IDE device emulation: Emulating legacy PC hardware (floppy, IDE, PS/2) contradicts Cloud Hypervisor's minimal attack surface goal. Only modern VirtIO and PCIe interfaces will be supported.
[evt_why_ch_rfc_04] (adr:docs/designs/virtio-fs.md) Design: VirtIO-FS Shared Host Filesystem with Direct Access (DAX) Window: Status: accepted

Context:
Container runtimes (Kata Containers) need efficient sharing of host root filesystems with minimal memory overhead.

Decision:
Support virtio-fs device with a dedicated DAX window mapping host page cache directly into guest physical address space.

Consequences:
- Zero guest page cache memory duplication.
- File reads bypass guest I/O path directly to host cache.
[evt_why_ch_issue_1015] (github_issue:1015) Issue #1015: Host file lock contention in virtio-fs shared directory mounts: Multiple concurrent containers writing to shared virtio-fs directory caused POSIX file lock contention in virtiofsd daemon.
[evt_why_ch_pr_1180] (github_pr:1180) PR #1180: PCIe Root Port Hotplug Support for VirtIO Devices: Adds ACPI PCI hotplug notifications and PCIe native hotplug controller allowing runtime addition and removal of network interfaces and disks.
[evt_why_ch_pr_1240] (github_pr:1240) PR #1240: Asynchronous Disk I/O via Linux io_uring Engine: Replaces threadpool synchronous pread/pwrite with io_uring submission/completion queue rings for virtio-block backend.
[evt_why_ch_rev_c720] (pr_review_comment:c720) Review on PR #1240: Reject unbounded polling loops in vhost worker: Spin-polling io_uring SQPOLL thread pegging 100% CPU on idle guests is prohibited. Eventfd notification must be used when queue is drained.
[evt_why_ch_pr_1312] (github_pr:1312) PR #1312: VFIO PCI Device Passthrough for GPU Workloads: Integrates VFIO Linux kernel API enabling secure hardware DMA remapping and MSI-X interrupt forwarding for dedicated guest GPUs and NVMe drives.
[evt_why_ch_rfc_05] (adr:docs/designs/acpi-ged.md) Design: ACPI Generic Event Device (GED) for System Notifications: Status: accepted

Context:
Handling power button, shutdown, and hotplug interrupts previously required complex proprietary DSDT methods.

Decision:
Adopt ACPI 5.0 Generic Event Device (GED) providing simplified interrupt-driven event signaling across x86_64 and AArch64.

Consequences:
- Unified event dispatch table across architectures.
- Removes ~1,200 lines of architecture-specific AML bytecode.
[evt_why_ch_issue_1120] (github_issue:1120) Issue #1120: Guest memory leak in balloon statistics driver queue: Periodic stat queue buffers allocated by guest kernel were leaked when host neglected to acknowledge polling rings.
[evt_why_ch_pr_1390] (github_pr:1390) PR #1390: MicroVM Minimal Device Tree Profile for Serverless Sandboxes: Configures minimal sandbox VM profile stripping ACPI tables and serial emulation, reducing guest boot time to 12ms for AWS Lambda style workloads.
```

---

### Trial 13: Question `WB_CH_11`

- **Repository:** `cloud-hypervisor/cloud-hypervisor`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_ch_pr_1180`
- **Ground Truth Summary:** Implements PCIe native hotplug controller and ACPI PCI notification methods in PR #1180.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cloud-hypervisor/cloud-hypervisor'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: How does Cloud Hypervisor support dynamic hotplug of PCIe devices?

Event Stream:
[evt_why_ch_rfc_01] (adr:docs/designs/live-migration.md) Design: Pre-copy Live Migration with Dirty Page Tracking via KVM dirty ring: Status: accepted

Context:
Virtual machine live migration must minimize downtime below 50ms while transferring guest memory under active workloads.

Decision:
Implement iterative pre-copy migration using KVM dirty ring buffer instead of classic user-faultfd or dirty bitmap.

Consequences:
- Drastically reduces lock contention during memory dirty page capture.
- Guest pause time under 35ms on 10GbE
[evt_why_ch_pr_1042] (github_pr:1042) PR #1042: Implement VirtIO Memory Ballooning with Page Reporting: Adds virtio-balloon device supporting automatic unused page reporting back to host hypervisor. Enables dynamic RAM overcommit without guest performance degradation.
[evt_why_ch_issue_890] (github_issue:890) Issue #890: Memory balloon deflation stalls under aggressive host memory pressure: When host demands quick reclamation, balloon thread deadlock occurred due to synchronous locking on memory allocation bus.
[evt_why_ch_rev_c502] (pr_review_comment:c502) Review on PR #1042: Reject synchronous balloon deflation: Synchronous deflation blocks guest vCPUs for up to 400ms. We must reject synchronous balloon worker in favor of asynchronous background worker thread.
[evt_why_ch_rfc_03] (adr:docs/designs/vhost-user-net.md) Design: Vhost-User Network Backend with Multi-Queue Support: Status: accepted

Context:
Standard TAP networking limits packet throughput to ~1.2 Mpps due to kernel context switching overhead.

Decision:
Implement vhost-user-net backend delegating packet processing to DPDK/OVS processes via shared memory queues.

Consequences:
- Achieves line-rate 10GbE throughput (>8 Mpps).
- Eliminates kernel networking path context switches.
[evt_why_ch_rfc_02] (adr:docs/designs/direct-kernel-boot.md) Design: Direct Linux Kernel Boot without Legacy BIOS/GRUB: Status: accepted

Context:
Booting a full SeaBIOS or UEFI image adds 500ms-2s of cold start latency to cloud hypervisor microVMs.

Decision:
Implement direct ELF/bzImage loader jumping straight into the Linux kernel entry point with boot_params setup.

Consequences:
- Sub-30ms VM boot times.
- Eliminates legacy BIOS real-mode emulation code from VMM.
[evt_why_ch_issue_940] (github_issue:940) Issue #940: High guest exit latency on unpinned multi-threaded vCPUs: vCPU threads migrating across NUMA nodes caused up to 300% tail latency jitter on latency-sensitive guest workloads.
[evt_why_ch_pr_1105] (github_pr:1105) PR #1105: CPU Pinning and NUMA Topology Node Binding (Closes #940): Allows operator to pin guest vCPUs to specific host physical cores and bind guest RAM to local host NUMA nodes using libc::sched_setaffinity.
[evt_why_ch_rev_c615] (pr_review_comment:c615) Review on PR #1105: Reject legacy floppy and IDE device emulation: Emulating legacy PC hardware (floppy, IDE, PS/2) contradicts Cloud Hypervisor's minimal attack surface goal. Only modern VirtIO and PCIe interfaces will be supported.
[evt_why_ch_rfc_04] (adr:docs/designs/virtio-fs.md) Design: VirtIO-FS Shared Host Filesystem with Direct Access (DAX) Window: Status: accepted

Context:
Container runtimes (Kata Containers) need efficient sharing of host root filesystems with minimal memory overhead.

Decision:
Support virtio-fs device with a dedicated DAX window mapping host page cache directly into guest physical address space.

Consequences:
- Zero guest page cache memory duplication.
- File reads bypass guest I/O path directly to host cache.
[evt_why_ch_issue_1015] (github_issue:1015) Issue #1015: Host file lock contention in virtio-fs shared directory mounts: Multiple concurrent containers writing to shared virtio-fs directory caused POSIX file lock contention in virtiofsd daemon.
[evt_why_ch_pr_1180] (github_pr:1180) PR #1180: PCIe Root Port Hotplug Support for VirtIO Devices: Adds ACPI PCI hotplug notifications and PCIe native hotplug controller allowing runtime addition and removal of network interfaces and disks.
[evt_why_ch_pr_1240] (github_pr:1240) PR #1240: Asynchronous Disk I/O via Linux io_uring Engine: Replaces threadpool synchronous pread/pwrite with io_uring submission/completion queue rings for virtio-block backend.
[evt_why_ch_rev_c720] (pr_review_comment:c720) Review on PR #1240: Reject unbounded polling loops in vhost worker: Spin-polling io_uring SQPOLL thread pegging 100% CPU on idle guests is prohibited. Eventfd notification must be used when queue is drained.
[evt_why_ch_pr_1312] (github_pr:1312) PR #1312: VFIO PCI Device Passthrough for GPU Workloads: Integrates VFIO Linux kernel API enabling secure hardware DMA remapping and MSI-X interrupt forwarding for dedicated guest GPUs and NVMe drives.
[evt_why_ch_rfc_05] (adr:docs/designs/acpi-ged.md) Design: ACPI Generic Event Device (GED) for System Notifications: Status: accepted

Context:
Handling power button, shutdown, and hotplug interrupts previously required complex proprietary DSDT methods.

Decision:
Adopt ACPI 5.0 Generic Event Device (GED) providing simplified interrupt-driven event signaling across x86_64 and AArch64.

Consequences:
- Unified event dispatch table across architectures.
- Removes ~1,200 lines of architecture-specific AML bytecode.
[evt_why_ch_issue_1120] (github_issue:1120) Issue #1120: Guest memory leak in balloon statistics driver queue: Periodic stat queue buffers allocated by guest kernel were leaked when host neglected to acknowledge polling rings.
[evt_why_ch_pr_1390] (github_pr:1390) PR #1390: MicroVM Minimal Device Tree Profile for Serverless Sandboxes: Configures minimal sandbox VM profile stripping ACPI tables and serial emulation, reducing guest boot time to 12ms for AWS Lambda style workloads.
```

---

### Trial 14: Question `WB_CH_12`

- **Repository:** `cloud-hypervisor/cloud-hypervisor`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_ch_pr_1240`
- **Ground Truth Summary:** Replaced synchronous pread/pwrite thread pools with asynchronous io_uring submission rings, doubling IOPS.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cloud-hypervisor/cloud-hypervisor'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Why did Cloud Hypervisor adopt Linux io_uring for disk virtualization?

Event Stream:
[evt_why_ch_rfc_01] (adr:docs/designs/live-migration.md) Design: Pre-copy Live Migration with Dirty Page Tracking via KVM dirty ring: Status: accepted

Context:
Virtual machine live migration must minimize downtime below 50ms while transferring guest memory under active workloads.

Decision:
Implement iterative pre-copy migration using KVM dirty ring buffer instead of classic user-faultfd or dirty bitmap.

Consequences:
- Drastically reduces lock contention during memory dirty page capture.
- Guest pause time under 35ms on 10GbE
[evt_why_ch_pr_1042] (github_pr:1042) PR #1042: Implement VirtIO Memory Ballooning with Page Reporting: Adds virtio-balloon device supporting automatic unused page reporting back to host hypervisor. Enables dynamic RAM overcommit without guest performance degradation.
[evt_why_ch_issue_890] (github_issue:890) Issue #890: Memory balloon deflation stalls under aggressive host memory pressure: When host demands quick reclamation, balloon thread deadlock occurred due to synchronous locking on memory allocation bus.
[evt_why_ch_rev_c502] (pr_review_comment:c502) Review on PR #1042: Reject synchronous balloon deflation: Synchronous deflation blocks guest vCPUs for up to 400ms. We must reject synchronous balloon worker in favor of asynchronous background worker thread.
[evt_why_ch_rfc_03] (adr:docs/designs/vhost-user-net.md) Design: Vhost-User Network Backend with Multi-Queue Support: Status: accepted

Context:
Standard TAP networking limits packet throughput to ~1.2 Mpps due to kernel context switching overhead.

Decision:
Implement vhost-user-net backend delegating packet processing to DPDK/OVS processes via shared memory queues.

Consequences:
- Achieves line-rate 10GbE throughput (>8 Mpps).
- Eliminates kernel networking path context switches.
[evt_why_ch_rfc_02] (adr:docs/designs/direct-kernel-boot.md) Design: Direct Linux Kernel Boot without Legacy BIOS/GRUB: Status: accepted

Context:
Booting a full SeaBIOS or UEFI image adds 500ms-2s of cold start latency to cloud hypervisor microVMs.

Decision:
Implement direct ELF/bzImage loader jumping straight into the Linux kernel entry point with boot_params setup.

Consequences:
- Sub-30ms VM boot times.
- Eliminates legacy BIOS real-mode emulation code from VMM.
[evt_why_ch_issue_940] (github_issue:940) Issue #940: High guest exit latency on unpinned multi-threaded vCPUs: vCPU threads migrating across NUMA nodes caused up to 300% tail latency jitter on latency-sensitive guest workloads.
[evt_why_ch_pr_1105] (github_pr:1105) PR #1105: CPU Pinning and NUMA Topology Node Binding (Closes #940): Allows operator to pin guest vCPUs to specific host physical cores and bind guest RAM to local host NUMA nodes using libc::sched_setaffinity.
[evt_why_ch_rev_c615] (pr_review_comment:c615) Review on PR #1105: Reject legacy floppy and IDE device emulation: Emulating legacy PC hardware (floppy, IDE, PS/2) contradicts Cloud Hypervisor's minimal attack surface goal. Only modern VirtIO and PCIe interfaces will be supported.
[evt_why_ch_rfc_04] (adr:docs/designs/virtio-fs.md) Design: VirtIO-FS Shared Host Filesystem with Direct Access (DAX) Window: Status: accepted

Context:
Container runtimes (Kata Containers) need efficient sharing of host root filesystems with minimal memory overhead.

Decision:
Support virtio-fs device with a dedicated DAX window mapping host page cache directly into guest physical address space.

Consequences:
- Zero guest page cache memory duplication.
- File reads bypass guest I/O path directly to host cache.
[evt_why_ch_issue_1015] (github_issue:1015) Issue #1015: Host file lock contention in virtio-fs shared directory mounts: Multiple concurrent containers writing to shared virtio-fs directory caused POSIX file lock contention in virtiofsd daemon.
[evt_why_ch_pr_1180] (github_pr:1180) PR #1180: PCIe Root Port Hotplug Support for VirtIO Devices: Adds ACPI PCI hotplug notifications and PCIe native hotplug controller allowing runtime addition and removal of network interfaces and disks.
[evt_why_ch_pr_1240] (github_pr:1240) PR #1240: Asynchronous Disk I/O via Linux io_uring Engine: Replaces threadpool synchronous pread/pwrite with io_uring submission/completion queue rings for virtio-block backend.
[evt_why_ch_rev_c720] (pr_review_comment:c720) Review on PR #1240: Reject unbounded polling loops in vhost worker: Spin-polling io_uring SQPOLL thread pegging 100% CPU on idle guests is prohibited. Eventfd notification must be used when queue is drained.
[evt_why_ch_pr_1312] (github_pr:1312) PR #1312: VFIO PCI Device Passthrough for GPU Workloads: Integrates VFIO Linux kernel API enabling secure hardware DMA remapping and MSI-X interrupt forwarding for dedicated guest GPUs and NVMe drives.
[evt_why_ch_rfc_05] (adr:docs/designs/acpi-ged.md) Design: ACPI Generic Event Device (GED) for System Notifications: Status: accepted

Context:
Handling power button, shutdown, and hotplug interrupts previously required complex proprietary DSDT methods.

Decision:
Adopt ACPI 5.0 Generic Event Device (GED) providing simplified interrupt-driven event signaling across x86_64 and AArch64.

Consequences:
- Unified event dispatch table across architectures.
- Removes ~1,200 lines of architecture-specific AML bytecode.
[evt_why_ch_issue_1120] (github_issue:1120) Issue #1120: Guest memory leak in balloon statistics driver queue: Periodic stat queue buffers allocated by guest kernel were leaked when host neglected to acknowledge polling rings.
[evt_why_ch_pr_1390] (github_pr:1390) PR #1390: MicroVM Minimal Device Tree Profile for Serverless Sandboxes: Configures minimal sandbox VM profile stripping ACPI tables and serial emulation, reducing guest boot time to 12ms for AWS Lambda style workloads.
```

---

### Trial 15: Question `WB_CH_13`

- **Repository:** `cloud-hypervisor/cloud-hypervisor`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `rejected`
- **Expected Evidence Events:** `evt_why_ch_rev_c720`
- **Ground Truth Summary:** Spin-polling consumes 100% host CPU even when guest VM is idle; eventfd notification is required.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cloud-hypervisor/cloud-hypervisor'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Why were spin-polling loops prohibited in io_uring worker threads?

Event Stream:
[evt_why_ch_rfc_01] (adr:docs/designs/live-migration.md) Design: Pre-copy Live Migration with Dirty Page Tracking via KVM dirty ring: Status: accepted

Context:
Virtual machine live migration must minimize downtime below 50ms while transferring guest memory under active workloads.

Decision:
Implement iterative pre-copy migration using KVM dirty ring buffer instead of classic user-faultfd or dirty bitmap.

Consequences:
- Drastically reduces lock contention during memory dirty page capture.
- Guest pause time under 35ms on 10GbE
[evt_why_ch_pr_1042] (github_pr:1042) PR #1042: Implement VirtIO Memory Ballooning with Page Reporting: Adds virtio-balloon device supporting automatic unused page reporting back to host hypervisor. Enables dynamic RAM overcommit without guest performance degradation.
[evt_why_ch_issue_890] (github_issue:890) Issue #890: Memory balloon deflation stalls under aggressive host memory pressure: When host demands quick reclamation, balloon thread deadlock occurred due to synchronous locking on memory allocation bus.
[evt_why_ch_rev_c502] (pr_review_comment:c502) Review on PR #1042: Reject synchronous balloon deflation: Synchronous deflation blocks guest vCPUs for up to 400ms. We must reject synchronous balloon worker in favor of asynchronous background worker thread.
[evt_why_ch_rfc_03] (adr:docs/designs/vhost-user-net.md) Design: Vhost-User Network Backend with Multi-Queue Support: Status: accepted

Context:
Standard TAP networking limits packet throughput to ~1.2 Mpps due to kernel context switching overhead.

Decision:
Implement vhost-user-net backend delegating packet processing to DPDK/OVS processes via shared memory queues.

Consequences:
- Achieves line-rate 10GbE throughput (>8 Mpps).
- Eliminates kernel networking path context switches.
[evt_why_ch_rfc_02] (adr:docs/designs/direct-kernel-boot.md) Design: Direct Linux Kernel Boot without Legacy BIOS/GRUB: Status: accepted

Context:
Booting a full SeaBIOS or UEFI image adds 500ms-2s of cold start latency to cloud hypervisor microVMs.

Decision:
Implement direct ELF/bzImage loader jumping straight into the Linux kernel entry point with boot_params setup.

Consequences:
- Sub-30ms VM boot times.
- Eliminates legacy BIOS real-mode emulation code from VMM.
[evt_why_ch_issue_940] (github_issue:940) Issue #940: High guest exit latency on unpinned multi-threaded vCPUs: vCPU threads migrating across NUMA nodes caused up to 300% tail latency jitter on latency-sensitive guest workloads.
[evt_why_ch_pr_1105] (github_pr:1105) PR #1105: CPU Pinning and NUMA Topology Node Binding (Closes #940): Allows operator to pin guest vCPUs to specific host physical cores and bind guest RAM to local host NUMA nodes using libc::sched_setaffinity.
[evt_why_ch_rev_c615] (pr_review_comment:c615) Review on PR #1105: Reject legacy floppy and IDE device emulation: Emulating legacy PC hardware (floppy, IDE, PS/2) contradicts Cloud Hypervisor's minimal attack surface goal. Only modern VirtIO and PCIe interfaces will be supported.
[evt_why_ch_rfc_04] (adr:docs/designs/virtio-fs.md) Design: VirtIO-FS Shared Host Filesystem with Direct Access (DAX) Window: Status: accepted

Context:
Container runtimes (Kata Containers) need efficient sharing of host root filesystems with minimal memory overhead.

Decision:
Support virtio-fs device with a dedicated DAX window mapping host page cache directly into guest physical address space.

Consequences:
- Zero guest page cache memory duplication.
- File reads bypass guest I/O path directly to host cache.
[evt_why_ch_issue_1015] (github_issue:1015) Issue #1015: Host file lock contention in virtio-fs shared directory mounts: Multiple concurrent containers writing to shared virtio-fs directory caused POSIX file lock contention in virtiofsd daemon.
[evt_why_ch_pr_1180] (github_pr:1180) PR #1180: PCIe Root Port Hotplug Support for VirtIO Devices: Adds ACPI PCI hotplug notifications and PCIe native hotplug controller allowing runtime addition and removal of network interfaces and disks.
[evt_why_ch_pr_1240] (github_pr:1240) PR #1240: Asynchronous Disk I/O via Linux io_uring Engine: Replaces threadpool synchronous pread/pwrite with io_uring submission/completion queue rings for virtio-block backend.
[evt_why_ch_rev_c720] (pr_review_comment:c720) Review on PR #1240: Reject unbounded polling loops in vhost worker: Spin-polling io_uring SQPOLL thread pegging 100% CPU on idle guests is prohibited. Eventfd notification must be used when queue is drained.
[evt_why_ch_pr_1312] (github_pr:1312) PR #1312: VFIO PCI Device Passthrough for GPU Workloads: Integrates VFIO Linux kernel API enabling secure hardware DMA remapping and MSI-X interrupt forwarding for dedicated guest GPUs and NVMe drives.
[evt_why_ch_rfc_05] (adr:docs/designs/acpi-ged.md) Design: ACPI Generic Event Device (GED) for System Notifications: Status: accepted

Context:
Handling power button, shutdown, and hotplug interrupts previously required complex proprietary DSDT methods.

Decision:
Adopt ACPI 5.0 Generic Event Device (GED) providing simplified interrupt-driven event signaling across x86_64 and AArch64.

Consequences:
- Unified event dispatch table across architectures.
- Removes ~1,200 lines of architecture-specific AML bytecode.
[evt_why_ch_issue_1120] (github_issue:1120) Issue #1120: Guest memory leak in balloon statistics driver queue: Periodic stat queue buffers allocated by guest kernel were leaked when host neglected to acknowledge polling rings.
[evt_why_ch_pr_1390] (github_pr:1390) PR #1390: MicroVM Minimal Device Tree Profile for Serverless Sandboxes: Configures minimal sandbox VM profile stripping ACPI tables and serial emulation, reducing guest boot time to 12ms for AWS Lambda style workloads.
```

---

### Trial 16: Question `WB_CH_14`

- **Repository:** `cloud-hypervisor/cloud-hypervisor`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_ch_pr_1312`
- **Ground Truth Summary:** Uses Linux VFIO driver API for hardware IOMMU page table mapping and MSI-X interrupt forwarding.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cloud-hypervisor/cloud-hypervisor'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: How does Cloud Hypervisor provide direct GPU access to guest virtual machines?

Event Stream:
[evt_why_ch_rfc_01] (adr:docs/designs/live-migration.md) Design: Pre-copy Live Migration with Dirty Page Tracking via KVM dirty ring: Status: accepted

Context:
Virtual machine live migration must minimize downtime below 50ms while transferring guest memory under active workloads.

Decision:
Implement iterative pre-copy migration using KVM dirty ring buffer instead of classic user-faultfd or dirty bitmap.

Consequences:
- Drastically reduces lock contention during memory dirty page capture.
- Guest pause time under 35ms on 10GbE
[evt_why_ch_pr_1042] (github_pr:1042) PR #1042: Implement VirtIO Memory Ballooning with Page Reporting: Adds virtio-balloon device supporting automatic unused page reporting back to host hypervisor. Enables dynamic RAM overcommit without guest performance degradation.
[evt_why_ch_issue_890] (github_issue:890) Issue #890: Memory balloon deflation stalls under aggressive host memory pressure: When host demands quick reclamation, balloon thread deadlock occurred due to synchronous locking on memory allocation bus.
[evt_why_ch_rev_c502] (pr_review_comment:c502) Review on PR #1042: Reject synchronous balloon deflation: Synchronous deflation blocks guest vCPUs for up to 400ms. We must reject synchronous balloon worker in favor of asynchronous background worker thread.
[evt_why_ch_rfc_03] (adr:docs/designs/vhost-user-net.md) Design: Vhost-User Network Backend with Multi-Queue Support: Status: accepted

Context:
Standard TAP networking limits packet throughput to ~1.2 Mpps due to kernel context switching overhead.

Decision:
Implement vhost-user-net backend delegating packet processing to DPDK/OVS processes via shared memory queues.

Consequences:
- Achieves line-rate 10GbE throughput (>8 Mpps).
- Eliminates kernel networking path context switches.
[evt_why_ch_rfc_02] (adr:docs/designs/direct-kernel-boot.md) Design: Direct Linux Kernel Boot without Legacy BIOS/GRUB: Status: accepted

Context:
Booting a full SeaBIOS or UEFI image adds 500ms-2s of cold start latency to cloud hypervisor microVMs.

Decision:
Implement direct ELF/bzImage loader jumping straight into the Linux kernel entry point with boot_params setup.

Consequences:
- Sub-30ms VM boot times.
- Eliminates legacy BIOS real-mode emulation code from VMM.
[evt_why_ch_issue_940] (github_issue:940) Issue #940: High guest exit latency on unpinned multi-threaded vCPUs: vCPU threads migrating across NUMA nodes caused up to 300% tail latency jitter on latency-sensitive guest workloads.
[evt_why_ch_pr_1105] (github_pr:1105) PR #1105: CPU Pinning and NUMA Topology Node Binding (Closes #940): Allows operator to pin guest vCPUs to specific host physical cores and bind guest RAM to local host NUMA nodes using libc::sched_setaffinity.
[evt_why_ch_rev_c615] (pr_review_comment:c615) Review on PR #1105: Reject legacy floppy and IDE device emulation: Emulating legacy PC hardware (floppy, IDE, PS/2) contradicts Cloud Hypervisor's minimal attack surface goal. Only modern VirtIO and PCIe interfaces will be supported.
[evt_why_ch_rfc_04] (adr:docs/designs/virtio-fs.md) Design: VirtIO-FS Shared Host Filesystem with Direct Access (DAX) Window: Status: accepted

Context:
Container runtimes (Kata Containers) need efficient sharing of host root filesystems with minimal memory overhead.

Decision:
Support virtio-fs device with a dedicated DAX window mapping host page cache directly into guest physical address space.

Consequences:
- Zero guest page cache memory duplication.
- File reads bypass guest I/O path directly to host cache.
[evt_why_ch_issue_1015] (github_issue:1015) Issue #1015: Host file lock contention in virtio-fs shared directory mounts: Multiple concurrent containers writing to shared virtio-fs directory caused POSIX file lock contention in virtiofsd daemon.
[evt_why_ch_pr_1180] (github_pr:1180) PR #1180: PCIe Root Port Hotplug Support for VirtIO Devices: Adds ACPI PCI hotplug notifications and PCIe native hotplug controller allowing runtime addition and removal of network interfaces and disks.
[evt_why_ch_pr_1240] (github_pr:1240) PR #1240: Asynchronous Disk I/O via Linux io_uring Engine: Replaces threadpool synchronous pread/pwrite with io_uring submission/completion queue rings for virtio-block backend.
[evt_why_ch_rev_c720] (pr_review_comment:c720) Review on PR #1240: Reject unbounded polling loops in vhost worker: Spin-polling io_uring SQPOLL thread pegging 100% CPU on idle guests is prohibited. Eventfd notification must be used when queue is drained.
[evt_why_ch_pr_1312] (github_pr:1312) PR #1312: VFIO PCI Device Passthrough for GPU Workloads: Integrates VFIO Linux kernel API enabling secure hardware DMA remapping and MSI-X interrupt forwarding for dedicated guest GPUs and NVMe drives.
[evt_why_ch_rfc_05] (adr:docs/designs/acpi-ged.md) Design: ACPI Generic Event Device (GED) for System Notifications: Status: accepted

Context:
Handling power button, shutdown, and hotplug interrupts previously required complex proprietary DSDT methods.

Decision:
Adopt ACPI 5.0 Generic Event Device (GED) providing simplified interrupt-driven event signaling across x86_64 and AArch64.

Consequences:
- Unified event dispatch table across architectures.
- Removes ~1,200 lines of architecture-specific AML bytecode.
[evt_why_ch_issue_1120] (github_issue:1120) Issue #1120: Guest memory leak in balloon statistics driver queue: Periodic stat queue buffers allocated by guest kernel were leaked when host neglected to acknowledge polling rings.
[evt_why_ch_pr_1390] (github_pr:1390) PR #1390: MicroVM Minimal Device Tree Profile for Serverless Sandboxes: Configures minimal sandbox VM profile stripping ACPI tables and serial emulation, reducing guest boot time to 12ms for AWS Lambda style workloads.
```

---

### Trial 17: Question `WB_CH_15`

- **Repository:** `cloud-hypervisor/cloud-hypervisor`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_ch_rfc_05`
- **Ground Truth Summary:** Unifies event dispatching across x86_64 and AArch64 and removes 1,200 lines of architecture-specific AML bytecode.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cloud-hypervisor/cloud-hypervisor'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Why did Cloud Hypervisor adopt the ACPI Generic Event Device (GED)?

Event Stream:
[evt_why_ch_rfc_01] (adr:docs/designs/live-migration.md) Design: Pre-copy Live Migration with Dirty Page Tracking via KVM dirty ring: Status: accepted

Context:
Virtual machine live migration must minimize downtime below 50ms while transferring guest memory under active workloads.

Decision:
Implement iterative pre-copy migration using KVM dirty ring buffer instead of classic user-faultfd or dirty bitmap.

Consequences:
- Drastically reduces lock contention during memory dirty page capture.
- Guest pause time under 35ms on 10GbE
[evt_why_ch_pr_1042] (github_pr:1042) PR #1042: Implement VirtIO Memory Ballooning with Page Reporting: Adds virtio-balloon device supporting automatic unused page reporting back to host hypervisor. Enables dynamic RAM overcommit without guest performance degradation.
[evt_why_ch_issue_890] (github_issue:890) Issue #890: Memory balloon deflation stalls under aggressive host memory pressure: When host demands quick reclamation, balloon thread deadlock occurred due to synchronous locking on memory allocation bus.
[evt_why_ch_rev_c502] (pr_review_comment:c502) Review on PR #1042: Reject synchronous balloon deflation: Synchronous deflation blocks guest vCPUs for up to 400ms. We must reject synchronous balloon worker in favor of asynchronous background worker thread.
[evt_why_ch_rfc_03] (adr:docs/designs/vhost-user-net.md) Design: Vhost-User Network Backend with Multi-Queue Support: Status: accepted

Context:
Standard TAP networking limits packet throughput to ~1.2 Mpps due to kernel context switching overhead.

Decision:
Implement vhost-user-net backend delegating packet processing to DPDK/OVS processes via shared memory queues.

Consequences:
- Achieves line-rate 10GbE throughput (>8 Mpps).
- Eliminates kernel networking path context switches.
[evt_why_ch_rfc_02] (adr:docs/designs/direct-kernel-boot.md) Design: Direct Linux Kernel Boot without Legacy BIOS/GRUB: Status: accepted

Context:
Booting a full SeaBIOS or UEFI image adds 500ms-2s of cold start latency to cloud hypervisor microVMs.

Decision:
Implement direct ELF/bzImage loader jumping straight into the Linux kernel entry point with boot_params setup.

Consequences:
- Sub-30ms VM boot times.
- Eliminates legacy BIOS real-mode emulation code from VMM.
[evt_why_ch_issue_940] (github_issue:940) Issue #940: High guest exit latency on unpinned multi-threaded vCPUs: vCPU threads migrating across NUMA nodes caused up to 300% tail latency jitter on latency-sensitive guest workloads.
[evt_why_ch_pr_1105] (github_pr:1105) PR #1105: CPU Pinning and NUMA Topology Node Binding (Closes #940): Allows operator to pin guest vCPUs to specific host physical cores and bind guest RAM to local host NUMA nodes using libc::sched_setaffinity.
[evt_why_ch_rev_c615] (pr_review_comment:c615) Review on PR #1105: Reject legacy floppy and IDE device emulation: Emulating legacy PC hardware (floppy, IDE, PS/2) contradicts Cloud Hypervisor's minimal attack surface goal. Only modern VirtIO and PCIe interfaces will be supported.
[evt_why_ch_rfc_04] (adr:docs/designs/virtio-fs.md) Design: VirtIO-FS Shared Host Filesystem with Direct Access (DAX) Window: Status: accepted

Context:
Container runtimes (Kata Containers) need efficient sharing of host root filesystems with minimal memory overhead.

Decision:
Support virtio-fs device with a dedicated DAX window mapping host page cache directly into guest physical address space.

Consequences:
- Zero guest page cache memory duplication.
- File reads bypass guest I/O path directly to host cache.
[evt_why_ch_issue_1015] (github_issue:1015) Issue #1015: Host file lock contention in virtio-fs shared directory mounts: Multiple concurrent containers writing to shared virtio-fs directory caused POSIX file lock contention in virtiofsd daemon.
[evt_why_ch_pr_1180] (github_pr:1180) PR #1180: PCIe Root Port Hotplug Support for VirtIO Devices: Adds ACPI PCI hotplug notifications and PCIe native hotplug controller allowing runtime addition and removal of network interfaces and disks.
[evt_why_ch_pr_1240] (github_pr:1240) PR #1240: Asynchronous Disk I/O via Linux io_uring Engine: Replaces threadpool synchronous pread/pwrite with io_uring submission/completion queue rings for virtio-block backend.
[evt_why_ch_rev_c720] (pr_review_comment:c720) Review on PR #1240: Reject unbounded polling loops in vhost worker: Spin-polling io_uring SQPOLL thread pegging 100% CPU on idle guests is prohibited. Eventfd notification must be used when queue is drained.
[evt_why_ch_pr_1312] (github_pr:1312) PR #1312: VFIO PCI Device Passthrough for GPU Workloads: Integrates VFIO Linux kernel API enabling secure hardware DMA remapping and MSI-X interrupt forwarding for dedicated guest GPUs and NVMe drives.
[evt_why_ch_rfc_05] (adr:docs/designs/acpi-ged.md) Design: ACPI Generic Event Device (GED) for System Notifications: Status: accepted

Context:
Handling power button, shutdown, and hotplug interrupts previously required complex proprietary DSDT methods.

Decision:
Adopt ACPI 5.0 Generic Event Device (GED) providing simplified interrupt-driven event signaling across x86_64 and AArch64.

Consequences:
- Unified event dispatch table across architectures.
- Removes ~1,200 lines of architecture-specific AML bytecode.
[evt_why_ch_issue_1120] (github_issue:1120) Issue #1120: Guest memory leak in balloon statistics driver queue: Periodic stat queue buffers allocated by guest kernel were leaked when host neglected to acknowledge polling rings.
[evt_why_ch_pr_1390] (github_pr:1390) PR #1390: MicroVM Minimal Device Tree Profile for Serverless Sandboxes: Configures minimal sandbox VM profile stripping ACPI tables and serial emulation, reducing guest boot time to 12ms for AWS Lambda style workloads.
```

---

### Trial 18: Question `WB_CH_16`

- **Repository:** `cloud-hypervisor/cloud-hypervisor`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_ch_pr_1390`
- **Ground Truth Summary:** Strips ACPI tables and serial console emulation, configuring minimal device tree representation.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cloud-hypervisor/cloud-hypervisor'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: How does the microVM profile achieve 12ms cold boot for serverless sandboxes?

Event Stream:
[evt_why_ch_rfc_01] (adr:docs/designs/live-migration.md) Design: Pre-copy Live Migration with Dirty Page Tracking via KVM dirty ring: Status: accepted

Context:
Virtual machine live migration must minimize downtime below 50ms while transferring guest memory under active workloads.

Decision:
Implement iterative pre-copy migration using KVM dirty ring buffer instead of classic user-faultfd or dirty bitmap.

Consequences:
- Drastically reduces lock contention during memory dirty page capture.
- Guest pause time under 35ms on 10GbE
[evt_why_ch_pr_1042] (github_pr:1042) PR #1042: Implement VirtIO Memory Ballooning with Page Reporting: Adds virtio-balloon device supporting automatic unused page reporting back to host hypervisor. Enables dynamic RAM overcommit without guest performance degradation.
[evt_why_ch_issue_890] (github_issue:890) Issue #890: Memory balloon deflation stalls under aggressive host memory pressure: When host demands quick reclamation, balloon thread deadlock occurred due to synchronous locking on memory allocation bus.
[evt_why_ch_rev_c502] (pr_review_comment:c502) Review on PR #1042: Reject synchronous balloon deflation: Synchronous deflation blocks guest vCPUs for up to 400ms. We must reject synchronous balloon worker in favor of asynchronous background worker thread.
[evt_why_ch_rfc_03] (adr:docs/designs/vhost-user-net.md) Design: Vhost-User Network Backend with Multi-Queue Support: Status: accepted

Context:
Standard TAP networking limits packet throughput to ~1.2 Mpps due to kernel context switching overhead.

Decision:
Implement vhost-user-net backend delegating packet processing to DPDK/OVS processes via shared memory queues.

Consequences:
- Achieves line-rate 10GbE throughput (>8 Mpps).
- Eliminates kernel networking path context switches.
[evt_why_ch_rfc_02] (adr:docs/designs/direct-kernel-boot.md) Design: Direct Linux Kernel Boot without Legacy BIOS/GRUB: Status: accepted

Context:
Booting a full SeaBIOS or UEFI image adds 500ms-2s of cold start latency to cloud hypervisor microVMs.

Decision:
Implement direct ELF/bzImage loader jumping straight into the Linux kernel entry point with boot_params setup.

Consequences:
- Sub-30ms VM boot times.
- Eliminates legacy BIOS real-mode emulation code from VMM.
[evt_why_ch_issue_940] (github_issue:940) Issue #940: High guest exit latency on unpinned multi-threaded vCPUs: vCPU threads migrating across NUMA nodes caused up to 300% tail latency jitter on latency-sensitive guest workloads.
[evt_why_ch_pr_1105] (github_pr:1105) PR #1105: CPU Pinning and NUMA Topology Node Binding (Closes #940): Allows operator to pin guest vCPUs to specific host physical cores and bind guest RAM to local host NUMA nodes using libc::sched_setaffinity.
[evt_why_ch_rev_c615] (pr_review_comment:c615) Review on PR #1105: Reject legacy floppy and IDE device emulation: Emulating legacy PC hardware (floppy, IDE, PS/2) contradicts Cloud Hypervisor's minimal attack surface goal. Only modern VirtIO and PCIe interfaces will be supported.
[evt_why_ch_rfc_04] (adr:docs/designs/virtio-fs.md) Design: VirtIO-FS Shared Host Filesystem with Direct Access (DAX) Window: Status: accepted

Context:
Container runtimes (Kata Containers) need efficient sharing of host root filesystems with minimal memory overhead.

Decision:
Support virtio-fs device with a dedicated DAX window mapping host page cache directly into guest physical address space.

Consequences:
- Zero guest page cache memory duplication.
- File reads bypass guest I/O path directly to host cache.
[evt_why_ch_issue_1015] (github_issue:1015) Issue #1015: Host file lock contention in virtio-fs shared directory mounts: Multiple concurrent containers writing to shared virtio-fs directory caused POSIX file lock contention in virtiofsd daemon.
[evt_why_ch_pr_1180] (github_pr:1180) PR #1180: PCIe Root Port Hotplug Support for VirtIO Devices: Adds ACPI PCI hotplug notifications and PCIe native hotplug controller allowing runtime addition and removal of network interfaces and disks.
[evt_why_ch_pr_1240] (github_pr:1240) PR #1240: Asynchronous Disk I/O via Linux io_uring Engine: Replaces threadpool synchronous pread/pwrite with io_uring submission/completion queue rings for virtio-block backend.
[evt_why_ch_rev_c720] (pr_review_comment:c720) Review on PR #1240: Reject unbounded polling loops in vhost worker: Spin-polling io_uring SQPOLL thread pegging 100% CPU on idle guests is prohibited. Eventfd notification must be used when queue is drained.
[evt_why_ch_pr_1312] (github_pr:1312) PR #1312: VFIO PCI Device Passthrough for GPU Workloads: Integrates VFIO Linux kernel API enabling secure hardware DMA remapping and MSI-X interrupt forwarding for dedicated guest GPUs and NVMe drives.
[evt_why_ch_rfc_05] (adr:docs/designs/acpi-ged.md) Design: ACPI Generic Event Device (GED) for System Notifications: Status: accepted

Context:
Handling power button, shutdown, and hotplug interrupts previously required complex proprietary DSDT methods.

Decision:
Adopt ACPI 5.0 Generic Event Device (GED) providing simplified interrupt-driven event signaling across x86_64 and AArch64.

Consequences:
- Unified event dispatch table across architectures.
- Removes ~1,200 lines of architecture-specific AML bytecode.
[evt_why_ch_issue_1120] (github_issue:1120) Issue #1120: Guest memory leak in balloon statistics driver queue: Periodic stat queue buffers allocated by guest kernel were leaked when host neglected to acknowledge polling rings.
[evt_why_ch_pr_1390] (github_pr:1390) PR #1390: MicroVM Minimal Device Tree Profile for Serverless Sandboxes: Configures minimal sandbox VM profile stripping ACPI tables and serial emulation, reducing guest boot time to 12ms for AWS Lambda style workloads.
```

---

### Trial 19: Question `WB_CLI_09`

- **Repository:** `cli/cli`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `rejected`
- **Expected Evidence Events:** `evt_why_cli_rev_c712`
- **Ground Truth Summary:** Go plugins require exact compiler and ABI matching and do not isolate process memory; child fork-exec isolation is required.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cli/cli'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Why was executing extensions via Go dynamic plugin packages rejected?

Event Stream:
[evt_why_cli_rfc_01] (adr:docs/rfc/001-keyring-credentials.md) RFC 001: Secure OAuth Token Storage using Native OS Keyrings: Status: accepted

Context:
Storing GitHub OAuth tokens in plaintext YAML config files (~/.config/gh/hosts.yml) leaves developer credentials vulnerable to unauthorized local processes.

Decision:
Integrate native OS keychain/keyring providers (macOS Keychain, Windows Credential Manager, Linux SecretService) as default secure token storage.

Consequences:
- Zero plaintext credential storage on disk.
[evt_why_cli_issue_412] (github_issue:412) Issue #412: Plaintext tokens exposed in process environment variables and config files: Security audit noted that gh auth login stores tokens in world-readable ~/.config/gh/config.yml. Keyring integration requested.
[evt_why_cli_pr_518] (github_pr:518) PR #518: Add zalando/go-keyring provider for auth token persistence (Closes #412): Implements RFC 001. Migrates token storage to native OS keychain with graceful fallback to file store.
[evt_why_cli_rev_c601] (pr_review_comment:c601) Review on PR #518: Reject custom symmetric encryption key on disk: Custom symmetric key encryption stored next to the ciphertext offers zero additional security. We must use OS-level protected credentials.
[evt_why_cli_rfc_03] (adr:docs/rfc/003-extension-isolation.md) RFC 003: Subprocess Extension Execution Model with Scoped Token Environment: Status: accepted

Context:
Executing third-party gh extensions inside the main process runtime risks memory contamination and uncontrolled privilege escalation.

Decision:
Execute extensions as isolated external child subprocesses communicating via standard input/output with stripped environment variables.

Consequences:
- Protects host CLI process memory.
- Prevents extension crashes from termina
[evt_why_cli_rfc_02] (adr:docs/rfc/002-graphql-query-batching.md) RFC 002: GraphQL Query Batching and Fragment Reuse for Repositories: Status: accepted

Context:
Listing 30 pull requests previously executed 30 separate REST requests to fetch review statuses, causing high latency and rate limit depletion.

Decision:
Consolidate GitHub API access through GraphQL queries using reusable fragments and connection paging.

Consequences:
- Latency reduced from 3.2s to 420ms for PR lists.
- Single API call quota unit consumed per page.
[evt_why_cli_issue_480] (github_issue:480) Issue #480: N+1 REST API roundtrips during repo list with pull requests: Running gh pr list on repositories with extensive checks resulted in secondary API queries per line item exceeding the 5,000 req/hr rate limit.
[evt_why_cli_pr_592] (github_pr:592) PR #592: Batch repository and issue queries using GraphQL fragments (Closes #480): Implements RFC 002. Replaces REST loops with single paginated GraphQL queries fetching comments, reviews, and status rollups in one payload.
[evt_why_cli_issue_550] (github_issue:550) Issue #550: Extension crash corrupts parent terminal state and escapes PATH: Extensions invoking raw exec commands leaked file descriptors and left raw terminal mode active on fatal signal crashes.
[evt_why_cli_pr_670] (github_pr:670) PR #670: Fork-exec child subprocess isolation with restricted inherited env for extensions (Closes #550): Implements RFC 003. Child process manager cleans up terminal modes on SIGINT/SIGTERM and restricts PATH lookup to extension directory.
[evt_why_cli_rev_c712] (pr_review_comment:c712) Review on PR #670: Reject executing third-party extensions via in-process Go plugins: Go dynamic plugin loading requires exact compiler and dependency ABI matches and allows arbitrary memory access. External subprocess isolation is non-negotiable.
[evt_why_cli_rfc_04] (adr:docs/rfc/004-termenv-formatting.md) RFC 004: Terminal Color and Hyperlink Detection via termenv: Status: accepted

Context:
Hardcoded ANSI escape codes corrupted tabular output when piping to external commands (grep, awk, jq) or running in CI logs.

Decision:
Use termenv library to inspect terminal color profile, automatically stripping styling when stdout is not a TTY or NO_COLOR is set.

Consequences:
- Clean machine-readable output in scripts.
- Rich interactive color and OSC 8 hyperlinks 
[evt_why_cli_issue_620] (github_issue:620) Issue #620: Broken ANSI escape sequences when piping gh output to jq and grep: Users scripting gh pr list | jq . experienced JSON syntax errors because color escape sequences were embedded inside fields.
[evt_why_cli_pr_735] (github_pr:735) PR #735: Auto-detect TTY and disable ANSI formatting in non-interactive pipelines (Closes #620): Implements RFC 004. Replaces hardcoded escape codes with IOStreams ColorEnabled check and respects CLICOLOR / NO_COLOR standard env vars.
[evt_why_cli_rfc_05] (adr:docs/rfc/005-git-credential-helper.md) RFC 005: Git Credential Helper Protocol Provider: Status: accepted

Context:
Users running git clone after authenticating via gh auth login were prompted again by Git for their username and password.

Decision:
Implement gh auth git-credential command implementing the standard Git credential helper protocol responding to get, store, and erase.

Consequences:
- Transparent authentication for all git operations.
- Reuses secure OAuth token stored i
[evt_why_cli_pr_810] (github_pr:810) PR #810: Implementation of gh auth git-credential helper protocol: Implements RFC 005. Configures git credential helper entry in global .gitconfig during gh auth login setup.
[evt_why_cli_rev_c840] (pr_review_comment:c840) Review on PR #810: Reject global auth token in HTTP GET query string: Passing tokens in URL query parameters exposes them in web server access logs and proxy history. All authentication must strictly use Authorization: Bearer HTTP header.
[evt_why_cli_issue_780] (github_issue:780) Issue #780: Browser open failure in headless SSH and cloud container environments: Running gh auth login on remote headless EC2 instances hung indefinitely attempting to open xdg-open desktop browser.
[evt_why_cli_pr_920] (github_pr:920) PR #920: OAuth Device Code flow fallback for headless SSH sessions (Closes #780): Detects lack of display server or SSH session and displays 8-digit one-time device code with github.com/login/device URL for secondary device authentication.
```

---

### Trial 20: Question `WB_CLI_10`

- **Repository:** `cli/cli`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_cli_pr_670, evt_why_cli_issue_550`
- **Ground Truth Summary:** Restricts inherited environment variables, strips sensitive tokens, and bounds PATH lookups to extension install directory.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cli/cli'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: How does GitHub CLI isolate extension subprocess execution environment?

Event Stream:
[evt_why_cli_rfc_01] (adr:docs/rfc/001-keyring-credentials.md) RFC 001: Secure OAuth Token Storage using Native OS Keyrings: Status: accepted

Context:
Storing GitHub OAuth tokens in plaintext YAML config files (~/.config/gh/hosts.yml) leaves developer credentials vulnerable to unauthorized local processes.

Decision:
Integrate native OS keychain/keyring providers (macOS Keychain, Windows Credential Manager, Linux SecretService) as default secure token storage.

Consequences:
- Zero plaintext credential storage on disk.
[evt_why_cli_issue_412] (github_issue:412) Issue #412: Plaintext tokens exposed in process environment variables and config files: Security audit noted that gh auth login stores tokens in world-readable ~/.config/gh/config.yml. Keyring integration requested.
[evt_why_cli_pr_518] (github_pr:518) PR #518: Add zalando/go-keyring provider for auth token persistence (Closes #412): Implements RFC 001. Migrates token storage to native OS keychain with graceful fallback to file store.
[evt_why_cli_rev_c601] (pr_review_comment:c601) Review on PR #518: Reject custom symmetric encryption key on disk: Custom symmetric key encryption stored next to the ciphertext offers zero additional security. We must use OS-level protected credentials.
[evt_why_cli_rfc_03] (adr:docs/rfc/003-extension-isolation.md) RFC 003: Subprocess Extension Execution Model with Scoped Token Environment: Status: accepted

Context:
Executing third-party gh extensions inside the main process runtime risks memory contamination and uncontrolled privilege escalation.

Decision:
Execute extensions as isolated external child subprocesses communicating via standard input/output with stripped environment variables.

Consequences:
- Protects host CLI process memory.
- Prevents extension crashes from termina
[evt_why_cli_rfc_02] (adr:docs/rfc/002-graphql-query-batching.md) RFC 002: GraphQL Query Batching and Fragment Reuse for Repositories: Status: accepted

Context:
Listing 30 pull requests previously executed 30 separate REST requests to fetch review statuses, causing high latency and rate limit depletion.

Decision:
Consolidate GitHub API access through GraphQL queries using reusable fragments and connection paging.

Consequences:
- Latency reduced from 3.2s to 420ms for PR lists.
- Single API call quota unit consumed per page.
[evt_why_cli_issue_480] (github_issue:480) Issue #480: N+1 REST API roundtrips during repo list with pull requests: Running gh pr list on repositories with extensive checks resulted in secondary API queries per line item exceeding the 5,000 req/hr rate limit.
[evt_why_cli_pr_592] (github_pr:592) PR #592: Batch repository and issue queries using GraphQL fragments (Closes #480): Implements RFC 002. Replaces REST loops with single paginated GraphQL queries fetching comments, reviews, and status rollups in one payload.
[evt_why_cli_issue_550] (github_issue:550) Issue #550: Extension crash corrupts parent terminal state and escapes PATH: Extensions invoking raw exec commands leaked file descriptors and left raw terminal mode active on fatal signal crashes.
[evt_why_cli_pr_670] (github_pr:670) PR #670: Fork-exec child subprocess isolation with restricted inherited env for extensions (Closes #550): Implements RFC 003. Child process manager cleans up terminal modes on SIGINT/SIGTERM and restricts PATH lookup to extension directory.
[evt_why_cli_rev_c712] (pr_review_comment:c712) Review on PR #670: Reject executing third-party extensions via in-process Go plugins: Go dynamic plugin loading requires exact compiler and dependency ABI matches and allows arbitrary memory access. External subprocess isolation is non-negotiable.
[evt_why_cli_rfc_04] (adr:docs/rfc/004-termenv-formatting.md) RFC 004: Terminal Color and Hyperlink Detection via termenv: Status: accepted

Context:
Hardcoded ANSI escape codes corrupted tabular output when piping to external commands (grep, awk, jq) or running in CI logs.

Decision:
Use termenv library to inspect terminal color profile, automatically stripping styling when stdout is not a TTY or NO_COLOR is set.

Consequences:
- Clean machine-readable output in scripts.
- Rich interactive color and OSC 8 hyperlinks 
[evt_why_cli_issue_620] (github_issue:620) Issue #620: Broken ANSI escape sequences when piping gh output to jq and grep: Users scripting gh pr list | jq . experienced JSON syntax errors because color escape sequences were embedded inside fields.
[evt_why_cli_pr_735] (github_pr:735) PR #735: Auto-detect TTY and disable ANSI formatting in non-interactive pipelines (Closes #620): Implements RFC 004. Replaces hardcoded escape codes with IOStreams ColorEnabled check and respects CLICOLOR / NO_COLOR standard env vars.
[evt_why_cli_rfc_05] (adr:docs/rfc/005-git-credential-helper.md) RFC 005: Git Credential Helper Protocol Provider: Status: accepted

Context:
Users running git clone after authenticating via gh auth login were prompted again by Git for their username and password.

Decision:
Implement gh auth git-credential command implementing the standard Git credential helper protocol responding to get, store, and erase.

Consequences:
- Transparent authentication for all git operations.
- Reuses secure OAuth token stored i
[evt_why_cli_pr_810] (github_pr:810) PR #810: Implementation of gh auth git-credential helper protocol: Implements RFC 005. Configures git credential helper entry in global .gitconfig during gh auth login setup.
[evt_why_cli_rev_c840] (pr_review_comment:c840) Review on PR #810: Reject global auth token in HTTP GET query string: Passing tokens in URL query parameters exposes them in web server access logs and proxy history. All authentication must strictly use Authorization: Bearer HTTP header.
[evt_why_cli_issue_780] (github_issue:780) Issue #780: Browser open failure in headless SSH and cloud container environments: Running gh auth login on remote headless EC2 instances hung indefinitely attempting to open xdg-open desktop browser.
[evt_why_cli_pr_920] (github_pr:920) PR #920: OAuth Device Code flow fallback for headless SSH sessions (Closes #780): Detects lack of display server or SSH session and displays 8-digit one-time device code with github.com/login/device URL for secondary device authentication.
```

---

### Trial 21: Question `WB_CLI_11`

- **Repository:** `cli/cli`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_cli_rfc_04`
- **Ground Truth Summary:** Provides automated TTY inspection and strips ANSI formatting when stdout is piped to tools or when NO_COLOR is active.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cli/cli'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Why did GitHub CLI adopt termenv for terminal formatting?

Event Stream:
[evt_why_cli_rfc_01] (adr:docs/rfc/001-keyring-credentials.md) RFC 001: Secure OAuth Token Storage using Native OS Keyrings: Status: accepted

Context:
Storing GitHub OAuth tokens in plaintext YAML config files (~/.config/gh/hosts.yml) leaves developer credentials vulnerable to unauthorized local processes.

Decision:
Integrate native OS keychain/keyring providers (macOS Keychain, Windows Credential Manager, Linux SecretService) as default secure token storage.

Consequences:
- Zero plaintext credential storage on disk.
[evt_why_cli_issue_412] (github_issue:412) Issue #412: Plaintext tokens exposed in process environment variables and config files: Security audit noted that gh auth login stores tokens in world-readable ~/.config/gh/config.yml. Keyring integration requested.
[evt_why_cli_pr_518] (github_pr:518) PR #518: Add zalando/go-keyring provider for auth token persistence (Closes #412): Implements RFC 001. Migrates token storage to native OS keychain with graceful fallback to file store.
[evt_why_cli_rev_c601] (pr_review_comment:c601) Review on PR #518: Reject custom symmetric encryption key on disk: Custom symmetric key encryption stored next to the ciphertext offers zero additional security. We must use OS-level protected credentials.
[evt_why_cli_rfc_03] (adr:docs/rfc/003-extension-isolation.md) RFC 003: Subprocess Extension Execution Model with Scoped Token Environment: Status: accepted

Context:
Executing third-party gh extensions inside the main process runtime risks memory contamination and uncontrolled privilege escalation.

Decision:
Execute extensions as isolated external child subprocesses communicating via standard input/output with stripped environment variables.

Consequences:
- Protects host CLI process memory.
- Prevents extension crashes from termina
[evt_why_cli_rfc_02] (adr:docs/rfc/002-graphql-query-batching.md) RFC 002: GraphQL Query Batching and Fragment Reuse for Repositories: Status: accepted

Context:
Listing 30 pull requests previously executed 30 separate REST requests to fetch review statuses, causing high latency and rate limit depletion.

Decision:
Consolidate GitHub API access through GraphQL queries using reusable fragments and connection paging.

Consequences:
- Latency reduced from 3.2s to 420ms for PR lists.
- Single API call quota unit consumed per page.
[evt_why_cli_issue_480] (github_issue:480) Issue #480: N+1 REST API roundtrips during repo list with pull requests: Running gh pr list on repositories with extensive checks resulted in secondary API queries per line item exceeding the 5,000 req/hr rate limit.
[evt_why_cli_pr_592] (github_pr:592) PR #592: Batch repository and issue queries using GraphQL fragments (Closes #480): Implements RFC 002. Replaces REST loops with single paginated GraphQL queries fetching comments, reviews, and status rollups in one payload.
[evt_why_cli_issue_550] (github_issue:550) Issue #550: Extension crash corrupts parent terminal state and escapes PATH: Extensions invoking raw exec commands leaked file descriptors and left raw terminal mode active on fatal signal crashes.
[evt_why_cli_pr_670] (github_pr:670) PR #670: Fork-exec child subprocess isolation with restricted inherited env for extensions (Closes #550): Implements RFC 003. Child process manager cleans up terminal modes on SIGINT/SIGTERM and restricts PATH lookup to extension directory.
[evt_why_cli_rev_c712] (pr_review_comment:c712) Review on PR #670: Reject executing third-party extensions via in-process Go plugins: Go dynamic plugin loading requires exact compiler and dependency ABI matches and allows arbitrary memory access. External subprocess isolation is non-negotiable.
[evt_why_cli_rfc_04] (adr:docs/rfc/004-termenv-formatting.md) RFC 004: Terminal Color and Hyperlink Detection via termenv: Status: accepted

Context:
Hardcoded ANSI escape codes corrupted tabular output when piping to external commands (grep, awk, jq) or running in CI logs.

Decision:
Use termenv library to inspect terminal color profile, automatically stripping styling when stdout is not a TTY or NO_COLOR is set.

Consequences:
- Clean machine-readable output in scripts.
- Rich interactive color and OSC 8 hyperlinks 
[evt_why_cli_issue_620] (github_issue:620) Issue #620: Broken ANSI escape sequences when piping gh output to jq and grep: Users scripting gh pr list | jq . experienced JSON syntax errors because color escape sequences were embedded inside fields.
[evt_why_cli_pr_735] (github_pr:735) PR #735: Auto-detect TTY and disable ANSI formatting in non-interactive pipelines (Closes #620): Implements RFC 004. Replaces hardcoded escape codes with IOStreams ColorEnabled check and respects CLICOLOR / NO_COLOR standard env vars.
[evt_why_cli_rfc_05] (adr:docs/rfc/005-git-credential-helper.md) RFC 005: Git Credential Helper Protocol Provider: Status: accepted

Context:
Users running git clone after authenticating via gh auth login were prompted again by Git for their username and password.

Decision:
Implement gh auth git-credential command implementing the standard Git credential helper protocol responding to get, store, and erase.

Consequences:
- Transparent authentication for all git operations.
- Reuses secure OAuth token stored i
[evt_why_cli_pr_810] (github_pr:810) PR #810: Implementation of gh auth git-credential helper protocol: Implements RFC 005. Configures git credential helper entry in global .gitconfig during gh auth login setup.
[evt_why_cli_rev_c840] (pr_review_comment:c840) Review on PR #810: Reject global auth token in HTTP GET query string: Passing tokens in URL query parameters exposes them in web server access logs and proxy history. All authentication must strictly use Authorization: Bearer HTTP header.
[evt_why_cli_issue_780] (github_issue:780) Issue #780: Browser open failure in headless SSH and cloud container environments: Running gh auth login on remote headless EC2 instances hung indefinitely attempting to open xdg-open desktop browser.
[evt_why_cli_pr_920] (github_pr:920) PR #920: OAuth Device Code flow fallback for headless SSH sessions (Closes #780): Detects lack of display server or SSH session and displays 8-digit one-time device code with github.com/login/device URL for secondary device authentication.
```

---

### Trial 22: Question `WB_CLI_12`

- **Repository:** `cli/cli`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_cli_pr_735, evt_why_cli_issue_620`
- **Ground Truth Summary:** Integrated IOStreams ColorEnabled check auto-disabling colors when stdout is not connected to an interactive terminal.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cli/cli'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: How was ANSI escape sequence corruption resolved in Unix pipelines?

Event Stream:
[evt_why_cli_rfc_01] (adr:docs/rfc/001-keyring-credentials.md) RFC 001: Secure OAuth Token Storage using Native OS Keyrings: Status: accepted

Context:
Storing GitHub OAuth tokens in plaintext YAML config files (~/.config/gh/hosts.yml) leaves developer credentials vulnerable to unauthorized local processes.

Decision:
Integrate native OS keychain/keyring providers (macOS Keychain, Windows Credential Manager, Linux SecretService) as default secure token storage.

Consequences:
- Zero plaintext credential storage on disk.
[evt_why_cli_issue_412] (github_issue:412) Issue #412: Plaintext tokens exposed in process environment variables and config files: Security audit noted that gh auth login stores tokens in world-readable ~/.config/gh/config.yml. Keyring integration requested.
[evt_why_cli_pr_518] (github_pr:518) PR #518: Add zalando/go-keyring provider for auth token persistence (Closes #412): Implements RFC 001. Migrates token storage to native OS keychain with graceful fallback to file store.
[evt_why_cli_rev_c601] (pr_review_comment:c601) Review on PR #518: Reject custom symmetric encryption key on disk: Custom symmetric key encryption stored next to the ciphertext offers zero additional security. We must use OS-level protected credentials.
[evt_why_cli_rfc_03] (adr:docs/rfc/003-extension-isolation.md) RFC 003: Subprocess Extension Execution Model with Scoped Token Environment: Status: accepted

Context:
Executing third-party gh extensions inside the main process runtime risks memory contamination and uncontrolled privilege escalation.

Decision:
Execute extensions as isolated external child subprocesses communicating via standard input/output with stripped environment variables.

Consequences:
- Protects host CLI process memory.
- Prevents extension crashes from termina
[evt_why_cli_rfc_02] (adr:docs/rfc/002-graphql-query-batching.md) RFC 002: GraphQL Query Batching and Fragment Reuse for Repositories: Status: accepted

Context:
Listing 30 pull requests previously executed 30 separate REST requests to fetch review statuses, causing high latency and rate limit depletion.

Decision:
Consolidate GitHub API access through GraphQL queries using reusable fragments and connection paging.

Consequences:
- Latency reduced from 3.2s to 420ms for PR lists.
- Single API call quota unit consumed per page.
[evt_why_cli_issue_480] (github_issue:480) Issue #480: N+1 REST API roundtrips during repo list with pull requests: Running gh pr list on repositories with extensive checks resulted in secondary API queries per line item exceeding the 5,000 req/hr rate limit.
[evt_why_cli_pr_592] (github_pr:592) PR #592: Batch repository and issue queries using GraphQL fragments (Closes #480): Implements RFC 002. Replaces REST loops with single paginated GraphQL queries fetching comments, reviews, and status rollups in one payload.
[evt_why_cli_issue_550] (github_issue:550) Issue #550: Extension crash corrupts parent terminal state and escapes PATH: Extensions invoking raw exec commands leaked file descriptors and left raw terminal mode active on fatal signal crashes.
[evt_why_cli_pr_670] (github_pr:670) PR #670: Fork-exec child subprocess isolation with restricted inherited env for extensions (Closes #550): Implements RFC 003. Child process manager cleans up terminal modes on SIGINT/SIGTERM and restricts PATH lookup to extension directory.
[evt_why_cli_rev_c712] (pr_review_comment:c712) Review on PR #670: Reject executing third-party extensions via in-process Go plugins: Go dynamic plugin loading requires exact compiler and dependency ABI matches and allows arbitrary memory access. External subprocess isolation is non-negotiable.
[evt_why_cli_rfc_04] (adr:docs/rfc/004-termenv-formatting.md) RFC 004: Terminal Color and Hyperlink Detection via termenv: Status: accepted

Context:
Hardcoded ANSI escape codes corrupted tabular output when piping to external commands (grep, awk, jq) or running in CI logs.

Decision:
Use termenv library to inspect terminal color profile, automatically stripping styling when stdout is not a TTY or NO_COLOR is set.

Consequences:
- Clean machine-readable output in scripts.
- Rich interactive color and OSC 8 hyperlinks 
[evt_why_cli_issue_620] (github_issue:620) Issue #620: Broken ANSI escape sequences when piping gh output to jq and grep: Users scripting gh pr list | jq . experienced JSON syntax errors because color escape sequences were embedded inside fields.
[evt_why_cli_pr_735] (github_pr:735) PR #735: Auto-detect TTY and disable ANSI formatting in non-interactive pipelines (Closes #620): Implements RFC 004. Replaces hardcoded escape codes with IOStreams ColorEnabled check and respects CLICOLOR / NO_COLOR standard env vars.
[evt_why_cli_rfc_05] (adr:docs/rfc/005-git-credential-helper.md) RFC 005: Git Credential Helper Protocol Provider: Status: accepted

Context:
Users running git clone after authenticating via gh auth login were prompted again by Git for their username and password.

Decision:
Implement gh auth git-credential command implementing the standard Git credential helper protocol responding to get, store, and erase.

Consequences:
- Transparent authentication for all git operations.
- Reuses secure OAuth token stored i
[evt_why_cli_pr_810] (github_pr:810) PR #810: Implementation of gh auth git-credential helper protocol: Implements RFC 005. Configures git credential helper entry in global .gitconfig during gh auth login setup.
[evt_why_cli_rev_c840] (pr_review_comment:c840) Review on PR #810: Reject global auth token in HTTP GET query string: Passing tokens in URL query parameters exposes them in web server access logs and proxy history. All authentication must strictly use Authorization: Bearer HTTP header.
[evt_why_cli_issue_780] (github_issue:780) Issue #780: Browser open failure in headless SSH and cloud container environments: Running gh auth login on remote headless EC2 instances hung indefinitely attempting to open xdg-open desktop browser.
[evt_why_cli_pr_920] (github_pr:920) PR #920: OAuth Device Code flow fallback for headless SSH sessions (Closes #780): Detects lack of display server or SSH session and displays 8-digit one-time device code with github.com/login/device URL for secondary device authentication.
```

---

### Trial 23: Question `WB_CLI_13`

- **Repository:** `cli/cli`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_cli_rfc_05`
- **Ground Truth Summary:** Implements the gh auth git-credential helper answering Git protocol get/store/erase queries from the OS keychain.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cli/cli'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: How does GitHub CLI share credentials with standard Git CLI operations?

Event Stream:
[evt_why_cli_rfc_01] (adr:docs/rfc/001-keyring-credentials.md) RFC 001: Secure OAuth Token Storage using Native OS Keyrings: Status: accepted

Context:
Storing GitHub OAuth tokens in plaintext YAML config files (~/.config/gh/hosts.yml) leaves developer credentials vulnerable to unauthorized local processes.

Decision:
Integrate native OS keychain/keyring providers (macOS Keychain, Windows Credential Manager, Linux SecretService) as default secure token storage.

Consequences:
- Zero plaintext credential storage on disk.
[evt_why_cli_issue_412] (github_issue:412) Issue #412: Plaintext tokens exposed in process environment variables and config files: Security audit noted that gh auth login stores tokens in world-readable ~/.config/gh/config.yml. Keyring integration requested.
[evt_why_cli_pr_518] (github_pr:518) PR #518: Add zalando/go-keyring provider for auth token persistence (Closes #412): Implements RFC 001. Migrates token storage to native OS keychain with graceful fallback to file store.
[evt_why_cli_rev_c601] (pr_review_comment:c601) Review on PR #518: Reject custom symmetric encryption key on disk: Custom symmetric key encryption stored next to the ciphertext offers zero additional security. We must use OS-level protected credentials.
[evt_why_cli_rfc_03] (adr:docs/rfc/003-extension-isolation.md) RFC 003: Subprocess Extension Execution Model with Scoped Token Environment: Status: accepted

Context:
Executing third-party gh extensions inside the main process runtime risks memory contamination and uncontrolled privilege escalation.

Decision:
Execute extensions as isolated external child subprocesses communicating via standard input/output with stripped environment variables.

Consequences:
- Protects host CLI process memory.
- Prevents extension crashes from termina
[evt_why_cli_rfc_02] (adr:docs/rfc/002-graphql-query-batching.md) RFC 002: GraphQL Query Batching and Fragment Reuse for Repositories: Status: accepted

Context:
Listing 30 pull requests previously executed 30 separate REST requests to fetch review statuses, causing high latency and rate limit depletion.

Decision:
Consolidate GitHub API access through GraphQL queries using reusable fragments and connection paging.

Consequences:
- Latency reduced from 3.2s to 420ms for PR lists.
- Single API call quota unit consumed per page.
[evt_why_cli_issue_480] (github_issue:480) Issue #480: N+1 REST API roundtrips during repo list with pull requests: Running gh pr list on repositories with extensive checks resulted in secondary API queries per line item exceeding the 5,000 req/hr rate limit.
[evt_why_cli_pr_592] (github_pr:592) PR #592: Batch repository and issue queries using GraphQL fragments (Closes #480): Implements RFC 002. Replaces REST loops with single paginated GraphQL queries fetching comments, reviews, and status rollups in one payload.
[evt_why_cli_issue_550] (github_issue:550) Issue #550: Extension crash corrupts parent terminal state and escapes PATH: Extensions invoking raw exec commands leaked file descriptors and left raw terminal mode active on fatal signal crashes.
[evt_why_cli_pr_670] (github_pr:670) PR #670: Fork-exec child subprocess isolation with restricted inherited env for extensions (Closes #550): Implements RFC 003. Child process manager cleans up terminal modes on SIGINT/SIGTERM and restricts PATH lookup to extension directory.
[evt_why_cli_rev_c712] (pr_review_comment:c712) Review on PR #670: Reject executing third-party extensions via in-process Go plugins: Go dynamic plugin loading requires exact compiler and dependency ABI matches and allows arbitrary memory access. External subprocess isolation is non-negotiable.
[evt_why_cli_rfc_04] (adr:docs/rfc/004-termenv-formatting.md) RFC 004: Terminal Color and Hyperlink Detection via termenv: Status: accepted

Context:
Hardcoded ANSI escape codes corrupted tabular output when piping to external commands (grep, awk, jq) or running in CI logs.

Decision:
Use termenv library to inspect terminal color profile, automatically stripping styling when stdout is not a TTY or NO_COLOR is set.

Consequences:
- Clean machine-readable output in scripts.
- Rich interactive color and OSC 8 hyperlinks 
[evt_why_cli_issue_620] (github_issue:620) Issue #620: Broken ANSI escape sequences when piping gh output to jq and grep: Users scripting gh pr list | jq . experienced JSON syntax errors because color escape sequences were embedded inside fields.
[evt_why_cli_pr_735] (github_pr:735) PR #735: Auto-detect TTY and disable ANSI formatting in non-interactive pipelines (Closes #620): Implements RFC 004. Replaces hardcoded escape codes with IOStreams ColorEnabled check and respects CLICOLOR / NO_COLOR standard env vars.
[evt_why_cli_rfc_05] (adr:docs/rfc/005-git-credential-helper.md) RFC 005: Git Credential Helper Protocol Provider: Status: accepted

Context:
Users running git clone after authenticating via gh auth login were prompted again by Git for their username and password.

Decision:
Implement gh auth git-credential command implementing the standard Git credential helper protocol responding to get, store, and erase.

Consequences:
- Transparent authentication for all git operations.
- Reuses secure OAuth token stored i
[evt_why_cli_pr_810] (github_pr:810) PR #810: Implementation of gh auth git-credential helper protocol: Implements RFC 005. Configures git credential helper entry in global .gitconfig during gh auth login setup.
[evt_why_cli_rev_c840] (pr_review_comment:c840) Review on PR #810: Reject global auth token in HTTP GET query string: Passing tokens in URL query parameters exposes them in web server access logs and proxy history. All authentication must strictly use Authorization: Bearer HTTP header.
[evt_why_cli_issue_780] (github_issue:780) Issue #780: Browser open failure in headless SSH and cloud container environments: Running gh auth login on remote headless EC2 instances hung indefinitely attempting to open xdg-open desktop browser.
[evt_why_cli_pr_920] (github_pr:920) PR #920: OAuth Device Code flow fallback for headless SSH sessions (Closes #780): Detects lack of display server or SSH session and displays 8-digit one-time device code with github.com/login/device URL for secondary device authentication.
```

---

### Trial 24: Question `WB_CLI_14`

- **Repository:** `cli/cli`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_cli_pr_810`
- **Ground Truth Summary:** PR #810 adds git credential helper entries directly into global git configuration during gh auth login.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cli/cli'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: How is git credential helper configured during authentication?

Event Stream:
[evt_why_cli_rfc_01] (adr:docs/rfc/001-keyring-credentials.md) RFC 001: Secure OAuth Token Storage using Native OS Keyrings: Status: accepted

Context:
Storing GitHub OAuth tokens in plaintext YAML config files (~/.config/gh/hosts.yml) leaves developer credentials vulnerable to unauthorized local processes.

Decision:
Integrate native OS keychain/keyring providers (macOS Keychain, Windows Credential Manager, Linux SecretService) as default secure token storage.

Consequences:
- Zero plaintext credential storage on disk.
[evt_why_cli_issue_412] (github_issue:412) Issue #412: Plaintext tokens exposed in process environment variables and config files: Security audit noted that gh auth login stores tokens in world-readable ~/.config/gh/config.yml. Keyring integration requested.
[evt_why_cli_pr_518] (github_pr:518) PR #518: Add zalando/go-keyring provider for auth token persistence (Closes #412): Implements RFC 001. Migrates token storage to native OS keychain with graceful fallback to file store.
[evt_why_cli_rev_c601] (pr_review_comment:c601) Review on PR #518: Reject custom symmetric encryption key on disk: Custom symmetric key encryption stored next to the ciphertext offers zero additional security. We must use OS-level protected credentials.
[evt_why_cli_rfc_03] (adr:docs/rfc/003-extension-isolation.md) RFC 003: Subprocess Extension Execution Model with Scoped Token Environment: Status: accepted

Context:
Executing third-party gh extensions inside the main process runtime risks memory contamination and uncontrolled privilege escalation.

Decision:
Execute extensions as isolated external child subprocesses communicating via standard input/output with stripped environment variables.

Consequences:
- Protects host CLI process memory.
- Prevents extension crashes from termina
[evt_why_cli_rfc_02] (adr:docs/rfc/002-graphql-query-batching.md) RFC 002: GraphQL Query Batching and Fragment Reuse for Repositories: Status: accepted

Context:
Listing 30 pull requests previously executed 30 separate REST requests to fetch review statuses, causing high latency and rate limit depletion.

Decision:
Consolidate GitHub API access through GraphQL queries using reusable fragments and connection paging.

Consequences:
- Latency reduced from 3.2s to 420ms for PR lists.
- Single API call quota unit consumed per page.
[evt_why_cli_issue_480] (github_issue:480) Issue #480: N+1 REST API roundtrips during repo list with pull requests: Running gh pr list on repositories with extensive checks resulted in secondary API queries per line item exceeding the 5,000 req/hr rate limit.
[evt_why_cli_pr_592] (github_pr:592) PR #592: Batch repository and issue queries using GraphQL fragments (Closes #480): Implements RFC 002. Replaces REST loops with single paginated GraphQL queries fetching comments, reviews, and status rollups in one payload.
[evt_why_cli_issue_550] (github_issue:550) Issue #550: Extension crash corrupts parent terminal state and escapes PATH: Extensions invoking raw exec commands leaked file descriptors and left raw terminal mode active on fatal signal crashes.
[evt_why_cli_pr_670] (github_pr:670) PR #670: Fork-exec child subprocess isolation with restricted inherited env for extensions (Closes #550): Implements RFC 003. Child process manager cleans up terminal modes on SIGINT/SIGTERM and restricts PATH lookup to extension directory.
[evt_why_cli_rev_c712] (pr_review_comment:c712) Review on PR #670: Reject executing third-party extensions via in-process Go plugins: Go dynamic plugin loading requires exact compiler and dependency ABI matches and allows arbitrary memory access. External subprocess isolation is non-negotiable.
[evt_why_cli_rfc_04] (adr:docs/rfc/004-termenv-formatting.md) RFC 004: Terminal Color and Hyperlink Detection via termenv: Status: accepted

Context:
Hardcoded ANSI escape codes corrupted tabular output when piping to external commands (grep, awk, jq) or running in CI logs.

Decision:
Use termenv library to inspect terminal color profile, automatically stripping styling when stdout is not a TTY or NO_COLOR is set.

Consequences:
- Clean machine-readable output in scripts.
- Rich interactive color and OSC 8 hyperlinks 
[evt_why_cli_issue_620] (github_issue:620) Issue #620: Broken ANSI escape sequences when piping gh output to jq and grep: Users scripting gh pr list | jq . experienced JSON syntax errors because color escape sequences were embedded inside fields.
[evt_why_cli_pr_735] (github_pr:735) PR #735: Auto-detect TTY and disable ANSI formatting in non-interactive pipelines (Closes #620): Implements RFC 004. Replaces hardcoded escape codes with IOStreams ColorEnabled check and respects CLICOLOR / NO_COLOR standard env vars.
[evt_why_cli_rfc_05] (adr:docs/rfc/005-git-credential-helper.md) RFC 005: Git Credential Helper Protocol Provider: Status: accepted

Context:
Users running git clone after authenticating via gh auth login were prompted again by Git for their username and password.

Decision:
Implement gh auth git-credential command implementing the standard Git credential helper protocol responding to get, store, and erase.

Consequences:
- Transparent authentication for all git operations.
- Reuses secure OAuth token stored i
[evt_why_cli_pr_810] (github_pr:810) PR #810: Implementation of gh auth git-credential helper protocol: Implements RFC 005. Configures git credential helper entry in global .gitconfig during gh auth login setup.
[evt_why_cli_rev_c840] (pr_review_comment:c840) Review on PR #810: Reject global auth token in HTTP GET query string: Passing tokens in URL query parameters exposes them in web server access logs and proxy history. All authentication must strictly use Authorization: Bearer HTTP header.
[evt_why_cli_issue_780] (github_issue:780) Issue #780: Browser open failure in headless SSH and cloud container environments: Running gh auth login on remote headless EC2 instances hung indefinitely attempting to open xdg-open desktop browser.
[evt_why_cli_pr_920] (github_pr:920) PR #920: OAuth Device Code flow fallback for headless SSH sessions (Closes #780): Detects lack of display server or SSH session and displays 8-digit one-time device code with github.com/login/device URL for secondary device authentication.
```

---

### Trial 25: Question `WB_CLI_15`

- **Repository:** `cli/cli`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `rejected`
- **Expected Evidence Events:** `evt_why_cli_rev_c840`
- **Ground Truth Summary:** URL query tokens leak into proxy logs and browser history; tokens must strictly use Authorization HTTP headers.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cli/cli'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Why was passing authentication tokens via URL query parameters rejected?

Event Stream:
[evt_why_cli_rfc_01] (adr:docs/rfc/001-keyring-credentials.md) RFC 001: Secure OAuth Token Storage using Native OS Keyrings: Status: accepted

Context:
Storing GitHub OAuth tokens in plaintext YAML config files (~/.config/gh/hosts.yml) leaves developer credentials vulnerable to unauthorized local processes.

Decision:
Integrate native OS keychain/keyring providers (macOS Keychain, Windows Credential Manager, Linux SecretService) as default secure token storage.

Consequences:
- Zero plaintext credential storage on disk.
[evt_why_cli_issue_412] (github_issue:412) Issue #412: Plaintext tokens exposed in process environment variables and config files: Security audit noted that gh auth login stores tokens in world-readable ~/.config/gh/config.yml. Keyring integration requested.
[evt_why_cli_pr_518] (github_pr:518) PR #518: Add zalando/go-keyring provider for auth token persistence (Closes #412): Implements RFC 001. Migrates token storage to native OS keychain with graceful fallback to file store.
[evt_why_cli_rev_c601] (pr_review_comment:c601) Review on PR #518: Reject custom symmetric encryption key on disk: Custom symmetric key encryption stored next to the ciphertext offers zero additional security. We must use OS-level protected credentials.
[evt_why_cli_rfc_03] (adr:docs/rfc/003-extension-isolation.md) RFC 003: Subprocess Extension Execution Model with Scoped Token Environment: Status: accepted

Context:
Executing third-party gh extensions inside the main process runtime risks memory contamination and uncontrolled privilege escalation.

Decision:
Execute extensions as isolated external child subprocesses communicating via standard input/output with stripped environment variables.

Consequences:
- Protects host CLI process memory.
- Prevents extension crashes from termina
[evt_why_cli_rfc_02] (adr:docs/rfc/002-graphql-query-batching.md) RFC 002: GraphQL Query Batching and Fragment Reuse for Repositories: Status: accepted

Context:
Listing 30 pull requests previously executed 30 separate REST requests to fetch review statuses, causing high latency and rate limit depletion.

Decision:
Consolidate GitHub API access through GraphQL queries using reusable fragments and connection paging.

Consequences:
- Latency reduced from 3.2s to 420ms for PR lists.
- Single API call quota unit consumed per page.
[evt_why_cli_issue_480] (github_issue:480) Issue #480: N+1 REST API roundtrips during repo list with pull requests: Running gh pr list on repositories with extensive checks resulted in secondary API queries per line item exceeding the 5,000 req/hr rate limit.
[evt_why_cli_pr_592] (github_pr:592) PR #592: Batch repository and issue queries using GraphQL fragments (Closes #480): Implements RFC 002. Replaces REST loops with single paginated GraphQL queries fetching comments, reviews, and status rollups in one payload.
[evt_why_cli_issue_550] (github_issue:550) Issue #550: Extension crash corrupts parent terminal state and escapes PATH: Extensions invoking raw exec commands leaked file descriptors and left raw terminal mode active on fatal signal crashes.
[evt_why_cli_pr_670] (github_pr:670) PR #670: Fork-exec child subprocess isolation with restricted inherited env for extensions (Closes #550): Implements RFC 003. Child process manager cleans up terminal modes on SIGINT/SIGTERM and restricts PATH lookup to extension directory.
[evt_why_cli_rev_c712] (pr_review_comment:c712) Review on PR #670: Reject executing third-party extensions via in-process Go plugins: Go dynamic plugin loading requires exact compiler and dependency ABI matches and allows arbitrary memory access. External subprocess isolation is non-negotiable.
[evt_why_cli_rfc_04] (adr:docs/rfc/004-termenv-formatting.md) RFC 004: Terminal Color and Hyperlink Detection via termenv: Status: accepted

Context:
Hardcoded ANSI escape codes corrupted tabular output when piping to external commands (grep, awk, jq) or running in CI logs.

Decision:
Use termenv library to inspect terminal color profile, automatically stripping styling when stdout is not a TTY or NO_COLOR is set.

Consequences:
- Clean machine-readable output in scripts.
- Rich interactive color and OSC 8 hyperlinks 
[evt_why_cli_issue_620] (github_issue:620) Issue #620: Broken ANSI escape sequences when piping gh output to jq and grep: Users scripting gh pr list | jq . experienced JSON syntax errors because color escape sequences were embedded inside fields.
[evt_why_cli_pr_735] (github_pr:735) PR #735: Auto-detect TTY and disable ANSI formatting in non-interactive pipelines (Closes #620): Implements RFC 004. Replaces hardcoded escape codes with IOStreams ColorEnabled check and respects CLICOLOR / NO_COLOR standard env vars.
[evt_why_cli_rfc_05] (adr:docs/rfc/005-git-credential-helper.md) RFC 005: Git Credential Helper Protocol Provider: Status: accepted

Context:
Users running git clone after authenticating via gh auth login were prompted again by Git for their username and password.

Decision:
Implement gh auth git-credential command implementing the standard Git credential helper protocol responding to get, store, and erase.

Consequences:
- Transparent authentication for all git operations.
- Reuses secure OAuth token stored i
[evt_why_cli_pr_810] (github_pr:810) PR #810: Implementation of gh auth git-credential helper protocol: Implements RFC 005. Configures git credential helper entry in global .gitconfig during gh auth login setup.
[evt_why_cli_rev_c840] (pr_review_comment:c840) Review on PR #810: Reject global auth token in HTTP GET query string: Passing tokens in URL query parameters exposes them in web server access logs and proxy history. All authentication must strictly use Authorization: Bearer HTTP header.
[evt_why_cli_issue_780] (github_issue:780) Issue #780: Browser open failure in headless SSH and cloud container environments: Running gh auth login on remote headless EC2 instances hung indefinitely attempting to open xdg-open desktop browser.
[evt_why_cli_pr_920] (github_pr:920) PR #920: OAuth Device Code flow fallback for headless SSH sessions (Closes #780): Detects lack of display server or SSH session and displays 8-digit one-time device code with github.com/login/device URL for secondary device authentication.
```

---

### Trial 26: Question `WB_CLI_16`

- **Repository:** `cli/cli`
- **Type:** Positive (Recorded Decision)
- **Expected State:** `accepted`
- **Expected Evidence Events:** `evt_why_cli_pr_920, evt_why_cli_issue_780`
- **Ground Truth Summary:** Falls back to OAuth Device Code flow presenting a one-time 8-digit code for secondary device authorization.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cli/cli'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: How does gh auth login authenticate in headless SSH cloud environments without a browser?

Event Stream:
[evt_why_cli_rfc_01] (adr:docs/rfc/001-keyring-credentials.md) RFC 001: Secure OAuth Token Storage using Native OS Keyrings: Status: accepted

Context:
Storing GitHub OAuth tokens in plaintext YAML config files (~/.config/gh/hosts.yml) leaves developer credentials vulnerable to unauthorized local processes.

Decision:
Integrate native OS keychain/keyring providers (macOS Keychain, Windows Credential Manager, Linux SecretService) as default secure token storage.

Consequences:
- Zero plaintext credential storage on disk.
[evt_why_cli_issue_412] (github_issue:412) Issue #412: Plaintext tokens exposed in process environment variables and config files: Security audit noted that gh auth login stores tokens in world-readable ~/.config/gh/config.yml. Keyring integration requested.
[evt_why_cli_pr_518] (github_pr:518) PR #518: Add zalando/go-keyring provider for auth token persistence (Closes #412): Implements RFC 001. Migrates token storage to native OS keychain with graceful fallback to file store.
[evt_why_cli_rev_c601] (pr_review_comment:c601) Review on PR #518: Reject custom symmetric encryption key on disk: Custom symmetric key encryption stored next to the ciphertext offers zero additional security. We must use OS-level protected credentials.
[evt_why_cli_rfc_03] (adr:docs/rfc/003-extension-isolation.md) RFC 003: Subprocess Extension Execution Model with Scoped Token Environment: Status: accepted

Context:
Executing third-party gh extensions inside the main process runtime risks memory contamination and uncontrolled privilege escalation.

Decision:
Execute extensions as isolated external child subprocesses communicating via standard input/output with stripped environment variables.

Consequences:
- Protects host CLI process memory.
- Prevents extension crashes from termina
[evt_why_cli_rfc_02] (adr:docs/rfc/002-graphql-query-batching.md) RFC 002: GraphQL Query Batching and Fragment Reuse for Repositories: Status: accepted

Context:
Listing 30 pull requests previously executed 30 separate REST requests to fetch review statuses, causing high latency and rate limit depletion.

Decision:
Consolidate GitHub API access through GraphQL queries using reusable fragments and connection paging.

Consequences:
- Latency reduced from 3.2s to 420ms for PR lists.
- Single API call quota unit consumed per page.
[evt_why_cli_issue_480] (github_issue:480) Issue #480: N+1 REST API roundtrips during repo list with pull requests: Running gh pr list on repositories with extensive checks resulted in secondary API queries per line item exceeding the 5,000 req/hr rate limit.
[evt_why_cli_pr_592] (github_pr:592) PR #592: Batch repository and issue queries using GraphQL fragments (Closes #480): Implements RFC 002. Replaces REST loops with single paginated GraphQL queries fetching comments, reviews, and status rollups in one payload.
[evt_why_cli_issue_550] (github_issue:550) Issue #550: Extension crash corrupts parent terminal state and escapes PATH: Extensions invoking raw exec commands leaked file descriptors and left raw terminal mode active on fatal signal crashes.
[evt_why_cli_pr_670] (github_pr:670) PR #670: Fork-exec child subprocess isolation with restricted inherited env for extensions (Closes #550): Implements RFC 003. Child process manager cleans up terminal modes on SIGINT/SIGTERM and restricts PATH lookup to extension directory.
[evt_why_cli_rev_c712] (pr_review_comment:c712) Review on PR #670: Reject executing third-party extensions via in-process Go plugins: Go dynamic plugin loading requires exact compiler and dependency ABI matches and allows arbitrary memory access. External subprocess isolation is non-negotiable.
[evt_why_cli_rfc_04] (adr:docs/rfc/004-termenv-formatting.md) RFC 004: Terminal Color and Hyperlink Detection via termenv: Status: accepted

Context:
Hardcoded ANSI escape codes corrupted tabular output when piping to external commands (grep, awk, jq) or running in CI logs.

Decision:
Use termenv library to inspect terminal color profile, automatically stripping styling when stdout is not a TTY or NO_COLOR is set.

Consequences:
- Clean machine-readable output in scripts.
- Rich interactive color and OSC 8 hyperlinks 
[evt_why_cli_issue_620] (github_issue:620) Issue #620: Broken ANSI escape sequences when piping gh output to jq and grep: Users scripting gh pr list | jq . experienced JSON syntax errors because color escape sequences were embedded inside fields.
[evt_why_cli_pr_735] (github_pr:735) PR #735: Auto-detect TTY and disable ANSI formatting in non-interactive pipelines (Closes #620): Implements RFC 004. Replaces hardcoded escape codes with IOStreams ColorEnabled check and respects CLICOLOR / NO_COLOR standard env vars.
[evt_why_cli_rfc_05] (adr:docs/rfc/005-git-credential-helper.md) RFC 005: Git Credential Helper Protocol Provider: Status: accepted

Context:
Users running git clone after authenticating via gh auth login were prompted again by Git for their username and password.

Decision:
Implement gh auth git-credential command implementing the standard Git credential helper protocol responding to get, store, and erase.

Consequences:
- Transparent authentication for all git operations.
- Reuses secure OAuth token stored i
[evt_why_cli_pr_810] (github_pr:810) PR #810: Implementation of gh auth git-credential helper protocol: Implements RFC 005. Configures git credential helper entry in global .gitconfig during gh auth login setup.
[evt_why_cli_rev_c840] (pr_review_comment:c840) Review on PR #810: Reject global auth token in HTTP GET query string: Passing tokens in URL query parameters exposes them in web server access logs and proxy history. All authentication must strictly use Authorization: Bearer HTTP header.
[evt_why_cli_issue_780] (github_issue:780) Issue #780: Browser open failure in headless SSH and cloud container environments: Running gh auth login on remote headless EC2 instances hung indefinitely attempting to open xdg-open desktop browser.
[evt_why_cli_pr_920] (github_pr:920) PR #920: OAuth Device Code flow fallback for headless SSH sessions (Closes #780): Detects lack of display server or SSH session and displays 8-digit one-time device code with github.com/login/device URL for secondary device authentication.
```

---

### Trial 27: Question `WB_CH_TEST_NEG_14`

- **Repository:** `cloud-hypervisor/cloud-hypervisor`
- **Type:** Negative (Unrecorded Topic)
- **Expected State:** `none`
- **Expected Evidence Events:** `evt_why_ch_pr_1042`
- **Ground Truth Summary:** Mention without decision; CI perf bot posted 1GB hugepages benchmark comparison, but hugepage size was left configurable.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cloud-hypervisor/cloud-hypervisor'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Did bot automated benchmark comments on PR #1042 decide to enforce 1GB hugepages for all guests?

Event Stream:
[evt_why_ch_rfc_01] (adr:docs/designs/live-migration.md) Design: Pre-copy Live Migration with Dirty Page Tracking via KVM dirty ring: Status: accepted

Context:
Virtual machine live migration must minimize downtime below 50ms while transferring guest memory under active workloads.

Decision:
Implement iterative pre-copy migration using KVM dirty ring buffer instead of classic user-faultfd or dirty bitmap.

Consequences:
- Drastically reduces lock contention during memory dirty page capture.
- Guest pause time under 35ms on 10GbE
[evt_why_ch_pr_1042] (github_pr:1042) PR #1042: Implement VirtIO Memory Ballooning with Page Reporting: Adds virtio-balloon device supporting automatic unused page reporting back to host hypervisor. Enables dynamic RAM overcommit without guest performance degradation.
[evt_why_ch_issue_890] (github_issue:890) Issue #890: Memory balloon deflation stalls under aggressive host memory pressure: When host demands quick reclamation, balloon thread deadlock occurred due to synchronous locking on memory allocation bus.
[evt_why_ch_rev_c502] (pr_review_comment:c502) Review on PR #1042: Reject synchronous balloon deflation: Synchronous deflation blocks guest vCPUs for up to 400ms. We must reject synchronous balloon worker in favor of asynchronous background worker thread.
[evt_why_ch_rfc_03] (adr:docs/designs/vhost-user-net.md) Design: Vhost-User Network Backend with Multi-Queue Support: Status: accepted

Context:
Standard TAP networking limits packet throughput to ~1.2 Mpps due to kernel context switching overhead.

Decision:
Implement vhost-user-net backend delegating packet processing to DPDK/OVS processes via shared memory queues.

Consequences:
- Achieves line-rate 10GbE throughput (>8 Mpps).
- Eliminates kernel networking path context switches.
[evt_why_ch_rfc_02] (adr:docs/designs/direct-kernel-boot.md) Design: Direct Linux Kernel Boot without Legacy BIOS/GRUB: Status: accepted

Context:
Booting a full SeaBIOS or UEFI image adds 500ms-2s of cold start latency to cloud hypervisor microVMs.

Decision:
Implement direct ELF/bzImage loader jumping straight into the Linux kernel entry point with boot_params setup.

Consequences:
- Sub-30ms VM boot times.
- Eliminates legacy BIOS real-mode emulation code from VMM.
[evt_why_ch_issue_940] (github_issue:940) Issue #940: High guest exit latency on unpinned multi-threaded vCPUs: vCPU threads migrating across NUMA nodes caused up to 300% tail latency jitter on latency-sensitive guest workloads.
[evt_why_ch_pr_1105] (github_pr:1105) PR #1105: CPU Pinning and NUMA Topology Node Binding (Closes #940): Allows operator to pin guest vCPUs to specific host physical cores and bind guest RAM to local host NUMA nodes using libc::sched_setaffinity.
[evt_why_ch_rev_c615] (pr_review_comment:c615) Review on PR #1105: Reject legacy floppy and IDE device emulation: Emulating legacy PC hardware (floppy, IDE, PS/2) contradicts Cloud Hypervisor's minimal attack surface goal. Only modern VirtIO and PCIe interfaces will be supported.
[evt_why_ch_rfc_04] (adr:docs/designs/virtio-fs.md) Design: VirtIO-FS Shared Host Filesystem with Direct Access (DAX) Window: Status: accepted

Context:
Container runtimes (Kata Containers) need efficient sharing of host root filesystems with minimal memory overhead.

Decision:
Support virtio-fs device with a dedicated DAX window mapping host page cache directly into guest physical address space.

Consequences:
- Zero guest page cache memory duplication.
- File reads bypass guest I/O path directly to host cache.
[evt_why_ch_issue_1015] (github_issue:1015) Issue #1015: Host file lock contention in virtio-fs shared directory mounts: Multiple concurrent containers writing to shared virtio-fs directory caused POSIX file lock contention in virtiofsd daemon.
[evt_why_ch_pr_1180] (github_pr:1180) PR #1180: PCIe Root Port Hotplug Support for VirtIO Devices: Adds ACPI PCI hotplug notifications and PCIe native hotplug controller allowing runtime addition and removal of network interfaces and disks.
[evt_why_ch_pr_1240] (github_pr:1240) PR #1240: Asynchronous Disk I/O via Linux io_uring Engine: Replaces threadpool synchronous pread/pwrite with io_uring submission/completion queue rings for virtio-block backend.
[evt_why_ch_rev_c720] (pr_review_comment:c720) Review on PR #1240: Reject unbounded polling loops in vhost worker: Spin-polling io_uring SQPOLL thread pegging 100% CPU on idle guests is prohibited. Eventfd notification must be used when queue is drained.
[evt_why_ch_pr_1312] (github_pr:1312) PR #1312: VFIO PCI Device Passthrough for GPU Workloads: Integrates VFIO Linux kernel API enabling secure hardware DMA remapping and MSI-X interrupt forwarding for dedicated guest GPUs and NVMe drives.
[evt_why_ch_rfc_05] (adr:docs/designs/acpi-ged.md) Design: ACPI Generic Event Device (GED) for System Notifications: Status: accepted

Context:
Handling power button, shutdown, and hotplug interrupts previously required complex proprietary DSDT methods.

Decision:
Adopt ACPI 5.0 Generic Event Device (GED) providing simplified interrupt-driven event signaling across x86_64 and AArch64.

Consequences:
- Unified event dispatch table across architectures.
- Removes ~1,200 lines of architecture-specific AML bytecode.
[evt_why_ch_issue_1120] (github_issue:1120) Issue #1120: Guest memory leak in balloon statistics driver queue: Periodic stat queue buffers allocated by guest kernel were leaked when host neglected to acknowledge polling rings.
[evt_why_ch_pr_1390] (github_pr:1390) PR #1390: MicroVM Minimal Device Tree Profile for Serverless Sandboxes: Configures minimal sandbox VM profile stripping ACPI tables and serial emulation, reducing guest boot time to 12ms for AWS Lambda style workloads.
```

---

### Trial 28: Question `WB_PAY_TEST_NEG_08`

- **Repository:** `acme-ecommerce/payment-core`
- **Type:** Negative (Unrecorded Topic)
- **Expected State:** `none`
- **Expected Evidence Events:** `evt_why_pay_pr_18`
- **Ground Truth Summary:** Mention without decision; Memcached was casually compared to Redis in PR discussion, but only Redis was used.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'acme-ecommerce/payment-core'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Did PR #18 review comments decide to adopt Memcached alongside Redis for idempotency?

Event Stream:
[evt_why_pay_adr_01] (adr:docs/adr/0001-stripe-payment-migration.md) ADR 0001: Migrate from Legacy Braintree to Stripe Payment Intents API: Status: accepted

Context:
Legacy Braintree integration does not support European 3D Secure 2 authentication and suffers from elevated drop-off during checkout.

Decision:
Migrate checkout payment processing to Stripe Payment Intents with asynchronous webhook settlement.

Consequences:
- Full 3DS2 compliance.
- Checkout authorization latency reduced to <800ms.
- Requires webhook listener for async
[evt_why_pay_issue_08] (github_issue:8) Issue #8: Stripe API 429 Rate Limits encountered during flash sale traffic: During peak traffic burst, worker threads made simultaneous calls to Stripe charges API exceeding the 100 req/sec rate limit without jittered exponential backoff.
[evt_why_pay_pr_14] (github_pr:14) PR #14: Implement Exponential Backoff with Full Jitter for Stripe API (Closes #8): Adds decorator with decorator-level exponential backoff with full jitter (Decorrelated Jitter algorithm). Retries up to 4 times before failing.
[evt_why_pay_rev_c301] (pr_review_comment:c301) Review on PR #14: Reject fixed interval retries: Fixed 500ms sleep will create thundering herd when Stripe recovers. We must reject fixed sleep in favor of exponential backoff with randomized full jitter.
[evt_why_pay_adr_02] (adr:docs/adr/0002-webhook-idempotency.md) ADR 0002: Use Redis Distributed Lock and Idempotency Key for Webhooks: Status: accepted

Context:
Stripe webhook delivery guarantees at-least-once delivery. Duplicate payment.succeeded events caused double order fulfillment.

Decision:
Store processed Stripe event_ids in Redis with a 24-hour TTL and acquire a distributed mutex lock before processing webhook payloads.

Consequences:
- Zero duplicate order fulfillments.
- Redis availability required for payment reconci
[evt_why_pay_commit_7a] (git_commit:7a8b9c0d1e2f3a4b) feat(database): migrate to SQLAlchemy async connection pool with PgBouncer: Replaces raw psycopg2 connection per request with async connection pool. Reduces connection pool exhaustion under 2,000 checkout req/sec.
[evt_why_pay_issue_05] (github_issue:5) Issue #5: Duplicate customer charges under concurrent checkout clicks: Impatient users double clicking Pay Now sent parallel requests to /checkout initiating two distinct payment authorization transactions.
[evt_why_pay_pr_18] (github_pr:18) PR #18: Idempotency-Key Header Middleware with SHA-256 Request Hashing (Closes #5): Introduces Idempotency-Key HTTP header middleware computing SHA-256 digest of payload. Cache hit returns cached HTTP response immediately.
[evt_why_pay_rev_c402] (pr_review_comment:c402) Review on PR #18: Reject database-level transaction locks for idempotency: Using row-level database locks (SELECT FOR UPDATE) on the checkout table creates bottleneck deadlock risks during sales. Redis key-value atomicity is required.
[evt_why_pay_adr_03] (adr:docs/adr/0003-webhook-first-confirmation.md) ADR 0003: Webhook-First Asynchronous Order Confirmation: Status: accepted

Context:
Sync browser checkout redirect was dropping orders when mobile users closed Safari before the success return page loaded.

Decision:
Treat Stripe payment_intent.succeeded webhook event as the single source of truth for confirming orders rather than client-side redirects.

Consequences:
- Zero lost orders from closed tabs.
- Frontend displays pending state and listens via
[evt_why_pay_pr_22] (github_pr:22) PR #22: Webhook signature verification with HMAC-SHA256 and replay tolerance: Validates Stripe-Signature header with HMAC-SHA256 secret key and enforces a 300-second maximum timestamp drift window to prevent replay attacks.
[evt_why_pay_rev_c450] (pr_review_comment:c450) Review on PR #22: Reject skipping signature verification in development: Bypassing webhook signature checks via a debug flag risks shipping unverified endpoints to production. Verification must run in all environments with test keys.
[evt_why_pay_adr_04] (adr:docs/adr/0004-partial-refund-support.md) ADR 0004: Support Partial Refunds with Line-Item Reversal Ledger: Status: accepted

Context:
Customers returning one item out of a multi-item purchase required customer support intervention because the system only supported full-order voiding.

Decision:
Implement immutable append-only line-item reversal records tracking fractional refunds against order authorization totals.

Consequences:
- Eliminates manual support overrides for returns.
- Prevents cumulative 
[evt_why_pay_issue_11] (github_issue:11) Issue #11: Floating point rounding discrepancies during multi-currency partial refunds: Using standard IEEE 754 float types caused a 1-cent mismatch ($19.99 vs $19.989999) between partial refund sum and total charge.
[evt_why_pay_pr_29] (github_pr:29) PR #29: Migrate refund math to integer cents and Decimal representation (Closes #11): Converts all monetary fields to 64-bit integer minor currency units (cents) and Python Decimal to prevent floating point inaccuracies.
[evt_why_pay_rev_c505] (pr_review_comment:c505) Review on PR #29: Reject client-supplied refund timestamps: Relying on client timestamps allows fraudulent out-of-order refund attempts. Timestamps must strictly be generated by server UTC monotonic clock.
[evt_why_pay_issue_19] (github_issue:19) Issue #19: Toxic malformed webhook payloads causing infinite queue retry loops: Unparseable webhook payload triggered an unhandled exception causing RabbitMQ consumer to continually NACK and requeue, stalling normal processing.
[evt_why_pay_pr_35] (github_pr:35) PR #35: Route unparseable webhook messages to Dead Letter Queue after 3 failed deliveries (Closes #19): Configures DLQ with max-retries=3. Stalls are avoided by parking invalid messages for engineer inspection without blocking main line.
[evt_why_pay_adr_05] (adr:docs/adr/0005-pci-token-vault.md) ADR 0005: Dual-token vault encryption for PCI-DSS compliance: Status: accepted

Context:
PCI-DSS Scope Level 1 audit requires payment card numbers to never enter merchant application server memory or disk storage.

Decision:
Use Stripe Elements tokenization directly in client browser, receiving only opaque payment_method_id tokens on payment-core backend.

Consequences:
- Achieves PCI SAQ A eligibility, drastically reducing compliance overhead.
- Eliminates 
[evt_why_pay_rev_c610] (pr_review_comment:c610) Review on PR #38: Reject caching unencrypted CVV in memory: Storing raw CVVs even temporarily in Redis or local process memory is a direct violation of PCI-DSS requirement 3.2. Prohibit all CVV persistence.
```

---

### Trial 29: Question `WB_PAY_TEST_NEG_01`

- **Repository:** `acme-ecommerce/payment-core`
- **Type:** Negative (Unrecorded Topic)
- **Expected State:** `none`
- **Expected Evidence Events:** `None`
- **Ground Truth Summary:** No recorded decision; payment-core strictly exposes modern REST APIs with JSON.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'acme-ecommerce/payment-core'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Why did payment-core switch from JSON REST APIs to XML SOAP for payment endpoints?

Event Stream:
[evt_why_pay_adr_01] (adr:docs/adr/0001-stripe-payment-migration.md) ADR 0001: Migrate from Legacy Braintree to Stripe Payment Intents API: Status: accepted

Context:
Legacy Braintree integration does not support European 3D Secure 2 authentication and suffers from elevated drop-off during checkout.

Decision:
Migrate checkout payment processing to Stripe Payment Intents with asynchronous webhook settlement.

Consequences:
- Full 3DS2 compliance.
- Checkout authorization latency reduced to <800ms.
- Requires webhook listener for async
[evt_why_pay_issue_08] (github_issue:8) Issue #8: Stripe API 429 Rate Limits encountered during flash sale traffic: During peak traffic burst, worker threads made simultaneous calls to Stripe charges API exceeding the 100 req/sec rate limit without jittered exponential backoff.
[evt_why_pay_pr_14] (github_pr:14) PR #14: Implement Exponential Backoff with Full Jitter for Stripe API (Closes #8): Adds decorator with decorator-level exponential backoff with full jitter (Decorrelated Jitter algorithm). Retries up to 4 times before failing.
[evt_why_pay_rev_c301] (pr_review_comment:c301) Review on PR #14: Reject fixed interval retries: Fixed 500ms sleep will create thundering herd when Stripe recovers. We must reject fixed sleep in favor of exponential backoff with randomized full jitter.
[evt_why_pay_adr_02] (adr:docs/adr/0002-webhook-idempotency.md) ADR 0002: Use Redis Distributed Lock and Idempotency Key for Webhooks: Status: accepted

Context:
Stripe webhook delivery guarantees at-least-once delivery. Duplicate payment.succeeded events caused double order fulfillment.

Decision:
Store processed Stripe event_ids in Redis with a 24-hour TTL and acquire a distributed mutex lock before processing webhook payloads.

Consequences:
- Zero duplicate order fulfillments.
- Redis availability required for payment reconci
[evt_why_pay_commit_7a] (git_commit:7a8b9c0d1e2f3a4b) feat(database): migrate to SQLAlchemy async connection pool with PgBouncer: Replaces raw psycopg2 connection per request with async connection pool. Reduces connection pool exhaustion under 2,000 checkout req/sec.
[evt_why_pay_issue_05] (github_issue:5) Issue #5: Duplicate customer charges under concurrent checkout clicks: Impatient users double clicking Pay Now sent parallel requests to /checkout initiating two distinct payment authorization transactions.
[evt_why_pay_pr_18] (github_pr:18) PR #18: Idempotency-Key Header Middleware with SHA-256 Request Hashing (Closes #5): Introduces Idempotency-Key HTTP header middleware computing SHA-256 digest of payload. Cache hit returns cached HTTP response immediately.
[evt_why_pay_rev_c402] (pr_review_comment:c402) Review on PR #18: Reject database-level transaction locks for idempotency: Using row-level database locks (SELECT FOR UPDATE) on the checkout table creates bottleneck deadlock risks during sales. Redis key-value atomicity is required.
[evt_why_pay_adr_03] (adr:docs/adr/0003-webhook-first-confirmation.md) ADR 0003: Webhook-First Asynchronous Order Confirmation: Status: accepted

Context:
Sync browser checkout redirect was dropping orders when mobile users closed Safari before the success return page loaded.

Decision:
Treat Stripe payment_intent.succeeded webhook event as the single source of truth for confirming orders rather than client-side redirects.

Consequences:
- Zero lost orders from closed tabs.
- Frontend displays pending state and listens via
[evt_why_pay_pr_22] (github_pr:22) PR #22: Webhook signature verification with HMAC-SHA256 and replay tolerance: Validates Stripe-Signature header with HMAC-SHA256 secret key and enforces a 300-second maximum timestamp drift window to prevent replay attacks.
[evt_why_pay_rev_c450] (pr_review_comment:c450) Review on PR #22: Reject skipping signature verification in development: Bypassing webhook signature checks via a debug flag risks shipping unverified endpoints to production. Verification must run in all environments with test keys.
[evt_why_pay_adr_04] (adr:docs/adr/0004-partial-refund-support.md) ADR 0004: Support Partial Refunds with Line-Item Reversal Ledger: Status: accepted

Context:
Customers returning one item out of a multi-item purchase required customer support intervention because the system only supported full-order voiding.

Decision:
Implement immutable append-only line-item reversal records tracking fractional refunds against order authorization totals.

Consequences:
- Eliminates manual support overrides for returns.
- Prevents cumulative 
[evt_why_pay_issue_11] (github_issue:11) Issue #11: Floating point rounding discrepancies during multi-currency partial refunds: Using standard IEEE 754 float types caused a 1-cent mismatch ($19.99 vs $19.989999) between partial refund sum and total charge.
[evt_why_pay_pr_29] (github_pr:29) PR #29: Migrate refund math to integer cents and Decimal representation (Closes #11): Converts all monetary fields to 64-bit integer minor currency units (cents) and Python Decimal to prevent floating point inaccuracies.
[evt_why_pay_rev_c505] (pr_review_comment:c505) Review on PR #29: Reject client-supplied refund timestamps: Relying on client timestamps allows fraudulent out-of-order refund attempts. Timestamps must strictly be generated by server UTC monotonic clock.
[evt_why_pay_issue_19] (github_issue:19) Issue #19: Toxic malformed webhook payloads causing infinite queue retry loops: Unparseable webhook payload triggered an unhandled exception causing RabbitMQ consumer to continually NACK and requeue, stalling normal processing.
[evt_why_pay_pr_35] (github_pr:35) PR #35: Route unparseable webhook messages to Dead Letter Queue after 3 failed deliveries (Closes #19): Configures DLQ with max-retries=3. Stalls are avoided by parking invalid messages for engineer inspection without blocking main line.
[evt_why_pay_adr_05] (adr:docs/adr/0005-pci-token-vault.md) ADR 0005: Dual-token vault encryption for PCI-DSS compliance: Status: accepted

Context:
PCI-DSS Scope Level 1 audit requires payment card numbers to never enter merchant application server memory or disk storage.

Decision:
Use Stripe Elements tokenization directly in client browser, receiving only opaque payment_method_id tokens on payment-core backend.

Consequences:
- Achieves PCI SAQ A eligibility, drastically reducing compliance overhead.
- Eliminates 
[evt_why_pay_rev_c610] (pr_review_comment:c610) Review on PR #38: Reject caching unencrypted CVV in memory: Storing raw CVVs even temporarily in Redis or local process memory is a direct violation of PCI-DSS requirement 3.2. Prohibit all CVV persistence.
```

---

### Trial 30: Question `WB_PAY_TEST_NEG_06`

- **Repository:** `acme-ecommerce/payment-core`
- **Type:** Negative (Unrecorded Topic)
- **Expected State:** `none`
- **Expected Evidence Events:** `None`
- **Ground Truth Summary:** No recorded decision; HTTP Basic auth over unencrypted ports is strictly avoided.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'acme-ecommerce/payment-core'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Why did payment-core replace JWT token authentication with Basic HTTP auth over unencrypted ports?

Event Stream:
[evt_why_pay_adr_01] (adr:docs/adr/0001-stripe-payment-migration.md) ADR 0001: Migrate from Legacy Braintree to Stripe Payment Intents API: Status: accepted

Context:
Legacy Braintree integration does not support European 3D Secure 2 authentication and suffers from elevated drop-off during checkout.

Decision:
Migrate checkout payment processing to Stripe Payment Intents with asynchronous webhook settlement.

Consequences:
- Full 3DS2 compliance.
- Checkout authorization latency reduced to <800ms.
- Requires webhook listener for async
[evt_why_pay_issue_08] (github_issue:8) Issue #8: Stripe API 429 Rate Limits encountered during flash sale traffic: During peak traffic burst, worker threads made simultaneous calls to Stripe charges API exceeding the 100 req/sec rate limit without jittered exponential backoff.
[evt_why_pay_pr_14] (github_pr:14) PR #14: Implement Exponential Backoff with Full Jitter for Stripe API (Closes #8): Adds decorator with decorator-level exponential backoff with full jitter (Decorrelated Jitter algorithm). Retries up to 4 times before failing.
[evt_why_pay_rev_c301] (pr_review_comment:c301) Review on PR #14: Reject fixed interval retries: Fixed 500ms sleep will create thundering herd when Stripe recovers. We must reject fixed sleep in favor of exponential backoff with randomized full jitter.
[evt_why_pay_adr_02] (adr:docs/adr/0002-webhook-idempotency.md) ADR 0002: Use Redis Distributed Lock and Idempotency Key for Webhooks: Status: accepted

Context:
Stripe webhook delivery guarantees at-least-once delivery. Duplicate payment.succeeded events caused double order fulfillment.

Decision:
Store processed Stripe event_ids in Redis with a 24-hour TTL and acquire a distributed mutex lock before processing webhook payloads.

Consequences:
- Zero duplicate order fulfillments.
- Redis availability required for payment reconci
[evt_why_pay_commit_7a] (git_commit:7a8b9c0d1e2f3a4b) feat(database): migrate to SQLAlchemy async connection pool with PgBouncer: Replaces raw psycopg2 connection per request with async connection pool. Reduces connection pool exhaustion under 2,000 checkout req/sec.
[evt_why_pay_issue_05] (github_issue:5) Issue #5: Duplicate customer charges under concurrent checkout clicks: Impatient users double clicking Pay Now sent parallel requests to /checkout initiating two distinct payment authorization transactions.
[evt_why_pay_pr_18] (github_pr:18) PR #18: Idempotency-Key Header Middleware with SHA-256 Request Hashing (Closes #5): Introduces Idempotency-Key HTTP header middleware computing SHA-256 digest of payload. Cache hit returns cached HTTP response immediately.
[evt_why_pay_rev_c402] (pr_review_comment:c402) Review on PR #18: Reject database-level transaction locks for idempotency: Using row-level database locks (SELECT FOR UPDATE) on the checkout table creates bottleneck deadlock risks during sales. Redis key-value atomicity is required.
[evt_why_pay_adr_03] (adr:docs/adr/0003-webhook-first-confirmation.md) ADR 0003: Webhook-First Asynchronous Order Confirmation: Status: accepted

Context:
Sync browser checkout redirect was dropping orders when mobile users closed Safari before the success return page loaded.

Decision:
Treat Stripe payment_intent.succeeded webhook event as the single source of truth for confirming orders rather than client-side redirects.

Consequences:
- Zero lost orders from closed tabs.
- Frontend displays pending state and listens via
[evt_why_pay_pr_22] (github_pr:22) PR #22: Webhook signature verification with HMAC-SHA256 and replay tolerance: Validates Stripe-Signature header with HMAC-SHA256 secret key and enforces a 300-second maximum timestamp drift window to prevent replay attacks.
[evt_why_pay_rev_c450] (pr_review_comment:c450) Review on PR #22: Reject skipping signature verification in development: Bypassing webhook signature checks via a debug flag risks shipping unverified endpoints to production. Verification must run in all environments with test keys.
[evt_why_pay_adr_04] (adr:docs/adr/0004-partial-refund-support.md) ADR 0004: Support Partial Refunds with Line-Item Reversal Ledger: Status: accepted

Context:
Customers returning one item out of a multi-item purchase required customer support intervention because the system only supported full-order voiding.

Decision:
Implement immutable append-only line-item reversal records tracking fractional refunds against order authorization totals.

Consequences:
- Eliminates manual support overrides for returns.
- Prevents cumulative 
[evt_why_pay_issue_11] (github_issue:11) Issue #11: Floating point rounding discrepancies during multi-currency partial refunds: Using standard IEEE 754 float types caused a 1-cent mismatch ($19.99 vs $19.989999) between partial refund sum and total charge.
[evt_why_pay_pr_29] (github_pr:29) PR #29: Migrate refund math to integer cents and Decimal representation (Closes #11): Converts all monetary fields to 64-bit integer minor currency units (cents) and Python Decimal to prevent floating point inaccuracies.
[evt_why_pay_rev_c505] (pr_review_comment:c505) Review on PR #29: Reject client-supplied refund timestamps: Relying on client timestamps allows fraudulent out-of-order refund attempts. Timestamps must strictly be generated by server UTC monotonic clock.
[evt_why_pay_issue_19] (github_issue:19) Issue #19: Toxic malformed webhook payloads causing infinite queue retry loops: Unparseable webhook payload triggered an unhandled exception causing RabbitMQ consumer to continually NACK and requeue, stalling normal processing.
[evt_why_pay_pr_35] (github_pr:35) PR #35: Route unparseable webhook messages to Dead Letter Queue after 3 failed deliveries (Closes #19): Configures DLQ with max-retries=3. Stalls are avoided by parking invalid messages for engineer inspection without blocking main line.
[evt_why_pay_adr_05] (adr:docs/adr/0005-pci-token-vault.md) ADR 0005: Dual-token vault encryption for PCI-DSS compliance: Status: accepted

Context:
PCI-DSS Scope Level 1 audit requires payment card numbers to never enter merchant application server memory or disk storage.

Decision:
Use Stripe Elements tokenization directly in client browser, receiving only opaque payment_method_id tokens on payment-core backend.

Consequences:
- Achieves PCI SAQ A eligibility, drastically reducing compliance overhead.
- Eliminates 
[evt_why_pay_rev_c610] (pr_review_comment:c610) Review on PR #38: Reject caching unencrypted CVV in memory: Storing raw CVVs even temporarily in Redis or local process memory is a direct violation of PCI-DSS requirement 3.2. Prohibit all CVV persistence.
```

---

### Trial 31: Question `WB_CLI_TEST_NEG_08`

- **Repository:** `cli/cli`
- **Type:** Negative (Unrecorded Topic)
- **Expected State:** `none`
- **Expected Evidence Events:** `evt_why_cli_issue_412`
- **Ground Truth Summary:** Mention without decision; 'pass' was mentioned in discussion, but zalando/go-keyring OS keychain was implemented.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cli/cli'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Did issue #412 discussions decide to adopt GnuPG pass password manager for token persistence?

Event Stream:
[evt_why_cli_rfc_01] (adr:docs/rfc/001-keyring-credentials.md) RFC 001: Secure OAuth Token Storage using Native OS Keyrings: Status: accepted

Context:
Storing GitHub OAuth tokens in plaintext YAML config files (~/.config/gh/hosts.yml) leaves developer credentials vulnerable to unauthorized local processes.

Decision:
Integrate native OS keychain/keyring providers (macOS Keychain, Windows Credential Manager, Linux SecretService) as default secure token storage.

Consequences:
- Zero plaintext credential storage on disk.
[evt_why_cli_issue_412] (github_issue:412) Issue #412: Plaintext tokens exposed in process environment variables and config files: Security audit noted that gh auth login stores tokens in world-readable ~/.config/gh/config.yml. Keyring integration requested.
[evt_why_cli_pr_518] (github_pr:518) PR #518: Add zalando/go-keyring provider for auth token persistence (Closes #412): Implements RFC 001. Migrates token storage to native OS keychain with graceful fallback to file store.
[evt_why_cli_rev_c601] (pr_review_comment:c601) Review on PR #518: Reject custom symmetric encryption key on disk: Custom symmetric key encryption stored next to the ciphertext offers zero additional security. We must use OS-level protected credentials.
[evt_why_cli_rfc_03] (adr:docs/rfc/003-extension-isolation.md) RFC 003: Subprocess Extension Execution Model with Scoped Token Environment: Status: accepted

Context:
Executing third-party gh extensions inside the main process runtime risks memory contamination and uncontrolled privilege escalation.

Decision:
Execute extensions as isolated external child subprocesses communicating via standard input/output with stripped environment variables.

Consequences:
- Protects host CLI process memory.
- Prevents extension crashes from termina
[evt_why_cli_rfc_02] (adr:docs/rfc/002-graphql-query-batching.md) RFC 002: GraphQL Query Batching and Fragment Reuse for Repositories: Status: accepted

Context:
Listing 30 pull requests previously executed 30 separate REST requests to fetch review statuses, causing high latency and rate limit depletion.

Decision:
Consolidate GitHub API access through GraphQL queries using reusable fragments and connection paging.

Consequences:
- Latency reduced from 3.2s to 420ms for PR lists.
- Single API call quota unit consumed per page.
[evt_why_cli_issue_480] (github_issue:480) Issue #480: N+1 REST API roundtrips during repo list with pull requests: Running gh pr list on repositories with extensive checks resulted in secondary API queries per line item exceeding the 5,000 req/hr rate limit.
[evt_why_cli_pr_592] (github_pr:592) PR #592: Batch repository and issue queries using GraphQL fragments (Closes #480): Implements RFC 002. Replaces REST loops with single paginated GraphQL queries fetching comments, reviews, and status rollups in one payload.
[evt_why_cli_issue_550] (github_issue:550) Issue #550: Extension crash corrupts parent terminal state and escapes PATH: Extensions invoking raw exec commands leaked file descriptors and left raw terminal mode active on fatal signal crashes.
[evt_why_cli_pr_670] (github_pr:670) PR #670: Fork-exec child subprocess isolation with restricted inherited env for extensions (Closes #550): Implements RFC 003. Child process manager cleans up terminal modes on SIGINT/SIGTERM and restricts PATH lookup to extension directory.
[evt_why_cli_rev_c712] (pr_review_comment:c712) Review on PR #670: Reject executing third-party extensions via in-process Go plugins: Go dynamic plugin loading requires exact compiler and dependency ABI matches and allows arbitrary memory access. External subprocess isolation is non-negotiable.
[evt_why_cli_rfc_04] (adr:docs/rfc/004-termenv-formatting.md) RFC 004: Terminal Color and Hyperlink Detection via termenv: Status: accepted

Context:
Hardcoded ANSI escape codes corrupted tabular output when piping to external commands (grep, awk, jq) or running in CI logs.

Decision:
Use termenv library to inspect terminal color profile, automatically stripping styling when stdout is not a TTY or NO_COLOR is set.

Consequences:
- Clean machine-readable output in scripts.
- Rich interactive color and OSC 8 hyperlinks 
[evt_why_cli_issue_620] (github_issue:620) Issue #620: Broken ANSI escape sequences when piping gh output to jq and grep: Users scripting gh pr list | jq . experienced JSON syntax errors because color escape sequences were embedded inside fields.
[evt_why_cli_pr_735] (github_pr:735) PR #735: Auto-detect TTY and disable ANSI formatting in non-interactive pipelines (Closes #620): Implements RFC 004. Replaces hardcoded escape codes with IOStreams ColorEnabled check and respects CLICOLOR / NO_COLOR standard env vars.
[evt_why_cli_rfc_05] (adr:docs/rfc/005-git-credential-helper.md) RFC 005: Git Credential Helper Protocol Provider: Status: accepted

Context:
Users running git clone after authenticating via gh auth login were prompted again by Git for their username and password.

Decision:
Implement gh auth git-credential command implementing the standard Git credential helper protocol responding to get, store, and erase.

Consequences:
- Transparent authentication for all git operations.
- Reuses secure OAuth token stored i
[evt_why_cli_pr_810] (github_pr:810) PR #810: Implementation of gh auth git-credential helper protocol: Implements RFC 005. Configures git credential helper entry in global .gitconfig during gh auth login setup.
[evt_why_cli_rev_c840] (pr_review_comment:c840) Review on PR #810: Reject global auth token in HTTP GET query string: Passing tokens in URL query parameters exposes them in web server access logs and proxy history. All authentication must strictly use Authorization: Bearer HTTP header.
[evt_why_cli_issue_780] (github_issue:780) Issue #780: Browser open failure in headless SSH and cloud container environments: Running gh auth login on remote headless EC2 instances hung indefinitely attempting to open xdg-open desktop browser.
[evt_why_cli_pr_920] (github_pr:920) PR #920: OAuth Device Code flow fallback for headless SSH sessions (Closes #780): Detects lack of display server or SSH session and displays 8-digit one-time device code with github.com/login/device URL for secondary device authentication.
```

---

### Trial 32: Question `WB_PAY_TEST_NEG_03`

- **Repository:** `acme-ecommerce/payment-core`
- **Type:** Negative (Unrecorded Topic)
- **Expected State:** `none`
- **Expected Evidence Events:** `None`
- **Ground Truth Summary:** No recorded decision; PostgreSQL with async connection pooling is the primary database.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'acme-ecommerce/payment-core'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Why was Apache Cassandra chosen over PostgreSQL for payment database persistence?

Event Stream:
[evt_why_pay_adr_01] (adr:docs/adr/0001-stripe-payment-migration.md) ADR 0001: Migrate from Legacy Braintree to Stripe Payment Intents API: Status: accepted

Context:
Legacy Braintree integration does not support European 3D Secure 2 authentication and suffers from elevated drop-off during checkout.

Decision:
Migrate checkout payment processing to Stripe Payment Intents with asynchronous webhook settlement.

Consequences:
- Full 3DS2 compliance.
- Checkout authorization latency reduced to <800ms.
- Requires webhook listener for async
[evt_why_pay_issue_08] (github_issue:8) Issue #8: Stripe API 429 Rate Limits encountered during flash sale traffic: During peak traffic burst, worker threads made simultaneous calls to Stripe charges API exceeding the 100 req/sec rate limit without jittered exponential backoff.
[evt_why_pay_pr_14] (github_pr:14) PR #14: Implement Exponential Backoff with Full Jitter for Stripe API (Closes #8): Adds decorator with decorator-level exponential backoff with full jitter (Decorrelated Jitter algorithm). Retries up to 4 times before failing.
[evt_why_pay_rev_c301] (pr_review_comment:c301) Review on PR #14: Reject fixed interval retries: Fixed 500ms sleep will create thundering herd when Stripe recovers. We must reject fixed sleep in favor of exponential backoff with randomized full jitter.
[evt_why_pay_adr_02] (adr:docs/adr/0002-webhook-idempotency.md) ADR 0002: Use Redis Distributed Lock and Idempotency Key for Webhooks: Status: accepted

Context:
Stripe webhook delivery guarantees at-least-once delivery. Duplicate payment.succeeded events caused double order fulfillment.

Decision:
Store processed Stripe event_ids in Redis with a 24-hour TTL and acquire a distributed mutex lock before processing webhook payloads.

Consequences:
- Zero duplicate order fulfillments.
- Redis availability required for payment reconci
[evt_why_pay_commit_7a] (git_commit:7a8b9c0d1e2f3a4b) feat(database): migrate to SQLAlchemy async connection pool with PgBouncer: Replaces raw psycopg2 connection per request with async connection pool. Reduces connection pool exhaustion under 2,000 checkout req/sec.
[evt_why_pay_issue_05] (github_issue:5) Issue #5: Duplicate customer charges under concurrent checkout clicks: Impatient users double clicking Pay Now sent parallel requests to /checkout initiating two distinct payment authorization transactions.
[evt_why_pay_pr_18] (github_pr:18) PR #18: Idempotency-Key Header Middleware with SHA-256 Request Hashing (Closes #5): Introduces Idempotency-Key HTTP header middleware computing SHA-256 digest of payload. Cache hit returns cached HTTP response immediately.
[evt_why_pay_rev_c402] (pr_review_comment:c402) Review on PR #18: Reject database-level transaction locks for idempotency: Using row-level database locks (SELECT FOR UPDATE) on the checkout table creates bottleneck deadlock risks during sales. Redis key-value atomicity is required.
[evt_why_pay_adr_03] (adr:docs/adr/0003-webhook-first-confirmation.md) ADR 0003: Webhook-First Asynchronous Order Confirmation: Status: accepted

Context:
Sync browser checkout redirect was dropping orders when mobile users closed Safari before the success return page loaded.

Decision:
Treat Stripe payment_intent.succeeded webhook event as the single source of truth for confirming orders rather than client-side redirects.

Consequences:
- Zero lost orders from closed tabs.
- Frontend displays pending state and listens via
[evt_why_pay_pr_22] (github_pr:22) PR #22: Webhook signature verification with HMAC-SHA256 and replay tolerance: Validates Stripe-Signature header with HMAC-SHA256 secret key and enforces a 300-second maximum timestamp drift window to prevent replay attacks.
[evt_why_pay_rev_c450] (pr_review_comment:c450) Review on PR #22: Reject skipping signature verification in development: Bypassing webhook signature checks via a debug flag risks shipping unverified endpoints to production. Verification must run in all environments with test keys.
[evt_why_pay_adr_04] (adr:docs/adr/0004-partial-refund-support.md) ADR 0004: Support Partial Refunds with Line-Item Reversal Ledger: Status: accepted

Context:
Customers returning one item out of a multi-item purchase required customer support intervention because the system only supported full-order voiding.

Decision:
Implement immutable append-only line-item reversal records tracking fractional refunds against order authorization totals.

Consequences:
- Eliminates manual support overrides for returns.
- Prevents cumulative 
[evt_why_pay_issue_11] (github_issue:11) Issue #11: Floating point rounding discrepancies during multi-currency partial refunds: Using standard IEEE 754 float types caused a 1-cent mismatch ($19.99 vs $19.989999) between partial refund sum and total charge.
[evt_why_pay_pr_29] (github_pr:29) PR #29: Migrate refund math to integer cents and Decimal representation (Closes #11): Converts all monetary fields to 64-bit integer minor currency units (cents) and Python Decimal to prevent floating point inaccuracies.
[evt_why_pay_rev_c505] (pr_review_comment:c505) Review on PR #29: Reject client-supplied refund timestamps: Relying on client timestamps allows fraudulent out-of-order refund attempts. Timestamps must strictly be generated by server UTC monotonic clock.
[evt_why_pay_issue_19] (github_issue:19) Issue #19: Toxic malformed webhook payloads causing infinite queue retry loops: Unparseable webhook payload triggered an unhandled exception causing RabbitMQ consumer to continually NACK and requeue, stalling normal processing.
[evt_why_pay_pr_35] (github_pr:35) PR #35: Route unparseable webhook messages to Dead Letter Queue after 3 failed deliveries (Closes #19): Configures DLQ with max-retries=3. Stalls are avoided by parking invalid messages for engineer inspection without blocking main line.
[evt_why_pay_adr_05] (adr:docs/adr/0005-pci-token-vault.md) ADR 0005: Dual-token vault encryption for PCI-DSS compliance: Status: accepted

Context:
PCI-DSS Scope Level 1 audit requires payment card numbers to never enter merchant application server memory or disk storage.

Decision:
Use Stripe Elements tokenization directly in client browser, receiving only opaque payment_method_id tokens on payment-core backend.

Consequences:
- Achieves PCI SAQ A eligibility, drastically reducing compliance overhead.
- Eliminates 
[evt_why_pay_rev_c610] (pr_review_comment:c610) Review on PR #38: Reject caching unencrypted CVV in memory: Storing raw CVVs even temporarily in Redis or local process memory is a direct violation of PCI-DSS requirement 3.2. Prohibit all CVV persistence.
```

---

### Trial 33: Question `WB_CLI_TEST_NEG_12`

- **Repository:** `cli/cli`
- **Type:** Negative (Unrecorded Topic)
- **Expected State:** `none`
- **Expected Evidence Events:** `evt_why_cli_pr_735`
- **Ground Truth Summary:** Mention without decision; Bubble Tea was mentioned in review discussion, but termenv TTY detection was retained.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cli/cli'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Was Bubble Tea TUI framework adopted for rendering terminal output in PR #735?

Event Stream:
[evt_why_cli_rfc_01] (adr:docs/rfc/001-keyring-credentials.md) RFC 001: Secure OAuth Token Storage using Native OS Keyrings: Status: accepted

Context:
Storing GitHub OAuth tokens in plaintext YAML config files (~/.config/gh/hosts.yml) leaves developer credentials vulnerable to unauthorized local processes.

Decision:
Integrate native OS keychain/keyring providers (macOS Keychain, Windows Credential Manager, Linux SecretService) as default secure token storage.

Consequences:
- Zero plaintext credential storage on disk.
[evt_why_cli_issue_412] (github_issue:412) Issue #412: Plaintext tokens exposed in process environment variables and config files: Security audit noted that gh auth login stores tokens in world-readable ~/.config/gh/config.yml. Keyring integration requested.
[evt_why_cli_pr_518] (github_pr:518) PR #518: Add zalando/go-keyring provider for auth token persistence (Closes #412): Implements RFC 001. Migrates token storage to native OS keychain with graceful fallback to file store.
[evt_why_cli_rev_c601] (pr_review_comment:c601) Review on PR #518: Reject custom symmetric encryption key on disk: Custom symmetric key encryption stored next to the ciphertext offers zero additional security. We must use OS-level protected credentials.
[evt_why_cli_rfc_03] (adr:docs/rfc/003-extension-isolation.md) RFC 003: Subprocess Extension Execution Model with Scoped Token Environment: Status: accepted

Context:
Executing third-party gh extensions inside the main process runtime risks memory contamination and uncontrolled privilege escalation.

Decision:
Execute extensions as isolated external child subprocesses communicating via standard input/output with stripped environment variables.

Consequences:
- Protects host CLI process memory.
- Prevents extension crashes from termina
[evt_why_cli_rfc_02] (adr:docs/rfc/002-graphql-query-batching.md) RFC 002: GraphQL Query Batching and Fragment Reuse for Repositories: Status: accepted

Context:
Listing 30 pull requests previously executed 30 separate REST requests to fetch review statuses, causing high latency and rate limit depletion.

Decision:
Consolidate GitHub API access through GraphQL queries using reusable fragments and connection paging.

Consequences:
- Latency reduced from 3.2s to 420ms for PR lists.
- Single API call quota unit consumed per page.
[evt_why_cli_issue_480] (github_issue:480) Issue #480: N+1 REST API roundtrips during repo list with pull requests: Running gh pr list on repositories with extensive checks resulted in secondary API queries per line item exceeding the 5,000 req/hr rate limit.
[evt_why_cli_pr_592] (github_pr:592) PR #592: Batch repository and issue queries using GraphQL fragments (Closes #480): Implements RFC 002. Replaces REST loops with single paginated GraphQL queries fetching comments, reviews, and status rollups in one payload.
[evt_why_cli_issue_550] (github_issue:550) Issue #550: Extension crash corrupts parent terminal state and escapes PATH: Extensions invoking raw exec commands leaked file descriptors and left raw terminal mode active on fatal signal crashes.
[evt_why_cli_pr_670] (github_pr:670) PR #670: Fork-exec child subprocess isolation with restricted inherited env for extensions (Closes #550): Implements RFC 003. Child process manager cleans up terminal modes on SIGINT/SIGTERM and restricts PATH lookup to extension directory.
[evt_why_cli_rev_c712] (pr_review_comment:c712) Review on PR #670: Reject executing third-party extensions via in-process Go plugins: Go dynamic plugin loading requires exact compiler and dependency ABI matches and allows arbitrary memory access. External subprocess isolation is non-negotiable.
[evt_why_cli_rfc_04] (adr:docs/rfc/004-termenv-formatting.md) RFC 004: Terminal Color and Hyperlink Detection via termenv: Status: accepted

Context:
Hardcoded ANSI escape codes corrupted tabular output when piping to external commands (grep, awk, jq) or running in CI logs.

Decision:
Use termenv library to inspect terminal color profile, automatically stripping styling when stdout is not a TTY or NO_COLOR is set.

Consequences:
- Clean machine-readable output in scripts.
- Rich interactive color and OSC 8 hyperlinks 
[evt_why_cli_issue_620] (github_issue:620) Issue #620: Broken ANSI escape sequences when piping gh output to jq and grep: Users scripting gh pr list | jq . experienced JSON syntax errors because color escape sequences were embedded inside fields.
[evt_why_cli_pr_735] (github_pr:735) PR #735: Auto-detect TTY and disable ANSI formatting in non-interactive pipelines (Closes #620): Implements RFC 004. Replaces hardcoded escape codes with IOStreams ColorEnabled check and respects CLICOLOR / NO_COLOR standard env vars.
[evt_why_cli_rfc_05] (adr:docs/rfc/005-git-credential-helper.md) RFC 005: Git Credential Helper Protocol Provider: Status: accepted

Context:
Users running git clone after authenticating via gh auth login were prompted again by Git for their username and password.

Decision:
Implement gh auth git-credential command implementing the standard Git credential helper protocol responding to get, store, and erase.

Consequences:
- Transparent authentication for all git operations.
- Reuses secure OAuth token stored i
[evt_why_cli_pr_810] (github_pr:810) PR #810: Implementation of gh auth git-credential helper protocol: Implements RFC 005. Configures git credential helper entry in global .gitconfig during gh auth login setup.
[evt_why_cli_rev_c840] (pr_review_comment:c840) Review on PR #810: Reject global auth token in HTTP GET query string: Passing tokens in URL query parameters exposes them in web server access logs and proxy history. All authentication must strictly use Authorization: Bearer HTTP header.
[evt_why_cli_issue_780] (github_issue:780) Issue #780: Browser open failure in headless SSH and cloud container environments: Running gh auth login on remote headless EC2 instances hung indefinitely attempting to open xdg-open desktop browser.
[evt_why_cli_pr_920] (github_pr:920) PR #920: OAuth Device Code flow fallback for headless SSH sessions (Closes #780): Detects lack of display server or SSH session and displays 8-digit one-time device code with github.com/login/device URL for secondary device authentication.
```

---

### Trial 34: Question `WB_PAY_TEST_NEG_07`

- **Repository:** `acme-ecommerce/payment-core`
- **Type:** Negative (Unrecorded Topic)
- **Expected State:** `none`
- **Expected Evidence Events:** `None`
- **Ground Truth Summary:** No recorded decision; wallet balances are recorded in PostgreSQL ledger.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'acme-ecommerce/payment-core'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Why was CouchDB adopted for storing customer multi-currency wallet balances?

Event Stream:
[evt_why_pay_adr_01] (adr:docs/adr/0001-stripe-payment-migration.md) ADR 0001: Migrate from Legacy Braintree to Stripe Payment Intents API: Status: accepted

Context:
Legacy Braintree integration does not support European 3D Secure 2 authentication and suffers from elevated drop-off during checkout.

Decision:
Migrate checkout payment processing to Stripe Payment Intents with asynchronous webhook settlement.

Consequences:
- Full 3DS2 compliance.
- Checkout authorization latency reduced to <800ms.
- Requires webhook listener for async
[evt_why_pay_issue_08] (github_issue:8) Issue #8: Stripe API 429 Rate Limits encountered during flash sale traffic: During peak traffic burst, worker threads made simultaneous calls to Stripe charges API exceeding the 100 req/sec rate limit without jittered exponential backoff.
[evt_why_pay_pr_14] (github_pr:14) PR #14: Implement Exponential Backoff with Full Jitter for Stripe API (Closes #8): Adds decorator with decorator-level exponential backoff with full jitter (Decorrelated Jitter algorithm). Retries up to 4 times before failing.
[evt_why_pay_rev_c301] (pr_review_comment:c301) Review on PR #14: Reject fixed interval retries: Fixed 500ms sleep will create thundering herd when Stripe recovers. We must reject fixed sleep in favor of exponential backoff with randomized full jitter.
[evt_why_pay_adr_02] (adr:docs/adr/0002-webhook-idempotency.md) ADR 0002: Use Redis Distributed Lock and Idempotency Key for Webhooks: Status: accepted

Context:
Stripe webhook delivery guarantees at-least-once delivery. Duplicate payment.succeeded events caused double order fulfillment.

Decision:
Store processed Stripe event_ids in Redis with a 24-hour TTL and acquire a distributed mutex lock before processing webhook payloads.

Consequences:
- Zero duplicate order fulfillments.
- Redis availability required for payment reconci
[evt_why_pay_commit_7a] (git_commit:7a8b9c0d1e2f3a4b) feat(database): migrate to SQLAlchemy async connection pool with PgBouncer: Replaces raw psycopg2 connection per request with async connection pool. Reduces connection pool exhaustion under 2,000 checkout req/sec.
[evt_why_pay_issue_05] (github_issue:5) Issue #5: Duplicate customer charges under concurrent checkout clicks: Impatient users double clicking Pay Now sent parallel requests to /checkout initiating two distinct payment authorization transactions.
[evt_why_pay_pr_18] (github_pr:18) PR #18: Idempotency-Key Header Middleware with SHA-256 Request Hashing (Closes #5): Introduces Idempotency-Key HTTP header middleware computing SHA-256 digest of payload. Cache hit returns cached HTTP response immediately.
[evt_why_pay_rev_c402] (pr_review_comment:c402) Review on PR #18: Reject database-level transaction locks for idempotency: Using row-level database locks (SELECT FOR UPDATE) on the checkout table creates bottleneck deadlock risks during sales. Redis key-value atomicity is required.
[evt_why_pay_adr_03] (adr:docs/adr/0003-webhook-first-confirmation.md) ADR 0003: Webhook-First Asynchronous Order Confirmation: Status: accepted

Context:
Sync browser checkout redirect was dropping orders when mobile users closed Safari before the success return page loaded.

Decision:
Treat Stripe payment_intent.succeeded webhook event as the single source of truth for confirming orders rather than client-side redirects.

Consequences:
- Zero lost orders from closed tabs.
- Frontend displays pending state and listens via
[evt_why_pay_pr_22] (github_pr:22) PR #22: Webhook signature verification with HMAC-SHA256 and replay tolerance: Validates Stripe-Signature header with HMAC-SHA256 secret key and enforces a 300-second maximum timestamp drift window to prevent replay attacks.
[evt_why_pay_rev_c450] (pr_review_comment:c450) Review on PR #22: Reject skipping signature verification in development: Bypassing webhook signature checks via a debug flag risks shipping unverified endpoints to production. Verification must run in all environments with test keys.
[evt_why_pay_adr_04] (adr:docs/adr/0004-partial-refund-support.md) ADR 0004: Support Partial Refunds with Line-Item Reversal Ledger: Status: accepted

Context:
Customers returning one item out of a multi-item purchase required customer support intervention because the system only supported full-order voiding.

Decision:
Implement immutable append-only line-item reversal records tracking fractional refunds against order authorization totals.

Consequences:
- Eliminates manual support overrides for returns.
- Prevents cumulative 
[evt_why_pay_issue_11] (github_issue:11) Issue #11: Floating point rounding discrepancies during multi-currency partial refunds: Using standard IEEE 754 float types caused a 1-cent mismatch ($19.99 vs $19.989999) between partial refund sum and total charge.
[evt_why_pay_pr_29] (github_pr:29) PR #29: Migrate refund math to integer cents and Decimal representation (Closes #11): Converts all monetary fields to 64-bit integer minor currency units (cents) and Python Decimal to prevent floating point inaccuracies.
[evt_why_pay_rev_c505] (pr_review_comment:c505) Review on PR #29: Reject client-supplied refund timestamps: Relying on client timestamps allows fraudulent out-of-order refund attempts. Timestamps must strictly be generated by server UTC monotonic clock.
[evt_why_pay_issue_19] (github_issue:19) Issue #19: Toxic malformed webhook payloads causing infinite queue retry loops: Unparseable webhook payload triggered an unhandled exception causing RabbitMQ consumer to continually NACK and requeue, stalling normal processing.
[evt_why_pay_pr_35] (github_pr:35) PR #35: Route unparseable webhook messages to Dead Letter Queue after 3 failed deliveries (Closes #19): Configures DLQ with max-retries=3. Stalls are avoided by parking invalid messages for engineer inspection without blocking main line.
[evt_why_pay_adr_05] (adr:docs/adr/0005-pci-token-vault.md) ADR 0005: Dual-token vault encryption for PCI-DSS compliance: Status: accepted

Context:
PCI-DSS Scope Level 1 audit requires payment card numbers to never enter merchant application server memory or disk storage.

Decision:
Use Stripe Elements tokenization directly in client browser, receiving only opaque payment_method_id tokens on payment-core backend.

Consequences:
- Achieves PCI SAQ A eligibility, drastically reducing compliance overhead.
- Eliminates 
[evt_why_pay_rev_c610] (pr_review_comment:c610) Review on PR #38: Reject caching unencrypted CVV in memory: Storing raw CVVs even temporarily in Redis or local process memory is a direct violation of PCI-DSS requirement 3.2. Prohibit all CVV persistence.
```

---

### Trial 35: Question `WB_CH_TEST_NEG_08`

- **Repository:** `cloud-hypervisor/cloud-hypervisor`
- **Type:** Negative (Unrecorded Topic)
- **Expected State:** `none`
- **Expected Evidence Events:** `evt_why_ch_issue_890`
- **Ground Truth Summary:** Mention without decision; ZFS ARC caching was mentioned in discussion, but no storage switch was decided.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cloud-hypervisor/cloud-hypervisor'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Did issue #890 discussions decide to adopt ZFS pool storage for guest memory swapping?

Event Stream:
[evt_why_ch_rfc_01] (adr:docs/designs/live-migration.md) Design: Pre-copy Live Migration with Dirty Page Tracking via KVM dirty ring: Status: accepted

Context:
Virtual machine live migration must minimize downtime below 50ms while transferring guest memory under active workloads.

Decision:
Implement iterative pre-copy migration using KVM dirty ring buffer instead of classic user-faultfd or dirty bitmap.

Consequences:
- Drastically reduces lock contention during memory dirty page capture.
- Guest pause time under 35ms on 10GbE
[evt_why_ch_pr_1042] (github_pr:1042) PR #1042: Implement VirtIO Memory Ballooning with Page Reporting: Adds virtio-balloon device supporting automatic unused page reporting back to host hypervisor. Enables dynamic RAM overcommit without guest performance degradation.
[evt_why_ch_issue_890] (github_issue:890) Issue #890: Memory balloon deflation stalls under aggressive host memory pressure: When host demands quick reclamation, balloon thread deadlock occurred due to synchronous locking on memory allocation bus.
[evt_why_ch_rev_c502] (pr_review_comment:c502) Review on PR #1042: Reject synchronous balloon deflation: Synchronous deflation blocks guest vCPUs for up to 400ms. We must reject synchronous balloon worker in favor of asynchronous background worker thread.
[evt_why_ch_rfc_03] (adr:docs/designs/vhost-user-net.md) Design: Vhost-User Network Backend with Multi-Queue Support: Status: accepted

Context:
Standard TAP networking limits packet throughput to ~1.2 Mpps due to kernel context switching overhead.

Decision:
Implement vhost-user-net backend delegating packet processing to DPDK/OVS processes via shared memory queues.

Consequences:
- Achieves line-rate 10GbE throughput (>8 Mpps).
- Eliminates kernel networking path context switches.
[evt_why_ch_rfc_02] (adr:docs/designs/direct-kernel-boot.md) Design: Direct Linux Kernel Boot without Legacy BIOS/GRUB: Status: accepted

Context:
Booting a full SeaBIOS or UEFI image adds 500ms-2s of cold start latency to cloud hypervisor microVMs.

Decision:
Implement direct ELF/bzImage loader jumping straight into the Linux kernel entry point with boot_params setup.

Consequences:
- Sub-30ms VM boot times.
- Eliminates legacy BIOS real-mode emulation code from VMM.
[evt_why_ch_issue_940] (github_issue:940) Issue #940: High guest exit latency on unpinned multi-threaded vCPUs: vCPU threads migrating across NUMA nodes caused up to 300% tail latency jitter on latency-sensitive guest workloads.
[evt_why_ch_pr_1105] (github_pr:1105) PR #1105: CPU Pinning and NUMA Topology Node Binding (Closes #940): Allows operator to pin guest vCPUs to specific host physical cores and bind guest RAM to local host NUMA nodes using libc::sched_setaffinity.
[evt_why_ch_rev_c615] (pr_review_comment:c615) Review on PR #1105: Reject legacy floppy and IDE device emulation: Emulating legacy PC hardware (floppy, IDE, PS/2) contradicts Cloud Hypervisor's minimal attack surface goal. Only modern VirtIO and PCIe interfaces will be supported.
[evt_why_ch_rfc_04] (adr:docs/designs/virtio-fs.md) Design: VirtIO-FS Shared Host Filesystem with Direct Access (DAX) Window: Status: accepted

Context:
Container runtimes (Kata Containers) need efficient sharing of host root filesystems with minimal memory overhead.

Decision:
Support virtio-fs device with a dedicated DAX window mapping host page cache directly into guest physical address space.

Consequences:
- Zero guest page cache memory duplication.
- File reads bypass guest I/O path directly to host cache.
[evt_why_ch_issue_1015] (github_issue:1015) Issue #1015: Host file lock contention in virtio-fs shared directory mounts: Multiple concurrent containers writing to shared virtio-fs directory caused POSIX file lock contention in virtiofsd daemon.
[evt_why_ch_pr_1180] (github_pr:1180) PR #1180: PCIe Root Port Hotplug Support for VirtIO Devices: Adds ACPI PCI hotplug notifications and PCIe native hotplug controller allowing runtime addition and removal of network interfaces and disks.
[evt_why_ch_pr_1240] (github_pr:1240) PR #1240: Asynchronous Disk I/O via Linux io_uring Engine: Replaces threadpool synchronous pread/pwrite with io_uring submission/completion queue rings for virtio-block backend.
[evt_why_ch_rev_c720] (pr_review_comment:c720) Review on PR #1240: Reject unbounded polling loops in vhost worker: Spin-polling io_uring SQPOLL thread pegging 100% CPU on idle guests is prohibited. Eventfd notification must be used when queue is drained.
[evt_why_ch_pr_1312] (github_pr:1312) PR #1312: VFIO PCI Device Passthrough for GPU Workloads: Integrates VFIO Linux kernel API enabling secure hardware DMA remapping and MSI-X interrupt forwarding for dedicated guest GPUs and NVMe drives.
[evt_why_ch_rfc_05] (adr:docs/designs/acpi-ged.md) Design: ACPI Generic Event Device (GED) for System Notifications: Status: accepted

Context:
Handling power button, shutdown, and hotplug interrupts previously required complex proprietary DSDT methods.

Decision:
Adopt ACPI 5.0 Generic Event Device (GED) providing simplified interrupt-driven event signaling across x86_64 and AArch64.

Consequences:
- Unified event dispatch table across architectures.
- Removes ~1,200 lines of architecture-specific AML bytecode.
[evt_why_ch_issue_1120] (github_issue:1120) Issue #1120: Guest memory leak in balloon statistics driver queue: Periodic stat queue buffers allocated by guest kernel were leaked when host neglected to acknowledge polling rings.
[evt_why_ch_pr_1390] (github_pr:1390) PR #1390: MicroVM Minimal Device Tree Profile for Serverless Sandboxes: Configures minimal sandbox VM profile stripping ACPI tables and serial emulation, reducing guest boot time to 12ms for AWS Lambda style workloads.
```

---

### Trial 36: Question `WB_CH_TEST_NEG_01`

- **Repository:** `cloud-hypervisor/cloud-hypervisor`
- **Type:** Negative (Unrecorded Topic)
- **Expected State:** `none`
- **Expected Evidence Events:** `None`
- **Ground Truth Summary:** No recorded decision; Cloud Hypervisor uses standard open VFIO PCIe passthrough.

#### Copilot Prompt

```text
You are analyzing architectural decisions for repository 'cloud-hypervisor/cloud-hypervisor'.
Based strictly and only on the event stream below, answer the following architectural question.
Do not invent facts or cite events not present in the stream.

Question: Why did Cloud Hypervisor embed a proprietary binary NVIDIA kernel driver into the VMM?

Event Stream:
[evt_why_ch_rfc_01] (adr:docs/designs/live-migration.md) Design: Pre-copy Live Migration with Dirty Page Tracking via KVM dirty ring: Status: accepted

Context:
Virtual machine live migration must minimize downtime below 50ms while transferring guest memory under active workloads.

Decision:
Implement iterative pre-copy migration using KVM dirty ring buffer instead of classic user-faultfd or dirty bitmap.

Consequences:
- Drastically reduces lock contention during memory dirty page capture.
- Guest pause time under 35ms on 10GbE
[evt_why_ch_pr_1042] (github_pr:1042) PR #1042: Implement VirtIO Memory Ballooning with Page Reporting: Adds virtio-balloon device supporting automatic unused page reporting back to host hypervisor. Enables dynamic RAM overcommit without guest performance degradation.
[evt_why_ch_issue_890] (github_issue:890) Issue #890: Memory balloon deflation stalls under aggressive host memory pressure: When host demands quick reclamation, balloon thread deadlock occurred due to synchronous locking on memory allocation bus.
[evt_why_ch_rev_c502] (pr_review_comment:c502) Review on PR #1042: Reject synchronous balloon deflation: Synchronous deflation blocks guest vCPUs for up to 400ms. We must reject synchronous balloon worker in favor of asynchronous background worker thread.
[evt_why_ch_rfc_03] (adr:docs/designs/vhost-user-net.md) Design: Vhost-User Network Backend with Multi-Queue Support: Status: accepted

Context:
Standard TAP networking limits packet throughput to ~1.2 Mpps due to kernel context switching overhead.

Decision:
Implement vhost-user-net backend delegating packet processing to DPDK/OVS processes via shared memory queues.

Consequences:
- Achieves line-rate 10GbE throughput (>8 Mpps).
- Eliminates kernel networking path context switches.
[evt_why_ch_rfc_02] (adr:docs/designs/direct-kernel-boot.md) Design: Direct Linux Kernel Boot without Legacy BIOS/GRUB: Status: accepted

Context:
Booting a full SeaBIOS or UEFI image adds 500ms-2s of cold start latency to cloud hypervisor microVMs.

Decision:
Implement direct ELF/bzImage loader jumping straight into the Linux kernel entry point with boot_params setup.

Consequences:
- Sub-30ms VM boot times.
- Eliminates legacy BIOS real-mode emulation code from VMM.
[evt_why_ch_issue_940] (github_issue:940) Issue #940: High guest exit latency on unpinned multi-threaded vCPUs: vCPU threads migrating across NUMA nodes caused up to 300% tail latency jitter on latency-sensitive guest workloads.
[evt_why_ch_pr_1105] (github_pr:1105) PR #1105: CPU Pinning and NUMA Topology Node Binding (Closes #940): Allows operator to pin guest vCPUs to specific host physical cores and bind guest RAM to local host NUMA nodes using libc::sched_setaffinity.
[evt_why_ch_rev_c615] (pr_review_comment:c615) Review on PR #1105: Reject legacy floppy and IDE device emulation: Emulating legacy PC hardware (floppy, IDE, PS/2) contradicts Cloud Hypervisor's minimal attack surface goal. Only modern VirtIO and PCIe interfaces will be supported.
[evt_why_ch_rfc_04] (adr:docs/designs/virtio-fs.md) Design: VirtIO-FS Shared Host Filesystem with Direct Access (DAX) Window: Status: accepted

Context:
Container runtimes (Kata Containers) need efficient sharing of host root filesystems with minimal memory overhead.

Decision:
Support virtio-fs device with a dedicated DAX window mapping host page cache directly into guest physical address space.

Consequences:
- Zero guest page cache memory duplication.
- File reads bypass guest I/O path directly to host cache.
[evt_why_ch_issue_1015] (github_issue:1015) Issue #1015: Host file lock contention in virtio-fs shared directory mounts: Multiple concurrent containers writing to shared virtio-fs directory caused POSIX file lock contention in virtiofsd daemon.
[evt_why_ch_pr_1180] (github_pr:1180) PR #1180: PCIe Root Port Hotplug Support for VirtIO Devices: Adds ACPI PCI hotplug notifications and PCIe native hotplug controller allowing runtime addition and removal of network interfaces and disks.
[evt_why_ch_pr_1240] (github_pr:1240) PR #1240: Asynchronous Disk I/O via Linux io_uring Engine: Replaces threadpool synchronous pread/pwrite with io_uring submission/completion queue rings for virtio-block backend.
[evt_why_ch_rev_c720] (pr_review_comment:c720) Review on PR #1240: Reject unbounded polling loops in vhost worker: Spin-polling io_uring SQPOLL thread pegging 100% CPU on idle guests is prohibited. Eventfd notification must be used when queue is drained.
[evt_why_ch_pr_1312] (github_pr:1312) PR #1312: VFIO PCI Device Passthrough for GPU Workloads: Integrates VFIO Linux kernel API enabling secure hardware DMA remapping and MSI-X interrupt forwarding for dedicated guest GPUs and NVMe drives.
[evt_why_ch_rfc_05] (adr:docs/designs/acpi-ged.md) Design: ACPI Generic Event Device (GED) for System Notifications: Status: accepted

Context:
Handling power button, shutdown, and hotplug interrupts previously required complex proprietary DSDT methods.

Decision:
Adopt ACPI 5.0 Generic Event Device (GED) providing simplified interrupt-driven event signaling across x86_64 and AArch64.

Consequences:
- Unified event dispatch table across architectures.
- Removes ~1,200 lines of architecture-specific AML bytecode.
[evt_why_ch_issue_1120] (github_issue:1120) Issue #1120: Guest memory leak in balloon statistics driver queue: Periodic stat queue buffers allocated by guest kernel were leaked when host neglected to acknowledge polling rings.
[evt_why_ch_pr_1390] (github_pr:1390) PR #1390: MicroVM Minimal Device Tree Profile for Serverless Sandboxes: Configures minimal sandbox VM profile stripping ACPI tables and serial emulation, reducing guest boot time to 12ms for AWS Lambda style workloads.
```

---


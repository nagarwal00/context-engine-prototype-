# WhyBench Frozen Test Split Specification (`test_v2`)

> **Protocol Notice**: In accordance with Section 2.4 and Step 4.9 of `ANTIGRAVITY_HANDOFF_V2.md`, the `test_v2` split is permanently frozen. Questions were authored and verified **before** examining system outputs to prevent tuning overfitting.

---

## 1. Cryptographic Freeze Hashes (SHA-256)

| Asset | SHA-256 Digest | Status |
|---|---|:---:|
| **Full Questions Dataset** (`backend/evaluation/whybench/questions.json`) | `1e46e50dd8a35f6d6a7c33b7b5472521e982b4ff907cd91584a0bb962f9d94ab` | Frozen |
| **Test Split Subset (`test_v2`)** (Canonical JSON serialization) | `48c8e99e19cdf0e3069c39e51dbed7dcf6c3b3617927f1db4caf7559078f4a5b` | Frozen |

---

## 2. Dataset Composition (`test_v2`)

- **Total `test_v2` Questions**: 71 (100% verified)
- **Standard Positive Questions**: 26
- **Negative Refusal Questions**: 45 (15 per repository; 8 type (b) [53.3%], 7 type (a) [46.7%])

### Per-Repository Quotas (≥ 20 verified questions per repo):
1. `acme-ecommerce/payment-core`: **25 questions** (10 standard + 15 negative)
2. `cli/cli`: **23 questions** (8 standard + 15 negative)
3. `cloud-hypervisor/cloud-hypervisor`: **23 questions** (8 standard + 15 negative)

---

## 3. Runner Enforcement Rules

1. **Explicit Final Flag Required**: `tools/run_whybench.py` strictly refuses to evaluate `test_v2` (or `test`) without `--final`.
2. **Anti-Overfitting Protection**: `tools/run_whybench.py` strictly refuses to re-run `test_v2` if results already exist, unless `--force` is explicitly provided.
3. **No Modification**: Ground-truth questions in `test_v2` are immutable; changes alter the SHA-256 digest and cause `tools/validate_whybench.py` to fail immediately.
4. **Headline Reporting**: `test_v1` is retained as the pre-improvement baseline and `test_v2` serves as the headline benchmark evaluation result.

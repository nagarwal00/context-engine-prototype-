# User Study Tasks & Ground Truth Scoring Sheet

This document specifies the two evaluation tasks for the user study. Both tasks are drawn from the **development split** of the repository dataset.

---

## Task A: Payment Gateway Architecture Migration
- **Target Repository:** `acme-ecommerce/payment-core` (or demo sample repository)
- **Scenario:** You are a newly joined backend engineer reviewing the payment processing infrastructure.
- **Task Prompt:**
  > *"Find why the payment processing service migrated away from legacy Braintree to the Stripe Payment Intents API. Specifically answer:*
  > 1. *What primary business or compliance requirement triggered this migration?*
  > 2. *What performance or conversion issue did the team resolve by switching?*
  > 3. *What specific event or documentation artifact records this decision?"*
- **Time Limit:** 10 minutes (600 seconds).
- **Ground Truth Criteria for Correctness (`correct = 1`):**
  - **Requirement:** European 3D-Secure 2 (3DS2) regulatory compliance / Strong Customer Authentication (SCA).
  - **Performance/Conversion Factor:** High checkout drop-offs under legacy flow; Stripe sub-800ms authorization latency and inline modal authentication.
  - **Evidence Artifact:** ADR 0001 (`docs/adr/0001-stripe-payment-migration.md`) or corresponding architectural commit.
  - *Scoring:* Participant must correctly identify the 3DS2/SCA compliance driver and name the ADR or pull request.

---

## Task B: Webhook Deduplication and Idempotency
- **Target Repository:** `acme-ecommerce/payment-core`
- **Scenario:** Several customer tickets report duplicate charges occurring during flash sale promotions when users double-click checkout buttons.
- **Task Prompt:**
  > *"Investigate how the payment service prevents double charges and handles duplicate webhook deliveries:*
  > 1. *What synchronization mechanism was implemented to guarantee idempotency?*
  > 2. *Why were database row locks rejected as an alternative?*
  > 3. *What is the state of this decision (accepted, rejected, superseded)?"*
- **Time Limit:** 10 minutes (600 seconds).
- **Ground Truth Criteria for Correctness (`correct = 1`):**
  - **Mechanism:** Redis distributed locks with short TTL combined with idempotency key hashing (SHA-256 of payload/event-id).
  - **Rejected Alternative:** Database row locks (`SELECT ... FOR UPDATE`) were rejected due to lock contention and connection pool exhaustion under high concurrency.
  - **Decision State:** Accepted (and actively enforced).
  - *Scoring:* Participant must identify the distributed Redis lock/idempotency approach and the contention reason for rejecting DB row locks.

---

## Counterbalancing Schedule

| Participant ID | Task 1 (Tool) | Task 2 (Tool) |
|---|---|---|
| **P01** | Task A (**CIF Tool**) | Task B (**Baseline Search**) |
| **P02** | Task A (**Baseline Search**) | Task B (**CIF Tool**) |
| **P03** | Task A (**CIF Tool**) | Task B (**Baseline Search**) |
| **P04** | Task A (**Baseline Search**) | Task B (**CIF Tool**) |
| **P05** | Task A (**CIF Tool**) | Task B (**Baseline Search**) |
| **P06** | Task A (**Baseline Search**) | Task B (**CIF Tool**) |
| **P07** | Task A (**CIF Tool**) | Task B (**Baseline Search**) |
| **P08** | Task A (**Baseline Search**) | Task B (**CIF Tool**) |

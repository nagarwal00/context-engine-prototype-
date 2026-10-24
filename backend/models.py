"""
Context Intelligence Framework - Data Models
Implements Section 5 of docs/process/implementation.md
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import uuid
import datetime

def generate_uuid() -> str:
    return str(uuid.uuid4())

def current_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

@dataclass
class Event:
    """Section 5.1 Event Schema"""
    event_id: str = field(default_factory=generate_uuid)
    source_type: str = "git_commit" # git_commit | github_issue | github_pr | pr_review_comment | adr | doc
    source_id: str = ""
    source_url: str = "" # Mandatory, never null per Section 5.1
    repo: str = ""
    author: str = ""
    timestamp: str = field(default_factory=current_iso)
    title: Optional[str] = None
    body: str = ""
    artifacts_touched: List[str] = field(default_factory=list)
    parent_event_ids: List[str] = field(default_factory=list)
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AlternativeConsidered:
    description: str
    rejection_reason: Optional[str] = None
    evidence_event_ids: List[str] = field(default_factory=list)

@dataclass
class StateChange:
    state: str
    changed_at: str = field(default_factory=current_iso)
    changed_by: str = "system"
    notes: Optional[str] = None

ALLOWED_DECISION_STATES = {"proposed", "tested", "accepted", "rejected", "superseded", "reopened"}
ALLOWED_EVIDENCE_ASSESSMENTS = {"strong", "moderate", "weak", "insufficient", "contradicted"}
ALLOWED_FRESHNESS = {"fresh", "stale", "under_review", "revalidated"}

@dataclass
class Decision:
    """Section 5.2 Decision Schema & Step 2.1 State Model"""
    decision_id: str = field(default_factory=generate_uuid)
    title: str = ""
    state: str = "proposed" # proposed | tested | accepted | rejected | superseded | reopened
    evidence_assessment: str = "insufficient" # strong | moderate | weak | insufficient | contradicted
    freshness: str = "fresh" # fresh | stale | under_review | revalidated
    state_history: List[Dict[str, Any]] = field(default_factory=list)
    made_by: str = ""
    made_at: str = field(default_factory=current_iso)
    artifacts_affected: List[str] = field(default_factory=list) # entity_ids
    alternatives_considered: List[Dict[str, Any]] = field(default_factory=list)
    rationale: str = ""
    evidence_event_ids: List[str] = field(default_factory=list)
    supersedes_decision_id: Optional[str] = None
    superseded_by_decision_id: Optional[str] = None
    confidence: float = 0.8
    review_status: str = "pending_review" # auto_confirmed | pending_review | human_confirmed | human_rejected | human_merged | human_corrected
    repo: str = ""

    def __post_init__(self):
        # Compatibility alias for legacy 'unresolved' state
        if self.state == "unresolved":
            self.state = "proposed"
            self.evidence_assessment = "insufficient"

    def validate_invariants(self):
        """
        Mechanical enforcement of Step 2.1 & Section 13:
        - state in proposed | tested | accepted | rejected | superseded | reopened
        - evidence_assessment in strong | moderate | weak | insufficient | contradicted
        - freshness in fresh | stale | under_review | revalidated
        - states tested, accepted, rejected, superseded require >= 1 evidence event.
        - proposed and reopened may have none, but then evidence_assessment must be insufficient.
        """
        if self.state not in ALLOWED_DECISION_STATES:
            raise ValueError(
                f"Invalid decision state: '{self.state}'. Must be one of {sorted(ALLOWED_DECISION_STATES)}"
            )
        if self.evidence_assessment not in ALLOWED_EVIDENCE_ASSESSMENTS:
            raise ValueError(
                f"Invalid evidence_assessment: '{self.evidence_assessment}'. Must be one of {sorted(ALLOWED_EVIDENCE_ASSESSMENTS)}"
            )
        if self.freshness not in ALLOWED_FRESHNESS:
            raise ValueError(
                f"Invalid freshness: '{self.freshness}'. Must be one of {sorted(ALLOWED_FRESHNESS)}"
            )

        if self.state in ("tested", "accepted", "rejected", "superseded"):
            if len(self.evidence_event_ids) == 0:
                raise ValueError(
                    f"Invariant Violation: Decision '{self.title}' ({self.decision_id}) has state='{self.state}' "
                    "but contains NO evidence_event_ids. Evidence invariant requires >= 1 evidence event."
                )
        elif self.state in ("proposed", "reopened"):
            if len(self.evidence_event_ids) == 0 and self.evidence_assessment != "insufficient":
                raise ValueError(
                    f"Invariant Violation: Decision '{self.title}' ({self.decision_id}) has state='{self.state}' "
                    f"with 0 evidence events, so evidence_assessment must be 'insufficient', got '{self.evidence_assessment}'."
                )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Entity:
    """Section 5.3 Entity Schema (resolved code artifact)"""
    entity_id: str = field(default_factory=generate_uuid)
    entity_type: str = "file" # repository | module | file | function | dependency | config
    canonical_path: str = "" # e.g. 'src/thermal/control.py::regulate_temperature'
    aliases: List[str] = field(default_factory=list)
    repo: str = ""
    repo_full_name: Optional[str] = None
    current_state_summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Edge:
    """Section 5.4 Edge Schema (temporal context graph)"""
    edge_id: str = field(default_factory=generate_uuid)
    edge_type: str = "affects" # caused_by | supersedes | affects | discussed_in | evidenced_by | conflicts_with | drifts_from
    from_id: str = ""
    from_type: str = "decision" # decision | entity | event
    to_id: str = ""
    to_type: str = "entity" # decision | entity | event
    valid_from: str = field(default_factory=current_iso)
    valid_to: Optional[str] = None # null means currently valid
    repo_full_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Identity:
    """Section 6.5 Identity resolution mapping"""
    canonical_id: str
    display_name: str
    git_emails: List[str] = field(default_factory=list)
    github_logins: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class GuardRule:
    """Section 5.1 Decision Guard Rule & Decision Constraint (Step 3.4)"""
    rule_id: str = field(default_factory=generate_uuid)
    decision_id: str = ""
    rule_type: str = "forbid_import" # forbid_import | require_import | forbid_pattern | config_value
    params: Dict[str, Any] = field(default_factory=dict)
    status: str = "proposed" # proposed | active | disabled
    created_by: str = "system"
    created_at: str = field(default_factory=current_iso)
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    polarity: str = "must_not" # must | must_not
    applies_to: List[str] = field(default_factory=list) # entity IDs or path globs
    source: str = "proposed" # human | proposed

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Alias per docs/process/ANTIGRAVITY_HANDOFF_V2.md Step 3.4
DecisionConstraint = GuardRule



ALLOWED_CLAIM_TYPES = {"rationale", "alternative_rejected", "outcome", "constraint"}
ALLOWED_CLAIM_RELATIONS = {"direct", "indirect", "contradicting"}

@dataclass
class DecisionClaim:
    """Step 3.1 Claim-level unit of a decision"""
    claim_id: str = field(default_factory=generate_uuid)
    decision_id: str = ""
    claim_type: str = "rationale"  # rationale | alternative_rejected | outcome | constraint
    text: str = ""

    def validate(self):
        if self.claim_type not in ALLOWED_CLAIM_TYPES:
            raise ValueError(f"Invalid claim_type: '{self.claim_type}'. Must be one of {sorted(ALLOWED_CLAIM_TYPES)}")
        if not self.text or not self.text.strip():
            raise ValueError("Claim text cannot be empty.")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ClaimEvidence:
    """Step 3.1 Claim-level evidence link with passage offset and source group"""
    claim_id: str = ""
    event_id: str = ""
    relation: str = "direct"  # direct | indirect | contradicting
    passage_text: Optional[str] = None
    passage_start: Optional[int] = None
    passage_end: Optional[int] = None
    source_group: str = ""

    def validate(self):
        if self.relation not in ALLOWED_CLAIM_RELATIONS:
            raise ValueError(f"Invalid relation: '{self.relation}'. Must be one of {sorted(ALLOWED_CLAIM_RELATIONS)}")
        if not self.source_group or not self.source_group.strip():
            raise ValueError("source_group cannot be empty.")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


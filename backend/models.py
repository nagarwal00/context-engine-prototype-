"""
Context Intelligence Framework - Data Models
Implements Section 5 of implementation.md
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

@dataclass
class Decision:
    """Section 5.2 Decision Schema"""
    decision_id: str = field(default_factory=generate_uuid)
    title: str = ""
    state: str = "proposed" # proposed | accepted | rejected | superseded | unresolved
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

    def validate_invariants(self):
        """
        Mechanical enforcement of Section 5.2 & Section 13:
        evidence_event_ids can never be empty for non-unresolved decisions!
        """
        if self.state != "unresolved" and len(self.evidence_event_ids) == 0:
            raise ValueError(
                f"Invariant Violation: Decision '{self.title}' ({self.decision_id}) has state='{self.state}' "
                "but contains NO evidence_event_ids. Section 5.2 requires at least one evidence link."
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
    """Section 5.1 Decision Guard Rule (Novelty Feature)"""
    rule_id: str = field(default_factory=generate_uuid)
    decision_id: str = ""
    rule_type: str = "forbid_import" # forbid_import | require_import | forbid_pattern | config_value
    params: Dict[str, Any] = field(default_factory=dict)
    status: str = "proposed" # proposed | active | disabled
    created_by: str = "system"
    created_at: str = field(default_factory=current_iso)
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


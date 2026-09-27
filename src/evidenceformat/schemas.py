"""
evidenceformat.schemas
Strict Pydantic v2 Canonical Schemas and Validation Models.
"""

from typing import List, Optional, Any
from datetime import datetime, timezone
import hashlib
from pydantic import BaseModel, Field, ConfigDict, field_validator


class Demographics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: Optional[int] = Field(default=None, ge=0, le=130, description="Age in years")
    sex: Optional[str] = Field(default=None, description="Biological sex (M/F/Unspecified)")

    @field_validator("sex", mode="before")
    @classmethod
    def validate_sex(cls, v: Any) -> Optional[str]:
        if v is None or v == "" or v == "N/A":
            return None
        v_upper = str(v).upper().strip()
        if v_upper in ["M", "MALE"]:
            return "M"
        elif v_upper in ["F", "FEMALE"]:
            return "F"
        return "U"


class RawEventInput(BaseModel):
    """Raw record ingested from CSV or raw REST payload."""
    model_config = ConfigDict(extra="ignore")

    event_id: str = Field(..., min_length=1)
    event_type: str = Field(...)
    patient_or_learner_id: str = Field(...)
    timestamp: str = Field(...)
    code: str = Field(default="")
    detail: str = Field(default="")
    age: Optional[str] = Field(default="")
    sex: Optional[str] = Field(default="")
    certainty_or_action: Optional[str] = Field(default="")
    dose_or_score: Optional[str] = Field(default="")
    competency_level: Optional[str] = Field(default="")
    feedback_text: Optional[str] = Field(default="")
    source_system: str = Field(default="UNKNOWN_SOURCE")
    evidence_refs: Optional[str] = Field(default="")


class CanonicalEvent(BaseModel):
    """Canonical Normalized Domain Entity."""
    model_config = ConfigDict(frozen=True)

    event_id: str
    event_type: str
    subject_id: str
    timestamp: str
    code: str
    detail: str
    nominative_label: str
    snomed_code: str
    demographics: Demographics
    action_or_certainty: Optional[str] = None
    dose_or_score: Optional[str] = None
    competency_level: Optional[str] = None
    feedback_text: Optional[str] = None
    source_system: str
    raw_payload_hash: str
    ingest_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    transform_version: str = "v1.0.0-pydantic2"


class AuditRecord(BaseModel):
    """Immutable Audit Ledger Entry with SHA-256 Hash Chaining."""
    model_config = ConfigDict(frozen=True)

    audit_id: str
    event_id: str
    event_type: str
    subject_id: str
    ingest_timestamp: str
    transform_version: str
    raw_payload_hash: str
    previous_record_hash: str
    record_hash: str
    normalized_event: CanonicalEvent
    confidence_score: float = Field(..., ge=0.0, le=100.0)
    drug_interaction_warning: bool
    interaction_details: List[str]
    evidence_refs: List[str]
    explainability_text: str
    conflict_flag: bool

    @staticmethod
    def calculate_hash(
        audit_id: str,
        event_id: str,
        raw_payload_hash: str,
        confidence_score: float,
        drug_warning: bool,
        previous_record_hash: str
    ) -> str:
        """Computes deterministic SHA-256 hash for record chaining."""
        payload = f"{audit_id}|{event_id}|{raw_payload_hash}|{confidence_score:.2f}|{drug_warning}|{previous_record_hash}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
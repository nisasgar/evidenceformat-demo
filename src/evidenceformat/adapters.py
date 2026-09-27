"""
evidenceformat.adapters
Parsers for xAPI (IEEE LTSC / ADL) and FHIR R4 (HL7) Payloads.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from .schemas import RawEventInput


class XAPIActor(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: Optional[str] = None
    mbox: Optional[str] = None
    account: Optional[Dict[str, str]] = None


class XAPIVerb(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(..., json_schema_extra={"examples": ["http://adlnet.gov/expapi/verbs/attempted"]})
    display: Optional[Dict[str, str]] = None


class XAPIObject(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(..., json_schema_extra={"examples": ["http://example.org/assessments/quiz-101"]})
    definition: Optional[Dict[str, Any]] = None


class XAPIResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    score: Optional[Dict[str, Any]] = None
    completion: Optional[bool] = None
    success: Optional[bool] = None
    response: Optional[str] = None


class XAPIStatement(BaseModel):
    """Native xAPI Statement Representation."""
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., json_schema_extra={"examples": ["f81d4fae-7dec-11d0-a765-00a0c91e6bf6"]})
    actor: XAPIActor
    verb: XAPIVerb
    object: XAPIObject
    result: Optional[XAPIResult] = None
    timestamp: str = Field(..., json_schema_extra={"examples": ["2026-09-23T14:30:00Z"]})

    def to_raw_event(self) -> RawEventInput:
        """Adapts an xAPI statement into an EvidenceFormat RawEventInput."""
        actor_id = self.actor.mbox.replace("mailto:", "") if self.actor.mbox else (self.actor.name or "LRN_UNKNOWN")
        
        verb_part = self.verb.id.split("/")[-1]
        if "attempted" in verb_part or "completed" in verb_part:
            event_type = "AssessmentAttempt"
            code = "ASSESS_001"
        elif "mastered" in verb_part or "passed" in verb_part:
            event_type = "MasterySignal"
            code = "COMP_01"
        else:
            event_type = "Feedback"
            code = "FB_01"

        score_val = ""
        if self.result and self.result.score:
            score_val = str(self.result.score.get("scaled", self.result.score.get("raw", "")))

        detail_text = f"Verb: {verb_part} | Target: {self.object.id}"
        if self.object.definition and "name" in self.object.definition:
            detail_text += f" ({self.object.definition['name']})"

        return RawEventInput(
            event_id=self.id,
            event_type=event_type,
            patient_or_learner_id=actor_id,
            timestamp=self.timestamp,
            code=code,
            detail=detail_text,
            dose_or_score=score_val,
            source_system="xAPI_LRS_Webhook"
        )


class FHIRGenericResource(BaseModel):
    model_config = ConfigDict(extra="ignore")

    resourceType: str
    id: str
    subject: Optional[Dict[str, str]] = None
    patient: Optional[Dict[str, str]] = None
    code: Optional[Dict[str, Any]] = None
    medicationCodeableConcept: Optional[Dict[str, Any]] = None
    effectiveDateTime: Optional[str] = None
    authoredOn: Optional[str] = None

    def to_raw_event(self) -> RawEventInput:
        """Adapts a generic FHIR Resource into an EvidenceFormat RawEventInput."""
        patient_ref = "PAT_UNKNOWN"
        if self.subject and "reference" in self.subject:
            patient_ref = self.subject["reference"].replace("Patient/", "")
        elif self.patient and "reference" in self.patient:
            patient_ref = self.patient["reference"].replace("Patient/", "")

        primary_code = "I10"
        detail_str = f"FHIR {self.resourceType} Resource"

        if self.code and "coding" in self.code and len(self.code["coding"]) > 0:
            primary_code = self.code["coding"][0].get("code", "I10")
            detail_str = self.code["coding"][0].get("display", self.code.get("text", detail_str))
        elif self.medicationCodeableConcept and "coding" in self.medicationCodeableConcept:
            primary_code = "MED_REQ"
            detail_str = self.medicationCodeableConcept["coding"][0].get("display", "Prescribed Medication")

        event_type_map = {
            "Condition": "Diagnosis",
            "MedicationRequest": "MedicationChange",
            "Encounter": "Admission",
            "Observation": "Diagnosis"
        }

        return RawEventInput(
            event_id=f"FHIR_{self.resourceType}_{self.id}",
            event_type=event_type_map.get(self.resourceType, "Admission"),
            patient_or_learner_id=patient_ref,
            timestamp=self.effectiveDateTime or self.authoredOn or "2026-09-23T14:30:00Z",
            code=primary_code,
            detail=detail_str,
            source_system=f"FHIR_R4_{self.resourceType}"
        )
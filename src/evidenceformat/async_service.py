"""
evidenceformat.async_service
Asynchronous, Lock-Protected Pipeline Service for Real-Time Webhooks.
"""

import asyncio
import hashlib
from .schemas import RawEventInput, CanonicalEvent, Demographics, AuditRecord
from .engine import NominativeLabeler, CochraneEvidenceEngine
from .audit import CryptographicAuditLedger


class AsyncPipelineService:
    """Thread-safe Asynchronous Pipeline Service with Ledger Lock Management."""

    def __init__(self):
        self.ledger = CryptographicAuditLedger()
        self._lock = asyncio.Lock()

    async def process_raw_event_async(
        self,
        raw_input: RawEventInput,
        evidence_refs: str = ""
    ) -> AuditRecord:
        """
        Normalizes payload, applies evidence scoring, and appends to the
        cryptographic hash chain asynchronously under a mutex lock.
        """
        try:
            age_val = int(raw_input.age) if raw_input.age and raw_input.age.isdigit() else None
        except ValueError:
            age_val = None

        demographics = Demographics(age=age_val, sex=raw_input.sex)

        label, snomed = NominativeLabeler.resolve(raw_input.code, raw_input.detail)

        raw_payload_hash = hashlib.sha256(
            f"{raw_input.event_id}|{raw_input.code}|{raw_input.detail}".encode("utf-8")
        ).hexdigest()[:16]

        canonical = CanonicalEvent(
            event_id=raw_input.event_id,
            event_type=raw_input.event_type,
            subject_id=raw_input.patient_or_learner_id,
            timestamp=raw_input.timestamp,
            code=raw_input.code,
            detail=raw_input.detail,
            nominative_label=label,
            snomed_code=snomed,
            demographics=demographics,
            action_or_certainty=raw_input.certainty_or_action or None,
            dose_or_score=raw_input.dose_or_score or None,
            competency_level=raw_input.competency_level or None,
            feedback_text=raw_input.feedback_text or None,
            source_system=raw_input.source_system,
            raw_payload_hash=raw_payload_hash
        )

        score, refs, explain, conflict = CochraneEvidenceEngine.evaluate(canonical, evidence_refs)

        async with self._lock:
            record = self.ledger.append(
                canonical_event=canonical,
                confidence_score=score,
                drug_warning=False,
                interaction_details=[],
                evidence_refs=refs,
                explainability_text=explain,
                conflict_flag=conflict
            )

        return record


# Global Service Instance
async_pipeline = AsyncPipelineService()
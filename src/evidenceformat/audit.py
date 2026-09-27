"""
evidenceformat.audit
Cryptographic SHA-256 Hash Chain Manager and Ledger Validator.
"""

from typing import List, Dict, Tuple, Optional
from .schemas import AuditRecord, CanonicalEvent


class CryptographicAuditLedger:
    """Append-only cryptographic hash chain container."""

    def __init__(self, genesis_hash: Optional[str] = None):
        self._genesis_hash = genesis_hash or "0" * 64
        self._last_hash = self._genesis_hash
        self._chain: List[AuditRecord] = []
        self._store: Dict[str, AuditRecord] = {}

    @property
    def current_hash(self) -> str:
        return self._last_hash

    def append(
        self,
        canonical_event: CanonicalEvent,
        confidence_score: float,
        drug_warning: bool,
        interaction_details: List[str],
        evidence_refs: List[str],
        explainability_text: str,
        conflict_flag: bool
    ) -> AuditRecord:
        """Appends a new event and computes the SHA-256 link."""
        audit_id = f"AUDIT_{canonical_event.event_id}"
        
        record_hash = AuditRecord.calculate_hash(
            audit_id=audit_id,
            event_id=canonical_event.event_id,
            raw_payload_hash=canonical_event.raw_payload_hash,
            confidence_score=confidence_score,
            drug_warning=drug_warning,
            previous_record_hash=self._last_hash
        )

        record = AuditRecord(
            audit_id=audit_id,
            event_id=canonical_event.event_id,
            event_type=canonical_event.event_type,
            subject_id=canonical_event.subject_id,
            ingest_timestamp=canonical_event.ingest_timestamp,
            transform_version=canonical_event.transform_version,
            raw_payload_hash=canonical_event.raw_payload_hash,
            previous_record_hash=self._last_hash,
            record_hash=record_hash,
            normalized_event=canonical_event,
            confidence_score=confidence_score,
            drug_interaction_warning=drug_warning,
            interaction_details=interaction_details,
            evidence_refs=evidence_refs,
            explainability_text=explainability_text,
            conflict_flag=conflict_flag
        )

        self._chain.append(record)
        self._store[record.audit_id] = record
        self._last_hash = record_hash
        return record

    def verify_integrity(self) -> Tuple[bool, str]:
        """Traverses the ledger and verifies SHA-256 continuity."""
        expected_prev = self._genesis_hash
        for idx, record in enumerate(self._chain):
            if record.previous_record_hash != expected_prev:
                return False, f"Broken chain link at index {idx} ({record.audit_id})"
            
            recomputed = AuditRecord.calculate_hash(
                audit_id=record.audit_id,
                event_id=record.event_id,
                raw_payload_hash=record.raw_payload_hash,
                confidence_score=record.confidence_score,
                drug_warning=record.drug_interaction_warning,
                previous_record_hash=record.previous_record_hash
            )
            if recomputed != record.record_hash:
                return False, f"Tampered hash detected at index {idx} ({record.audit_id})"
            
            expected_prev = record.record_hash

        return True, f"Ledger integrity verified across {len(self._chain)} entries."

    def export_jsonl(self, filepath: str) -> None:
        """Exports verified audit records to an immutable JSONL file."""
        with open(filepath, "w", encoding="utf-8") as f:
            for record in self._chain:
                f.write(record.model_dump_json() + "\n")
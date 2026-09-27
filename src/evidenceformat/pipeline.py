"""
evidenceformat.pipeline
Synchronous Batch Pipeline Service for Processing Raw CSV Records.
"""

import csv
import hashlib
from typing import Tuple
from .schemas import RawEventInput, CanonicalEvent, Demographics
from .engine import NominativeLabeler, CochraneEvidenceEngine
from .audit import CryptographicAuditLedger


class BatchPipeline:
    """Synchronous Batch Processing Pipeline for CSV ingestion."""

    def __init__(self):
        self.ledger = CryptographicAuditLedger()

    def process_csv_file(self, input_csv_path: str, output_jsonl_path: str) -> Tuple[int, str]:
        """Ingests CSV payload, applies normalization & evidence scoring, and writes verified audit JSONL."""
        record_count = 0

        with open(input_csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                record_count += 1
                raw_input = RawEventInput(
                    event_id=str(row.get("event_id", f"EV_{record_count}")),
                    event_type=str(row.get("event_type", "Diagnosis")),
                    patient_or_learner_id=str(row.get("patient_or_learner_id", f"PAT_{record_count}")),
                    timestamp=str(row.get("timestamp", "2026-09-23T14:30:00Z")),
                    code=str(row.get("code", "")),
                    detail=str(row.get("detail", "")),
                    age=str(row.get("age", "")),
                    sex=str(row.get("sex", "")),
                    certainty_or_action=str(row.get("certainty_or_action", "")),
                    dose_or_score=str(row.get("dose_or_score", "")),
                    competency_level=str(row.get("competency_level", "")),
                    feedback_text=str(row.get("feedback_text", "")),
                    source_system=str(row.get("source_system", "Batch_Pipeline")),
                    evidence_refs=str(row.get("evidence_refs", ""))
                )

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

                score, refs, explain, conflict = CochraneEvidenceEngine.evaluate(
                    canonical, raw_input.evidence_refs or ""
                )

                self.ledger.append(
                    canonical_event=canonical,
                    confidence_score=score,
                    drug_warning=False,
                    interaction_details=[],
                    evidence_refs=refs,
                    explainability_text=explain,
                    conflict_flag=conflict
                )

        is_valid, msg = self.ledger.verify_integrity()
        if is_valid:
            self.ledger.export_jsonl(output_jsonl_path)

        return record_count, msg
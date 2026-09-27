"""
evaluate_precision.py
Benchmark Evaluation Suite for EvidenceFormat Engine against Gold Standard Dataset.
"""

import sys
import os
import csv
import hashlib
import time
import numpy as np
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from evidenceformat.schemas import RawEventInput, CanonicalEvent, Demographics
from evidenceformat.engine import NominativeLabeler, CochraneEvidenceEngine
from evidenceformat.audit import CryptographicAuditLedger
from generate_biomarker_dataset import generate_dataset


def run_benchmark(dataset_csv: str = "data/oncology_biomarker_200_pmid_dataset.csv") -> None:
    if not os.path.exists(dataset_csv):
        print(f"Dataset '{dataset_csv}' not found. Auto-generating 200-PMID dataset...")
        generate_dataset(dataset_csv)

    ledger = CryptographicAuditLedger()
    gold_scores: List[float] = []
    predicted_scores: List[float] = []
    
    total_records = 0
    conflict_flags_detected = 0

    print("==================================================================")
    print("EVIDENCEFORMAT ENGINE BENCHMARK: EVALUATION SUITE")
    print("==================================================================")

    start_perf = time.perf_counter()

    with open(dataset_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_records += 1
            gold_score = float(row["gold_confidence_score"])
            
            raw_input = RawEventInput(
                event_id=row["doc_id"],
                event_type="Diagnosis" if row["study_type"] != "MedicationChange" else "MedicationChange",
                patient_or_learner_id=f"PAT_{row['pmid'][-4:]}",
                timestamp="2026-09-23T14:30:00Z",
                code="I10",
                detail=row["claim_spans"],
                source_system=row["source_system"],
                evidence_refs=row["evidence_refs"]
            )

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
                demographics=Demographics(age=62, sex="M"),
                source_system=raw_input.source_system,
                raw_payload_hash=raw_payload_hash
            )

            predicted_score, refs, explain, conflict = CochraneEvidenceEngine.evaluate(
                canonical, row["evidence_refs"]
            )

            ledger.append(
                canonical_event=canonical,
                confidence_score=predicted_score,
                drug_warning=False,
                interaction_details=[],
                evidence_refs=refs,
                explainability_text=explain,
                conflict_flag=conflict
            )

            gold_scores.append(gold_score)
            predicted_scores.append(predicted_score)
            
            if conflict:
                conflict_flags_detected += 1

    elapsed_perf = max(time.perf_counter() - start_perf, 1e-6)

    if total_records == 0:
        print("⚠️ Warning: Provided dataset CSV contains no records.")
        return

    gold_arr = np.array(gold_scores, dtype=np.float64)
    pred_arr = np.array(predicted_scores, dtype=np.float64)

    mae = float(np.mean(np.abs(gold_arr - pred_arr)))
    rmse = float(np.sqrt(np.mean((gold_arr - pred_arr) ** 2)))
    
    if np.std(gold_arr) == 0 or np.std(pred_arr) == 0:
        correlation = 0.0
    else:
        correlation = float(np.corrcoef(gold_arr, pred_arr)[0, 1])

    is_valid_ledger, ledger_msg = ledger.verify_integrity()

    print(f"Results across {total_records} Evaluation Abstracts ({elapsed_perf:.3f} seconds):")
    print(f" • Confidence Score MAE (Mean Absolute Error):   {mae:.2f} pts")
    print(f" • Confidence Score RMSE:                        {rmse:.2f} pts")
    print(f" • Pearson Correlation (Predicted vs Gold):      {correlation:.4f}")
    print(f" • Conflict/Uncertainty Flagged Records:          {conflict_flags_detected} / {total_records}")
    print(f" • Cryptographic Audit Ledger Status:             {ledger_msg}")
    print("==================================================================")


if __name__ == "__main__":
    run_benchmark()
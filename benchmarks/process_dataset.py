"""
process_dataset.py
Batch Execution Script to process raw CSV records into an audit ledger.
"""

import sys
import os
import csv
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from evidenceformat.pipeline import BatchPipeline


def ensure_simulated_dataset(filepath: str) -> None:
    """Generates a default simulated CSV dataset if missing."""
    out_dir = os.path.dirname(filepath)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    if not os.path.exists(filepath):
        print(f"Generating default input dataset '{filepath}'...")
        fieldnames = [
            "event_id", "event_type", "patient_or_learner_id", "timestamp",
            "code", "detail", "age", "sex", "certainty_or_action",
            "dose_or_score", "competency_level", "feedback_text",
            "source_system", "evidence_refs"
        ]
        rows = []
        for i in range(1, 101):
            rows.append({
                "event_id": f"EV_{str(i).zfill(4)}",
                "event_type": "Diagnosis" if i % 2 == 0 else "MedicationChange",
                "patient_or_learner_id": f"PAT_{1000 + i}",
                "timestamp": "2026-09-23T14:30:00Z",
                "code": "I10" if i % 3 == 0 else "E11",
                "detail": f"Evaluation encounter for subject {i}",
                "age": "62",
                "sex": "M",
                "source_system": "EHR_Clinical_Note" if i % 2 == 0 else "Cochrane_Guideline_Repo",
                "evidence_refs": f"10.1001/jama.2025.{100+i}; local_note_draft" if i % 5 == 0 else f"10.1001/jama.2025.{100+i}"
            })
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    print("===============================================================")
    print("EVIDENCEFORMAT PYDANTIC V2 BATCH PROCESSING ENGINE")
    print("===============================================================")

    input_csv = "data/evidenceformat_simulated_dataset.csv"
    output_jsonl = "data/evidenceformat_verified_audit.jsonl"

    ensure_simulated_dataset(input_csv)

    pipeline = BatchPipeline()
    start_perf = time.perf_counter()

    print(f"Ingesting and validating: {input_csv} ...")
    count, integrity_msg = pipeline.process_csv_file(input_csv, output_jsonl)
    elapsed = max(time.perf_counter() - start_perf, 1e-6)

    print("\nBatch Run Summary:")
    print(f" • Total Records Processed: {count}")
    print(f" • Elapsed Execution Time: {elapsed:.4f} seconds")
    print(f" • Processing Throughput: {count / elapsed:.1f} records/sec")
    print(f" • Cryptographic Integrity: {integrity_msg}")
    print(f" • Output Written To: {output_jsonl}")
    print("===============================================================")
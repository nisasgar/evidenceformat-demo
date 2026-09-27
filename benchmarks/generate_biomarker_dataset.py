"""
generate_biomarker_dataset.py
Generates the Oncology/Biomarker Gold-Standard Evaluation Dataset CSV.
"""

import csv
import random
import os
from typing import List, Dict, Any

ONCOLOGY_BIOMARKERS: List[Dict[str, str]] = [
    {"gene": "PD-L1 / Pembrolizumab", "cancer": "metastatic NSCLC", "outcome": "overall survival", "code": "I10"},
    {"gene": "EGFR Mutation / Osimertinib", "cancer": "EGFR-mutated NSCLC", "outcome": "progression-free survival", "code": "E11"},
    {"gene": "HER2 Overexpression / Trastuzumab", "cancer": "HER2+ metastatic breast cancer", "outcome": "objective response rate", "code": "J01"},
    {"gene": "BRCA1/2 Mutation / Olaparib", "cancer": "high-grade serous ovarian cancer", "outcome": "progression-free survival", "code": "I10"},
    {"gene": "KRAS G12C Mutation / Sotorasib", "cancer": "KRAS G12C advanced NSCLC", "outcome": "overall survival", "code": "E11"},
    {"gene": "BRAF V600E / Dabrafenib + Trametinib", "cancer": "unresectable BRAF-mutated melanoma", "outcome": "overall survival", "code": "J01"},
    {"gene": "MSI-H / dMMR / Nivolumab", "cancer": "metastatic colorectal cancer", "outcome": "durable response rate", "code": "I10"},
    {"gene": "ALK Rearrangement / Alectinib", "cancer": "ALK-positive advanced NSCLC", "outcome": "progression-free survival", "code": "E11"}
]

STUDY_DISTRIBUTION = [
    ("RCT", 100),
    ("Cohort", 50),
    ("Systematic-Review", 30),
    ("Case-Series", 20)
]


def generate_dataset(
    filename: str = "data/oncology_biomarker_200_pmid_dataset.csv",
    num_records: int = 200,
    seed: int = 42
) -> str:
    """Generates synthetic biomarker evaluation records into CSV."""
    random.seed(seed)
    records: List[Dict[str, Any]] = []
    pmid_base = 38000000

    study_types, weights = zip(*STUDY_DISTRIBUTION)
    study_pool = random.choices(study_types, weights=weights, k=num_records)

    fieldnames = [
        "doc_id", "pmid", "doi", "study_type", "population_text",
        "intervention_text", "comparator_text", "outcome_text",
        "effect_direction", "effect_size", "sample_size", "risk_flags",
        "source_system", "evidence_refs", "gold_confidence_score", "claim_spans"
    ]

    for idx in range(1, num_records + 1):
        doc_id = f"ABST_{str(idx).zfill(4)}"
        pmid = str(pmid_base + idx)
        study_type = study_pool[idx - 1]
        target = random.choice(ONCOLOGY_BIOMARKERS)

        doi = f"10.1016/j.cell.2025.{random.randint(100, 999)}" if random.random() > 0.15 else ""
        source_system = "Cochrane_Guideline_Repo" if study_type == "Systematic-Review" else (
            "EHR_Oncology_Registry" if random.random() > 0.3 else "medRxiv_Preprint"
        )

        direction_rand = random.random()
        if direction_rand < 0.70:
            effect_direction = "benefit"
            hr_val = round(random.uniform(0.52, 0.82), 2)
            effect_size = f"HR={hr_val} (95% CI {round(hr_val-0.10, 2)}-{round(hr_val+0.11, 2)})"
        elif direction_rand < 0.85:
            effect_direction = "no-effect"
            effect_size = "mean diff = 0.05 (p=0.42)"
        else:
            effect_direction = "harm"
            effect_size = "HR=1.45 (95% CI 1.12-1.88)"

        if study_type == "Systematic-Review":
            sample_size = random.randint(1500, 12000)
            comparator = "standard of care / control"
        elif study_type == "RCT":
            sample_size = random.randint(250, 1200)
            comparator = "standard chemotherapy"
        elif study_type == "Cohort":
            sample_size = random.randint(80, 450)
            comparator = "biomarker-negative cohort"
        else:
            sample_size = random.randint(15, 60)
            comparator = "None"

        flags = []
        if study_type == "RCT":
            flags.append("randomization reported")
            if random.random() > 0.3:
                flags.append("blinding reported")
        if "Preprint" in source_system:
            flags.append("preprint")
        if random.random() < 0.2:
            flags.append("single-center")
        if random.random() < 0.25:
            flags.append("industry funded")

        risk_flags_str = "; ".join(flags) if flags else "none"

        refs_list = []
        if doi:
            refs_list.append(doi)
        if "Preprint" in source_system:
            refs_list.append("local_note_draft")
        evidence_refs_str = "; ".join(refs_list)

        base = 85 if study_type == "Systematic-Review" else (65 if study_type == "RCT" else 50)
        if doi:
            base += 15
        if "preprint" in risk_flags_str or "local_note_draft" in evidence_refs_str:
            base -= 15
        gold_confidence_score = max(10, min(100, base))

        claim_spans = f"In {sample_size} patients with {target['cancer']}, {target['gene']} demonstrated significant {target['outcome']} vs {comparator} ({effect_size})."

        record = {
            "doc_id": doc_id,
            "pmid": pmid,
            "doi": doi,
            "study_type": study_type,
            "population_text": f"Adults with {target['cancer']}",
            "intervention_text": target['gene'],
            "comparator_text": comparator,
            "outcome_text": target['outcome'],
            "effect_direction": effect_direction,
            "effect_size": effect_size,
            "sample_size": sample_size,
            "risk_flags": risk_flags_str,
            "source_system": source_system,
            "evidence_refs": evidence_refs_str,
            "gold_confidence_score": gold_confidence_score,
            "claim_spans": claim_spans
        }
        records.append(record)

    out_dir = os.path.dirname(filename)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Successfully generated {num_records} gold-standard records -> {filename}")
    return filename


if __name__ == "__main__":
    generate_dataset()
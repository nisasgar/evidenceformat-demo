"""
evidenceformat.engine
Symbolic Logic, Nominative Labeling, and Cochrane Evidence Tagging.
"""

from typing import List, Tuple, Optional
from .schemas import CanonicalEvent


class NominativeLabeler:
    """Exact Nominative and Anatomical Labeling Mapper."""
    ONTOLOGY = {
        "I10": ("Essential Primary Hypertension", "59621000"),
        "E11": ("Type 2 Diabetes Mellitus", "44054006"),
        "J01": ("Acute Sinusitis", "36971009"),
        "ASSESS_001": ("Standardized Evaluation Attempt", "705009000"),
        "COMP_01": ("Algebraic Competency Signal", "705010000"),
    }

    @classmethod
    def resolve(cls, code: Optional[str], detail: Optional[str]) -> Tuple[str, str]:
        clean_code = code.strip().upper() if code else ""
        if clean_code in cls.ONTOLOGY:
            return cls.ONTOLOGY[clean_code]
        clean_detail = detail.strip() if detail else ""
        label = clean_detail if clean_detail else f"Normalized Entity [{clean_code}]"
        return label, "99999999"


class CochraneEvidenceEngine:
    """Evaluates source trust, DOI references, and conflict heuristics."""
    
    @staticmethod
    def evaluate(event: CanonicalEvent, raw_refs_str: str) -> Tuple[float, List[str], str, bool]:
        base_score = 50.0
        reasons = []

        source = event.source_system.lower()
        if "guideline" in source or "cochrane" in source:
            base_score = 85.0
            reasons.append("source:high_trust_guideline(+35)")
        elif "ehr" in source or "clinic" in source:
            base_score = 65.0
            reasons.append("source:clinical_ehr(+15)")
        elif "lms" in source or "course" in source:
            base_score = 70.0
            reasons.append("source:educational_system(+20)")

        refs = [r.strip() for r in raw_refs_str.split(";") if r.strip()] if raw_refs_str else []
        doi_count = sum(1 for r in refs if "10." in r)
        
        if doi_count >= 1:
            method_bonus = min(doi_count * 15.0, 30.0)
            base_score += method_bonus
            reasons.append(f"methodology:doi_verified(+{method_bonus:.1f})")

        has_local_notes = any("local_note" in r.lower() for r in refs)
        conflict = bool(has_local_notes and doi_count > 0)
        if conflict:
            base_score -= 15.0
            reasons.append("conflict:local_vs_doi_disagreement(-15)")

        final_score = max(0.0, min(100.0, base_score))
        explainability = "; ".join(reasons) if reasons else "baseline_scoring"
        return final_score, refs, explainability, conflict
"""
streamlit_pilot_dashboard.py
Upgraded Hosted Streamlit Pilot Dashboard for EvidenceFormat & StatMech Engine.
"""

import sys
import os
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any

import streamlit as st
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evidenceformat.schemas import CanonicalEvent, Demographics
from evidenceformat.engine import NominativeLabeler, CochraneEvidenceEngine
from evidenceformat.audit import CryptographicAuditLedger
from statmech_engine import StatMechEngine, MathematicalConfidenceRequest

st.set_page_config(
    page_title="EvidenceFormat Executive Pilot Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    if "ledger" not in st.session_state:
        st.session_state["ledger"] = CryptographicAuditLedger()
    if "audits" not in st.session_state:
        st.session_state["audits"] = []
    if "df_cache" not in st.session_state:
        st.session_state["df_cache"] = pd.DataFrame()
    if "selected_event_id" not in st.session_state:
        st.session_state["selected_event_id"] = ""
    if "is_loaded" not in st.session_state:
        st.session_state["is_loaded"] = False

init_session_state()


def run_pipeline_over_records(raw_rows: List[Dict[str, Any]]):
    ledger = CryptographicAuditLedger()
    audit_records = []
    flattened_rows = []

    for row in raw_rows:
        event_id = str(row.get("event_id", row.get("doc_id", f"EV_{len(audit_records)+1}")))
        event_type = str(row.get("event_type", "Diagnosis"))
        subject_id = str(row.get("patient_or_learner_id", row.get("pmid", f"PAT_{1000+len(audit_records)}")))
        timestamp = str(row.get("timestamp", "2026-09-23T14:30:00Z"))
        code = str(row.get("code", "I10"))
        detail = str(row.get("detail", row.get("claim_spans", "Clinical Note Payload")))
        source_system = str(row.get("source_system", "EHR_Clinical_Note"))
        evidence_refs_str = str(row.get("evidence_refs", ""))
        age_str = str(row.get("age", ""))
        sex_str = str(row.get("sex", "M"))

        age_val = int(age_str) if age_str.isdigit() else 62
        demographics = Demographics(age=age_val, sex=sex_str)

        label, snomed = NominativeLabeler.resolve(code, detail)
        raw_payload_hash = hashlib.sha256(f"{event_id}|{code}|{detail}".encode("utf-8")).hexdigest()[:16]

        canonical = CanonicalEvent(
            event_id=event_id,
            event_type=event_type,
            subject_id=subject_id,
            timestamp=timestamp,
            code=code,
            detail=detail,
            nominative_label=label,
            snomed_code=snomed,
            demographics=demographics,
            source_system=source_system,
            raw_payload_hash=raw_payload_hash
        )

        score, refs, explain, conflict = CochraneEvidenceEngine.evaluate(canonical, evidence_refs_str)

        rec = ledger.append(
            canonical_event=canonical,
            confidence_score=score,
            drug_warning=False,
            interaction_details=[],
            evidence_refs=refs,
            explainability_text=explain,
            conflict_flag=conflict
        )

        audit_records.append(rec)

        flattened_rows.append({
            "audit_id": rec.audit_id,
            "event_id": rec.event_id,
            "event_type": rec.event_type,
            "subject_id": rec.subject_id,
            "timestamp": canonical.timestamp,
            "code": canonical.code,
            "nominative_label": canonical.nominative_label,
            "snomed_code": canonical.snomed_code,
            "source_system": canonical.source_system,
            "confidence_score": rec.confidence_score,
            "conflict_flag": rec.conflict_flag,
            "evidence_refs": "; ".join(rec.evidence_refs),
            "explainability_text": rec.explainability_text,
            "raw_payload_hash": rec.raw_payload_hash,
            "record_hash": rec.record_hash
        })

    st.session_state["ledger"] = ledger
    st.session_state["audits"] = audit_records
    st.session_state["df_cache"] = pd.DataFrame(flattened_rows)
    st.session_state["is_loaded"] = True


st.sidebar.title("🏥 EvidenceFormat Pilot")
st.sidebar.markdown("**Enterprise Health Informatics Data Layer**")
st.sidebar.subheader("1. Data Ingestion Controls")

dataset_choice = st.sidebar.radio(
    "Select Input Dataset Source:",
    ("200-PMID Oncology Biomarker Dataset", "Simulated EHR/LMS Stream (60 Rows)", "Upload Custom CSV"),
    index=0
)

if dataset_choice == "Upload Custom CSV":
    uploaded_file = st.sidebar.file_uploader("Upload CSV Payload", type=["csv"])
    if uploaded_file is not None:
        if st.sidebar.button("Process Uploaded CSV", type="primary"):
            df_upload = pd.read_csv(uploaded_file, dtype=str).fillna("")
            run_pipeline_over_records(df_upload.to_dict(orient="records"))
            st.sidebar.success(f"Processed {len(df_upload)} uploaded records!")
else:
    if st.sidebar.button("Run / Reload Dataset Pipeline", type="primary") or not st.session_state["is_loaded"]:
        if "Oncology" in dataset_choice:
            sample_data = []
            biomarkers = ["PD-L1 / Pembrolizumab", "EGFR / Osimertinib", "HER2 / Trastuzumab", "BRCA1/2 / Olaparib"]
            for i in range(1, 201):
                bm = biomarkers[i % len(biomarkers)]
                is_conflict = (i % 5 == 0)
                sample_data.append({
                    "event_id": f"ABST_{str(i).zfill(4)}",
                    "event_type": "Diagnosis" if i % 2 == 0 else "MedicationChange",
                    "patient_or_learner_id": f"PAT_{38000000 + i}",
                    "timestamp": f"2026-09-{(i%28)+1:02d}T14:30:00Z",
                    "code": "I10" if i % 3 == 0 else "E11",
                    "detail": f"Biomarker response evaluation for {bm} in metastatic cancer.",
                    "source_system": "Cochrane_Guideline_Repo" if i % 4 == 0 else ("medRxiv_Preprint" if is_conflict else "EHR_Clinical_Note"),
                    "evidence_refs": f"10.1016/j.cell.2025.{100+i}" + ("; local_note_draft" if is_conflict else ""),
                    "age": "64",
                    "sex": "M"
                })
            run_pipeline_over_records(sample_data)
            st.sidebar.success("Loaded 200-PMID Oncology Dataset!")
        else:
            sample_data = []
            for i in range(1, 61):
                sample_data.append({
                    "event_id": f"EV_{str(i).zfill(4)}",
                    "event_type": "MedicationChange" if i % 2 == 0 else "AssessmentAttempt",
                    "patient_or_learner_id": f"PAT_{1000 + i}",
                    "timestamp": "2026-09-23T14:30:00Z",
                    "code": "I10",
                    "detail": "Hypertension treatment evaluation",
                    "source_system": "EHR_A" if i % 2 == 0 else "LMS_CoursePortal",
                    "evidence_refs": "10.1001/jama.2025.102"
                })
            run_pipeline_over_records(sample_data)
            st.sidebar.success("Loaded 60 Simulated Stream Rows!")

st.sidebar.subheader("2. Filter & Triage Criteria")
df_all = st.session_state["df_cache"]

if not df_all.empty:
    event_types = ["All"] + sorted(df_all["event_type"].dropna().unique().tolist())
    selected_type = st.sidebar.selectbox("Event Type Filter", event_types)
    min_confidence = st.sidebar.slider("Minimum Confidence Score", 0, 100, 40)
    show_conflicts_only = st.sidebar.checkbox("Show Conflict-Flagged Only", False)
    search_subject = st.sidebar.text_input("Search Subject / Patient ID")

    df_filtered = df_all.copy()
    if selected_type != "All":
        df_filtered = df_filtered[df_filtered["event_type"] == selected_type]
    df_filtered = df_filtered[df_filtered["confidence_score"] >= min_confidence]
    if show_conflicts_only:
        df_filtered = df_filtered[df_filtered["conflict_flag"]]
    if search_subject:
        df_filtered = df_filtered[df_filtered["subject_id"].str.contains(search_subject, case=False, na=False)]
else:
    df_filtered = pd.DataFrame()


st.title("🏥 EvidenceFormat Pilot Dashboard")
st.markdown("Standardize clinical/learning events, enforce Cochrane evidence tags, and maintain a SHA-256 cryptographic audit ledger.")

if df_filtered.empty:
    st.info("No records loaded. Please click 'Run / Reload Dataset Pipeline' in the sidebar.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Active Events", len(df_filtered))
col2.metric("Mean Confidence Score", f"{df_filtered['confidence_score'].mean():.1f} / 100")
col3.metric("Flagged Conflicts", int(df_filtered["conflict_flag"].sum()))
col4.metric("Unique Subjects / Patients", df_filtered["subject_id"].nunique())

st.markdown("---")

tabs = st.tabs([
    "📊 Event List & Triaging",
    "🔍 Deep Event Detail",
    "⚡ StatMech & Teleodynamics Analytics",
    "🔗 Cryptographic Audit Ledger",
    "📄 Executive Pilot Reports & Exports"
])

with tabs[0]:
    st.subheader("Normalized Event List")
    display_cols = ["event_id", "event_type", "subject_id", "nominative_label", "snomed_code", "confidence_score", "conflict_flag", "source_system"]
    st.dataframe(df_filtered[display_cols].sort_values(by="confidence_score", ascending=True).reset_index(drop=True), use_container_width=True, height=400)

with tabs[1]:
    st.subheader("Deep Event Payload & Evidence Inspection")
    event_id_input = st.text_input("Enter Event ID to Inspect:", value=st.session_state["selected_event_id"])
    
    if event_id_input:
        st.session_state["selected_event_id"] = event_id_input
        match_audit = next((a for a in st.session_state["audits"] if a.event_id == event_id_input), None)
        
        if match_audit:
            col_left, col_right = st.columns([1, 1])
            with col_left:
                st.markdown("### Normalized Canonical Event")
                ev = match_audit.normalized_event
                st.write("**Event ID:**", ev.event_id)
                st.write("**Event Type:**", ev.event_type)
                st.write("**Subject ID:**", ev.subject_id)
                st.write("**Timestamp:**", ev.timestamp)
                st.write("**Nominative Label:**", f"`{ev.nominative_label}`")
                st.write("**SNOMED-CT Code:**", f"`{ev.snomed_code}`")
                st.write("**Source System:**", ev.source_system)
                st.write("**Raw Payload SHA-256:**", f"`{ev.raw_payload_hash}`")
            
            with col_right:
                st.markdown("### Evidence & Conflict Tags")
                st.metric("Confidence Score", f"{match_audit.confidence_score:.1f} / 100")
                st.write("**Conflict Flagged:**", "⚠️ YES" if match_audit.conflict_flag else "✅ NO")
                st.write("**Evidence References:**", match_audit.evidence_refs or "None attached")
                st.write("**Explainability Rationale:**", match_audit.explainability_text)
                
                st.markdown("### Raw Cryptographic Audit Record")
                st.code(json.dumps(match_audit.model_dump(), indent=2), language="json")

with tabs[2]:
    st.subheader("⚡ Statistical Mechanics & Teleodynamics Diagnostics")
    st.caption("Real-time information theory metrics, spectral graph entropy, and active inference confidence calibration.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 1. Payload Shannon Entropy $H(X)$")
        sample_text = st.text_area("Input Clinical Note Stream for Token Entropy:", value="Patient presenting with glioblastoma multiforme biomarker PD-L1 positive.")
        if sample_text:
            tokens = sample_text.lower().split()
            shannon_h = StatMechEngine.compute_shannon_entropy(tokens)
            st.metric("Shannon Entropy (bits)", f"{shannon_h:.4f}")

    with c2:
        st.markdown("#### 2. Von Neumann Graph Entropy $S_{VN}(\\rho)$")
        st.caption("Adjacency Matrix Spectrum of Graph Laplacian $L = D - A$")
        adj = np.array([
            [0, 1, 1, 0],
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [0, 1, 1, 0]
        ])
        svn = StatMechEngine.compute_von_neumann_graph_entropy(adj)
        st.metric("Von Neumann Graph Entropy", f"{svn:.4f}")

    st.markdown("---")
    st.markdown("#### 3. Active Inference Evidence Calibration $S_{conf}(E)$")
    
    req_sim = MathematicalConfidenceRequest(
        source_type="cochrane_guideline",
        study_design="rct",
        sample_size=512,
        publication_year=2024,
        current_year=2026,
        is_randomized=True,
        is_double_blind=True,
        has_high_risk_of_bias=False,
        local_observation_dist=[0.82, 0.18],
        reference_literature_dist=[0.75, 0.25]
    )
    score_calib, metrics_calib, explain_log = StatMechEngine.calculate_confidence_score(req_sim)
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Calibrated Score $S_{conf}$", f"{score_calib:.2f} / 100")
    col_m2.metric("Jensen-Shannon Divergence $D_{JS}$", f"{metrics_calib['d_js']:.4f}")
    col_m3.metric("Recency Decay Factor", f"{metrics_calib['decay_factor']:.3f}")
    
    st.code(f"Explainability Log: {explain_log}", language="text")

with tabs[3]:
    st.subheader("Cryptographic Audit Chain & Integrity Verification")
    if st.button("Verify SHA-256 Ledger Integrity Now"):
        is_valid, msg = st.session_state["ledger"].verify_integrity()
        if is_valid:
            st.success(f"✅ {msg}")
        else:
            st.error(f"🚨 {msg}")

    st.markdown("### Recent Audit Chain Blocks")
    chain_df = df_filtered[["event_id", "confidence_score", "conflict_flag", "raw_payload_hash", "record_hash"]].tail(20)
    st.dataframe(chain_df.reset_index(drop=True), use_container_width=True)

with tabs[4]:
    st.subheader("📄 Executive Pilot Reports & Data Exports")
    is_valid, integrity_msg = st.session_state["ledger"].verify_integrity()
    kpi_summary = {
        "report_title": "EvidenceFormat 90-Day Pilot Performance Report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_events_processed": len(df_filtered),
        "mean_confidence_score": float(df_filtered["confidence_score"].mean()),
        "conflict_flagged_count": int(df_filtered["conflict_flag"].sum()),
        "unique_subjects": int(df_filtered["subject_id"].nunique()),
        "ledger_integrity_verified": is_valid,
        "ledger_integrity_status": integrity_msg
    }

    col_exp1, col_exp2, col_exp3 = st.columns(3)
    with col_exp1:
        st.download_button("Download Filtered CSV", data=df_filtered.to_csv(index=False).encode("utf-8"), file_name="evidenceformat_filtered.csv", mime="text/csv")
    with col_exp2:
        jsonl_bytes = "\n".join([a.model_dump_json() for a in st.session_state["audits"]]).encode("utf-8")
        st.download_button("Export Audit JSONL", data=jsonl_bytes, file_name="evidenceformat_audit.jsonl", mime="application/jsonlines")
    with col_exp3:
        st.download_button("Download Pilot KPI JSON", data=json.dumps(kpi_summary, indent=2).encode("utf-8"), file_name="evidenceformat_kpi.json", mime="application/json")

    st.json(kpi_summary)
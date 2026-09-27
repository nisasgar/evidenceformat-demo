"""
server.py
FastAPI Webhook REST Server for Asynchronous FHIR, xAPI Ingestion, and Statistical Mechanics Diagnostics.
"""

import sys
import os
from datetime import datetime, timezone
import numpy as np
from fastapi import FastAPI, BackgroundTasks, status, Query

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from evidenceformat.adapters import XAPIStatement, FHIRGenericResource
from evidenceformat.async_service import async_pipeline
from statmech_engine import StatMechEngine, MathematicalConfidenceRequest, StatMechDiagnostics

app = FastAPI(
    title="EvidenceFormat Webhook API",
    description="Asynchronous Ingestion Middleware for FHIR R4 & xAPI Streams with SHA-256 Audit Chaining & StatMech Engine.",
    version="1.0.0-async"
)


async def background_ingest_worker(raw_event, evidence_refs: str):
    """Worker task that processes events asynchronously in the background."""
    try:
        await async_pipeline.process_raw_event_async(raw_event, evidence_refs)
    except Exception as e:
        print(f"[ERROR] Background Ingestion Failed for Event {raw_event.event_id}: {str(e)}")


@app.get("/", tags=["Health"])
async def root_health_check():
    return {
        "status": "healthy",
        "service": "EvidenceFormat Async Webhook & StatMech Engine",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ledger_entries": len(async_pipeline.ledger._chain)
    }


@app.post(
    "/api/v1/ingest/fhir",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Webhooks"]
)
async def ingest_fhir_webhook(
    resource: FHIRGenericResource,
    background_tasks: BackgroundTasks,
    evidence_refs: str = Query(default="", description="Optional DOIs or guideline tags")
):
    """Asynchronous Webhook Endpoint for FHIR R4 Resources."""
    raw_event = resource.to_raw_event()
    background_tasks.add_task(background_ingest_worker, raw_event, evidence_refs)

    return {
        "status": "accepted",
        "message": f"FHIR {resource.resourceType} resource queued for normalization.",
        "event_id": raw_event.event_id,
        "ingest_timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post(
    "/api/v1/ingest/xapi",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Webhooks"]
)
async def ingest_xapi_webhook(
    statement: XAPIStatement,
    background_tasks: BackgroundTasks,
    evidence_refs: str = Query(default="", description="Optional rubric or evidence tags")
):
    """Asynchronous Webhook Endpoint for xAPI Statements."""
    raw_event = statement.to_raw_event()
    background_tasks.add_task(background_ingest_worker, raw_event, evidence_refs)

    return {
        "status": "accepted",
        "message": "xAPI Statement queued for normalization.",
        "event_id": raw_event.event_id,
        "actor": raw_event.patient_or_learner_id,
        "ingest_timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post(
    "/api/v1/diagnostics/statmech",
    response_model=StatMechDiagnostics,
    tags=["Statistical Mechanics"]
)
async def compute_statmech_diagnostics(req: MathematicalConfidenceRequest):
    """Evaluates mathematical confidence scoring, JSD, Free Energy, and Entropy metrics."""
    score, metrics, explain_log = StatMechEngine.calculate_confidence_score(req)
    
    shannon_h = StatMechEngine.compute_shannon_entropy([req.source_type, req.study_design])
    adj = np.array([[0, 1], [1, 0]])
    s_vn = StatMechEngine.compute_von_neumann_graph_entropy(adj)
    f_energy = StatMechEngine.compute_variational_free_energy(
        np.array(req.local_observation_dist),
        np.array(req.reference_literature_dist),
        log_likelihood=-0.5
    )
    te_est = StatMechEngine.estimate_transfer_entropy(
        np.array([1.0, 2.0, 1.5, 3.0]),
        np.array([1.1, 1.9, 1.6, 2.8])
    )

    return StatMechDiagnostics(
        shannon_payload_entropy_bits=shannon_h,
        von_neumann_graph_entropy=s_vn,
        jensen_shannon_divergence=metrics["d_js"],
        variational_free_energy=f_energy,
        transfer_entropy_estimate=te_est,
        calibrated_confidence_score=score,
        explainability_log=explain_log
    )


@app.get("/api/v1/audit/verify", tags=["Ledger Verification"])
async def verify_audit_ledger():
    """Traverses and verifies the SHA-256 cryptographic audit chain in real time."""
    is_valid, msg = async_pipeline.ledger.verify_integrity()
    return {
        "ledger_valid": is_valid,
        "integrity_message": msg,
        "total_records": len(async_pipeline.ledger._chain),
        "latest_block_hash": async_pipeline.ledger.current_hash
    }


@app.get("/api/v1/audit/chain", tags=["Ledger Verification"])
async def get_audit_chain():
    """Returns all audit records in the active ledger serialized safely for JSON output."""
    return [record.model_dump(mode="json") for record in async_pipeline.ledger._chain]
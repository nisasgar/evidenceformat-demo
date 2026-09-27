# EvidenceFormat Engine

An enterprise-grade health informatics, neuro-symbolic reasoning, and statistical mechanics platform built for real-time telemetry processing, clinical/learning event standardization, Cochrane evidence tag enforcement, and SHA-256 cryptographic audit chaining.

## 🚀 Features

- **Pydantic v2 Canonical Data Layer**: Built on Pydantic v2.6+ for ultra-fast, strict schema validation across incoming clinical, educational, and observational telemetry.
- **SHA-256 Cryptographic Audit Ledger**: Immutable, append-only hash chain linking every ingested payload, confidence score, and explainability rationale to guarantee auditability and tamper protection.
- **Neuro-Symbolic & Cochrane Evidence Engine**: Automated nominative entity resolution, SNOMED-CT code mapping, study design evaluation, DOI verification, and conflict detection.
- **Statistical Mechanics & Teleodynamics Diagnostics**: Real-time information-theoretic analytics including discrete Shannon Entropy H(X), Von Neumann Graph Entropy \(S_{VN}(\rho)\) derived from Laplacian spectra, Jensen-Shannon Divergence \(D_{JS}\), Variational Free Energy F (Active Inference), and Directed Transfer Entropy \(T_{X\rightarrow Y}\).
- **Multimodal Webhook Adapters**: Built-in parsers converting raw FHIR R4 (HL7) resources and xAPI (IEEE LTSC / ADL) learning statements directly into canonical event streams.
- **Production Services**: Asynchronous FastAPI REST middleware with background workers alongside a multi-tab hosted Streamlit Pilot Dashboard.

## 📁 Directory Structure

```text
.
├── pyproject.toml                         # Package configuration & dependencies
├── src/
│   ├── evidenceformat/                    # Core EvidenceFormat python package
│   │   ├── __init__.py                    # Package exports
│   │   ├── schemas.py                     # Pydantic v2 models (CanonicalEvent, AuditRecord)
│   │   ├── engine.py                      # NominativeLabeler & CochraneEvidenceEngine
│   │   ├── audit.py                       # SHA-256 Cryptographic Audit Ledger
│   │   ├── adapters.py                    # FHIR R4 & xAPI Webhook parsers
│   │   ├── async_service.py               # Async lock-protected pipeline service
│   │   └── pipeline.py                    # Synchronous batch pipeline runner
│   ├── statmech_engine.py                 # Entropy, JSD, Free Energy & StatMech diagnostics
│   ├── server.py                          # FastAPI Webhook REST API server
│   └── streamlit_pilot_dashboard.py       # Hosted Streamlit pilot dashboard UI
├── data/                                  # Datasets & exports
│   ├── evidenceformat_simulated_dataset.csv
│   ├── oncology_biomarker_200_pmid_dataset.csv
│   └── evidenceformat_verified_audit.jsonl
└── benchmarks/                            # Benchmark & evaluation runners
    ├── generate_biomarker_dataset.py      # 200-PMID Gold-Standard CSV generator
    ├── evaluate_precision.py              # Precision, MAE, and RMSE evaluation runner
    └── process_dataset.py                 # Pure Pydantic v2 batch processing runner
```

## 📦 Installation

Get the platform up and running locally by setting up the environment and installing dependencies.

### Prerequisites

Make sure you have the following installed:
* **Python**: 3.10 or higher
* **Core Libraries**: Pydantic 2.6+, NumPy 2.0+, SciPy 1.12+, FastAPI 0.110+, Streamlit 1.30+, Pandas 2.1+

### Setup Steps

1. Clone the repository and navigate to the root directory:
   ```bash
   cd evidenceformat-engine
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the package in editable mode with development dependencies:
   ```bash
   pip install -e .
   ```

## 🛠️ Execution Guide

### 1. Execute Batch Processing Runner
Ingest raw CSV records, process payloads through the normalization pipeline, verify cryptographic hash chain integrity, and export immutable JSONL records:
```bash
python benchmarks/process_dataset.py
```

### 2. Run Benchmark Precision Evaluation Suite
Evaluate confidence score alignment against the 200-PMID Gold-Standard Oncology Dataset (N=200 evaluation abstracts):
```bash
python benchmarks/evaluate_precision.py
```

### 3. Launch FastAPI Webhook REST API Server
Start the asynchronous FastAPI middleware to ingest real-time FHIR R4 and xAPI webhooks:
```bash
uvicorn src.server:app --reload --host 0.0.0.0 --port 8000
```
* **Interactive Swagger Docs**: `http://localhost:8000/docs`
* **ReDoc Interface**: `http://localhost:8000/redoc`

### 4. Launch Streamlit Executive Pilot Dashboard
Launch the interactive 5-tab pilot UI for data triaging, telemetry inspection, StatMech diagnostics, and ledger verification:
```bash
streamlit run src/streamlit_pilot_dashboard.py
```

## 🔌 API Reference Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/` | Webhook health check and active audit ledger block count. |
| **POST** | `/api/v1/ingest/fhir` | Asynchronous queue endpoint for HL7 FHIR R4 resources. |
| **POST** | `/api/v1/ingest/xapi` | Asynchronous queue endpoint for IEEE xAPI statements. |
| **POST** | `/api/v1/diagnostics/statmech` | Computes Shannon Entropy, Graph Entropy, JSD, Free Energy, and calibrated confidence scores. |
| **GET** | `/api/v1/audit/verify` | Real-time traversal and integrity verification of the SHA-256 audit chain. |
| **GET** | `/api/v1/audit/chain` | Retrieves all audit records in JSON format. |

## 🛠️ Technology Stack

| Dependency | Specification | Role |
| :--- | :--- | :--- |
| **Pydantic** | `>= 2.6.0` | Canonical schema validation, OpenAPI extras, and serialization. |
| **NumPy** | `>= 2.0.0` | Symmetrized Laplacian spectrum calculation and vector mathematics. |
| **SciPy** | `>= 1.12.0` | Relative entropy (KL-divergence) and distribution metrics. |
| **FastAPI** | `>= 0.110.0` | Asynchronous REST endpoints and background task dispatching. |
| **Streamlit** | `>= 1.30.0` | Executive dashboard and real-time ledger triaging. |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License right now. See `LICENSE` for more information or updates.
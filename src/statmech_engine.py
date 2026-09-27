"""
statmech_engine.py
Mathematical & Statistical Mechanics Engine for Telemetry Entropy,
Active Inference (Variational Free Energy), Transfer Entropy, and Calibrated Evidence Scoring.
"""

import numpy as np
from scipy.stats import entropy
import math
from typing import List, Dict, Tuple
from pydantic import BaseModel, Field


class MathematicalConfidenceRequest(BaseModel):
    source_type: str = Field(..., json_schema_extra={"examples": ["cochrane_guideline"]})
    study_design: str = Field(..., json_schema_extra={"examples": ["rct"]})
    sample_size: int = Field(..., json_schema_extra={"examples": [512]})
    publication_year: int = Field(..., json_schema_extra={"examples": [2024]})
    current_year: int = Field(2026, json_schema_extra={"examples": [2026]})
    is_randomized: bool = Field(True, json_schema_extra={"examples": [True]})
    is_double_blind: bool = Field(True, json_schema_extra={"examples": [True]})
    has_high_risk_of_bias: bool = Field(False, json_schema_extra={"examples": [False]})
    local_observation_dist: List[float] = Field(..., json_schema_extra={"examples": [[0.85, 0.15]]})
    reference_literature_dist: List[float] = Field(..., json_schema_extra={"examples": [[0.72, 0.28]]})


class StatMechDiagnostics(BaseModel):
    shannon_payload_entropy_bits: float
    von_neumann_graph_entropy: float
    jensen_shannon_divergence: float
    variational_free_energy: float
    transfer_entropy_estimate: float
    calibrated_confidence_score: float
    explainability_log: str


class StatMechEngine:
    """
    Mathematical & Statistical Mechanics Engine for Telemetry Entropy,
    Active Inference Trajectories, and Calibrated Cochrane Evidence Scoring.
    """

    @staticmethod
    def compute_shannon_entropy(payload_tokens: List[str]) -> float:
        """Computes discrete Shannon Entropy H(X) in bits for payload tokens."""
        if not payload_tokens:
            return 0.0
        _, counts = np.unique(payload_tokens, return_counts=True)
        probabilities = counts / len(payload_tokens)
        return float(-np.sum(probabilities * np.log2(probabilities)))

    @staticmethod
    def compute_von_neumann_graph_entropy(adjacency_matrix: np.ndarray) -> float:
        """
        Computes Von Neumann Graph Entropy S_VN(rho) from the spectrum of
        the trace-normalized Graph Laplacian: L = D - A.
        Symmetrizes density matrix prior to eigenvalue decomposition.
        """
        N = adjacency_matrix.shape[0]
        if N <= 1:
            return 0.0

        degrees = np.sum(adjacency_matrix, axis=1)
        degree_matrix = np.diag(degrees)
        laplacian = degree_matrix - adjacency_matrix

        trace_L = np.trace(laplacian)
        if trace_L == 0:
            return 0.0

        density_matrix = laplacian / trace_L
        sym_density = 0.5 * (density_matrix + density_matrix.T)
        eigenvalues = np.linalg.eigvalsh(sym_density)
        
        eigenvalues = eigenvalues[eigenvalues > 1e-12]
        if len(eigenvalues) == 0:
            return 0.0

        return float(-np.sum(eigenvalues * np.log2(eigenvalues)))

    @staticmethod
    def compute_jensen_shannon_divergence(p: np.ndarray, q: np.ndarray) -> float:
        """Computes Jensen-Shannon Divergence D_JS(P || Q) bounded in [0, 1]."""
        p = np.asarray(p, dtype=np.float64) + 1e-12
        q = np.asarray(q, dtype=np.float64) + 1e-12
        
        p = p / np.sum(p)
        q = q / np.sum(q)
        
        m = 0.5 * (p + q)
        kl_pm = entropy(p, m, base=2)
        kl_qm = entropy(q, m, base=2)
        
        return float(0.5 * kl_pm + 0.5 * kl_qm)

    @staticmethod
    def compute_variational_free_energy(
        q_theta: np.ndarray,
        p_theta: np.ndarray,
        log_likelihood: float
    ) -> float:
        """
        Calculates Variational Free Energy F = D_KL[q(theta) || p(theta)] - E_q[ln p(y | theta)]
        used in Active Inference and homeostatic trajectory modeling.
        """
        q_theta = np.asarray(q_theta, dtype=np.float64) + 1e-12
        p_theta = np.asarray(p_theta, dtype=np.float64) + 1e-12
        q_theta /= np.sum(q_theta)
        p_theta /= np.sum(p_theta)
        
        d_kl = float(entropy(q_theta, p_theta, base=2))
        f_val = d_kl - log_likelihood
        return float(f_val)

    @staticmethod
    def estimate_transfer_entropy(
        source_stream: np.ndarray,
        target_stream: np.ndarray,
        lag: int = 1
    ) -> float:
        """
        Approximates Directed Transfer Entropy T_{X -> Y} across continuous telemetry channels
        to detect systemic organ-decoupling.
        """
        if len(source_stream) <= lag or len(target_stream) <= lag:
            return 0.0

        y_future = target_stream[lag:]
        y_past = target_stream[:-lag]
        x_past = source_stream[:-lag]

        bins = 4
        def quantize(arr: np.ndarray) -> np.ndarray:
            min_val, max_val = float(np.min(arr)), float(np.max(arr))
            if math.isclose(min_val, max_val):
                return np.zeros(len(arr), dtype=int)
            edges = np.linspace(min_val, max_val, bins + 1)[1:-1]
            return np.digitize(arr, edges)

        y_f_b = quantize(y_future)
        y_p_b = quantize(y_past)
        x_p_b = quantize(x_past)

        def h_joint(*args) -> float:
            stacked = np.vstack(args).T
            _, counts = np.unique(stacked, axis=0, return_counts=True)
            p = counts / len(stacked)
            return float(-np.sum(p * np.log2(p + 1e-12)))

        h_yf_yp = h_joint(y_f_b, y_p_b)
        h_yp = h_joint(y_p_b)
        h_yf_yp_xp = h_joint(y_f_b, y_p_b, x_p_b)
        h_yp_xp = h_joint(y_p_b, x_p_b)

        te = (h_yf_yp - h_yp) - (h_yf_yp_xp - h_yp_xp)
        return float(max(0.0, te))

    @classmethod
    def calculate_confidence_score(cls, req: MathematicalConfidenceRequest) -> Tuple[float, Dict[str, float], str]:
        """Executes mathematically calibrated confidence score calculation S_conf(E)."""
        src_map = {
            "cochrane_guideline": 1.8,
            "ehr_system": 0.5,
            "local_note": -0.8
        }
        w_src = src_map.get(req.source_type.lower(), 0.0)

        design_map = {
            "meta_analysis": 1.2,
            "rct": 1.0,
            "cohort": 0.5,
            "case_series": 0.2
        }
        delta_design = design_map.get(req.study_design.lower(), 0.2)
        delta_rigor = delta_design + (0.5 if req.is_randomized else 0.0) + \
                      (0.4 if req.is_double_blind else 0.0) - \
                      (0.8 if req.has_high_risk_of_bias else 0.0)

        k_N = 0.005
        f_N = (2.0 / (1.0 + math.exp(-k_N * req.sample_size))) - 1.0

        delta_t = max(0.0, float(req.current_year - req.publication_year))
        t_half = 5.0
        lam = math.log(2) / t_half
        decay_factor = math.exp(-lam * delta_t)

        d_js = cls.compute_jensen_shannon_divergence(
            np.array(req.local_observation_dist),
            np.array(req.reference_literature_dist)
        )
        gamma = 3.0

        z = w_src + (delta_rigor * f_N * decay_factor) - (gamma * d_js)

        sigma_z = 1.0 / (1.0 + math.exp(-z))
        s_conf = float(np.clip(100.0 * sigma_z, 0.0, 100.0))

        explain = (
            f"w_src={w_src:+.2f}; "
            f"delta_rigor={delta_rigor:+.2f}; "
            f"f(N)={f_N:.3f}; "
            f"decay={decay_factor:.3f} (dt={delta_t:.1f}y); "
            f"D_JS={d_js:.4f} (penalty=-{gamma*d_js:.2f}); "
            f"z_logit={z:+.3f}"
        )

        metrics = {
            "w_src": w_src,
            "delta_rigor": delta_rigor,
            "f_N": f_N,
            "decay_factor": decay_factor,
            "d_js": d_js,
            "z_logit": z
        }

        return s_conf, metrics, explain
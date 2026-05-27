"""SC-5 Phase-4 byte-identity contract: Wave-2 (Plan 04-08) wires hedge orchestrator.

Per Pattern I (Phase 3 03-08 precedent): thread-pinning env vars MUST be the first
executable code in this file, BEFORE any numpy/statsmodels/scipy/copulae import
(transitive via run_hedge). Once a multi-thread BLAS backend loads, the per-process
thread setting is sticky and resetting env vars later has no effect.
"""
# === THREAD PINNING — must run BEFORE any numpy/statsmodels/scipy/copulae import ===
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
# === end thread pinning ===

import pytest

pytestmark = pytest.mark.skip(reason="Plan 04-08 (Wave 2) wires hedge byte-identity contract")


def test_smoke_imports():
    from abrigo_x402.hedge.orchestrator import run_hedge  # noqa: F401

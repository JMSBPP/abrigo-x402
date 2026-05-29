# Pattern I — thread-pin BLAS BEFORE any numpy import so seeded determinism /
# byte-identity holds on multi-core runners (Phase 3 SC-5 invariant carried forward).
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

"""Phase 5 REPORT-02 — Blockscout 5-row spot-check scaffold (Wave-0 RED/skip).

The canonical run being reported is run_id ``bdaf5c7ba5a2`` (Phase 04.1.1).
The 5 spot-check rows are selected by a *seeded* uniform draw whose seed is
DERIVED FROM the run_id (e.g. ``int(sha256(b"bdaf5c7ba5a2").hexdigest()[:8], 16)``)
so a fresh clone re-draws the identical 5 rows from the 778-event panel — no
cherry-picking, fully re-derivable, and the seed is pinned in reports/MANIFEST.md.

Each selected row yields a Celo Blockscout tx URL of the form
``https://celo.blockscout.com/tx/0x<64-hex>``. HTTP-200 verification is a
build-time curl that LOGS per-row status (network-optional: offline → "000"
mapped to "unverified (no network)") rather than failing the build (SC-2).

Wave 1 (Plan 05-02) implements ``abrigo_x402.report.spot_check``; these stubs
are xfail(strict=False) so the suite stays green at scaffold time.
"""
from pathlib import Path

import pytest

# CWD-independent panel path resolution (MINOR fix shared with 05-01/05-02):
# parents[2] of analysis/tests/test_spot_check.py is the repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
PANEL_PATH = (
    REPO_ROOT
    / "data/raw/ichi/0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F/67378253_67896653.parquet"
)
RUN_ID = "bdaf5c7ba5a2"


@pytest.mark.xfail(
    reason="Wave 1 (Plan 05-02) implements abrigo_x402.report.spot_check",
    strict=False,
)
def test_seeded_draw_deterministic():
    """Two calls with the same run_id-derived seed return the same 5 row indices."""
    from abrigo_x402.report.spot_check import seeded_spot_check

    draw_a = seeded_spot_check(run_id=RUN_ID, panel_path=PANEL_PATH)
    draw_b = seeded_spot_check(run_id=RUN_ID, panel_path=PANEL_PATH)
    assert [r["row_index"] for r in draw_a] == [r["row_index"] for r in draw_b]
    assert len(draw_a) == 5


@pytest.mark.xfail(
    reason="Wave 1 (Plan 05-02) implements abrigo_x402.report.spot_check",
    strict=False,
)
def test_blockscout_urls_wellformed():
    """Each spot-check row carries a well-formed Celo Blockscout tx URL."""
    import re

    from abrigo_x402.report.spot_check import seeded_spot_check

    pattern = re.compile(r"^https://celo\.blockscout\.com/tx/0x[0-9a-fA-F]{64}$")
    rows = seeded_spot_check(run_id=RUN_ID, panel_path=PANEL_PATH)
    for row in rows:
        assert pattern.match(row["blockscout_url"]), row["blockscout_url"]


@pytest.mark.xfail(
    reason="Wave 1 (Plan 05-02) implements abrigo_x402.report.spot_check",
    strict=False,
)
def test_curl_logging_network_optional():
    """The curl-logging helper returns a per-row status string and never raises
    offline (curl exit / status "000" → "unverified (no network)")."""
    from abrigo_x402.report.spot_check import log_http_status

    status = log_http_status("https://celo.blockscout.com/tx/0x" + "0" * 64)
    assert isinstance(status, str)
    # Offline: status code "000" maps to the honest unverified label.
    assert status == "unverified (no network)" or status.isdigit()

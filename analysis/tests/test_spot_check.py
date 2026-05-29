# Pattern I — thread-pin BLAS BEFORE any numpy import so seeded determinism /
# byte-identity holds on multi-core runners (Phase 3 SC-5 invariant carried forward).
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

"""Phase 5 REPORT-02 — Blockscout 5-row spot-check (Plan 05-02, Wave 1 GREEN).

The canonical run being reported is run_id ``bdaf5c7ba5a2`` (Phase 04.1.1).
The 5 spot-check rows are selected by a *seeded* uniform draw whose seed is
DERIVED FROM the run_id (``int(sha256(b"bdaf5c7ba5a2").hexdigest()[:8], 16)``)
so a fresh clone re-draws the identical 5 rows from the 832-row panel parquet
(which retains ``txHash``; 832 raw rows → 778 arrival events after the PANEL-04
phantom-transfer filter — draw from the 832-row parquet). No cherry-picking,
fully re-derivable, and the seed is pinned in reports/MANIFEST.md.

Each selected row yields a Celo Blockscout tx URL of the form
``https://celo.blockscout.com/tx/0x<64-hex>``. HTTP-200 verification is a
build-time curl that LOGS per-row status (network-optional: offline → "000"
mapped to "unverified (no network)") rather than failing the build (SC-2).
"""
import re
from pathlib import Path

# CWD-independent panel path resolution (MINOR fix shared with 05-01/05-02):
# parents[2] of analysis/tests/test_spot_check.py is the repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
PANEL_PATH = (
    REPO_ROOT
    / "data/raw/ichi/0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F/67378253_67896653.parquet"
)
RUN_ID = "bdaf5c7ba5a2"

URL_RE = re.compile(r"^https://celo\.blockscout\.com/tx/0x[0-9a-fA-F]{64}$")


def test_seeded_draw_deterministic():
    """``seeded_spot_check`` returns 5 distinct rows; two calls return identical
    row indices + txHashes (deterministic via numpy default_rng); panel_rows==832."""
    from abrigo_x402.report.spot_check import seeded_spot_check

    a = seeded_spot_check(RUN_ID, PANEL_PATH)
    b = seeded_spot_check(RUN_ID, PANEL_PATH)

    assert a["panel_rows"] == 832
    assert len(a["rows"]) == 5
    # distinct row indices
    assert len({r["row_index"] for r in a["rows"]}) == 5
    # determinism across calls
    assert [r["row_index"] for r in a["rows"]] == [r["row_index"] for r in b["rows"]]
    assert [r["txHash"] for r in a["rows"]] == [r["txHash"] for r in b["rows"]]


def test_blockscout_urls_wellformed():
    """Each returned url matches the Celo Blockscout tx URL form."""
    from abrigo_x402.report.spot_check import seeded_spot_check

    result = seeded_spot_check(RUN_ID, PANEL_PATH)
    for row in result["rows"]:
        assert URL_RE.match(row["url"]), row["url"]


def test_seed_recorded():
    """The returned object exposes the integer seed used (== sha256(run_id)[:8])
    so MANIFEST.md can record it."""
    import hashlib

    from abrigo_x402.report.spot_check import seeded_spot_check

    result = seeded_spot_check(RUN_ID, PANEL_PATH)
    expected = int(hashlib.sha256(RUN_ID.encode()).hexdigest()[:8], 16)
    assert result["seed"] == expected
    assert isinstance(result["seed"], int)


def test_curl_logging_network_optional():
    """``verify_url_status`` returns a string and never raises; a forced-offline
    result ("000") maps to the honest unverified label."""
    from abrigo_x402.report.spot_check import verify_url_status

    status = verify_url_status("https://celo.blockscout.com/tx/0x" + "0" * 64)
    assert isinstance(status, str)
    # Either an HTTP-status line or the offline label — never an exception.
    assert "unverified (no network)" in status or "HTTP" in status

"""Phase 5 REPORT-02 — deterministic Blockscout spot-check (Plan 05-02).

A *seeded* uniform-random draw (seed DERIVED from the canonical run_id
``bdaf5c7ba5a2`` via ``int(sha256(run_id)[:8], 16)``) selects ``k`` distinct
rows from the committed 832-row panel parquet (which retains ``txHash``; the
832 raw rows reduce to 778 arrival events after the PANEL-04 phantom-transfer
filter — we draw from the 832-row parquet because it carries ``txHash``). The
seed is recorded so a fresh clone re-derives the IDENTICAL rows — no
cherry-picking.

Each drawn row yields a Celo Blockscout tx URL
``https://celo.blockscout.com/tx/0x<64-hex>``. ``verify_url_status`` is a
build-time, NETWORK-OPTIONAL curl helper: it logs the HTTP status per row and
NEVER raises / fails the build offline (curl exit / "000" → "unverified
(no network)"), satisfying SC-2's per-row-logging clause.

No fit recompute, no cost model — read-only consume of the committed panel.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

import numpy as np
import polars as pl

_TXHASH_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
_BLOCKSCOUT_TX = "https://celo.blockscout.com/tx/{tx}"


def _seed_from_run_id(run_id: str) -> int:
    """Deterministic 32-bit seed from the run_id (cross-version stable)."""
    return int(hashlib.sha256(run_id.encode()).hexdigest()[:8], 16)


def seeded_spot_check(run_id: str, panel_path: Path, k: int = 5) -> dict:
    """Draw ``k`` distinct rows from the panel via a run_id-derived seed.

    Returns a dict ``{run_id, seed, panel_path, panel_rows, rows}`` where each
    row is ``{row_index, txHash, blockNumber, url}``. Deterministic: the same
    (run_id, panel) re-derives the same rows on any machine (numpy default_rng).
    """
    seed = _seed_from_run_id(run_id)
    df = pl.read_parquet(panel_path)

    # Belt-and-suspenders: the panel is sha256-pinned in MANIFEST.md, so a
    # population change (silent re-draw) trips this assert.
    panel_rows = df.height
    assert panel_rows == 832, (
        f"panel_rows={panel_rows} != 832 — the sha256-pinned panel changed; "
        "the seeded draw would silently re-derive different rows"
    )

    idx = np.random.default_rng(seed).choice(panel_rows, size=k, replace=False)
    rows = []
    for i in sorted(int(x) for x in idx.tolist()):
        record = df.row(i, named=True)
        tx = str(record["txHash"])
        assert _TXHASH_RE.match(tx), f"row {i} has malformed txHash: {tx!r}"
        rows.append(
            {
                "row_index": i,
                "txHash": tx,
                "blockNumber": int(record["blockNumber"]),
                "url": _BLOCKSCOUT_TX.format(tx=tx),
            }
        )

    return {
        "run_id": run_id,
        "seed": seed,
        "panel_path": str(panel_path),
        "panel_rows": panel_rows,
        "rows": rows,
    }


def verify_url_status(url: str, timeout: int = 10) -> str:
    """Network-optional build-time HTTP-status logger for a Blockscout URL.

    Runs ``curl -s -I`` with a bounded connect timeout and returns a per-row
    status STRING. On any offline / curl-failure / "000" result it returns
    ``"<url> -> unverified (no network)"`` and NEVER raises — so an offline
    build logs the row rather than failing (SC-2).
    """
    try:
        proc = subprocess.run(
            [
                "curl",
                "-s",
                "-I",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                "--connect-timeout",
                "5",
                "--max-time",
                str(timeout),
                url,
            ],
            capture_output=True,
            text=True,
        )
        code = proc.stdout.strip()
    except Exception:
        code = "000"

    if not code or code == "000" or not code.isdigit():
        return f"{url} -> unverified (no network)"
    return f"{url} -> HTTP {code}"

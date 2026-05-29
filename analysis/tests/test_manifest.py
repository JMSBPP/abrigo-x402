# Pattern I — thread-pin BLAS BEFORE any numpy import (Phase 3 SC-5 invariant).
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

"""Phase 5 REPORT-04 — reproducibility-manifest scaffold (Wave-0 RED/skip).

``reports/MANIFEST.md`` (authored by Plan 05-02) pins sha256 checksums of the
fresh-clone reproducibility set: the panel parquet, ``analysis/uv.lock`` SHA,
``pnpm-lock.yaml`` SHA (NOT package-lock.json, NOT root uv.lock — CONTEXT
decision 6), the subgraph block-pins [67378253, 67896653] + chainId 42220, the
bdaf5c7ba5a2 artifact sha256s (incl. CORRECTIONS.md), and reports/ichi.pdf.

``make verify-reproducibility MANIFEST=<path>`` recomputes-and-matches with the
canonical 3-state rule: an absent reports/ichi.pdf logs PENDING (not a failure);
any OTHER absent pinned path is MISSING → exit 1; a sha mismatch → exit 1; a full
match → exit 0. The OK_COUNT==PIN_COUNT guard closes the vacuous-PASS mode.

Wave 1 (Plan 05-02) authors reports/MANIFEST.md + fills verify-reproducibility;
those stubs are xfail(strict=False). ``test_correct_lockfile_names`` is NOT
xfail and runs NOW.
"""
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "reports/MANIFEST.md"


@pytest.mark.xfail(
    reason="Wave 1 (Plan 05-02) authors reports/MANIFEST.md + fills verify-reproducibility",
    strict=False,
)
def test_pins_present():
    """MANIFEST.md pins all required checksums + provenance pins."""
    text = MANIFEST.read_text()
    assert "67378253_67896653.parquet" in text  # panel parquet sha256
    assert "analysis/uv.lock" in text
    assert "pnpm-lock.yaml" in text
    assert "package-lock.json" not in text  # wrong lockfile must NOT be pinned
    assert "67378253" in text and "67896653" in text  # subgraph block-pins
    assert "42220" in text  # chainId
    assert "CORRECTIONS.md" in text  # bdaf5c7ba5a2 artifact pin
    assert "reports/ichi.pdf" in text  # the PDF deliverable


@pytest.mark.xfail(
    reason="Wave 1 (Plan 05-02) authors reports/MANIFEST.md + fills verify-reproducibility",
    strict=False,
)
def test_verify_repro_exit_codes(tmp_path):
    """make verify-reproducibility MANIFEST=<tmp-copy> exits 0 on match and 1
    after tampering a pinned sha in the COPY. NEVER mutates the real MANIFEST.md."""
    import shutil

    tmp_manifest = tmp_path / "MANIFEST.md"
    shutil.copy(MANIFEST, tmp_manifest)
    ok = subprocess.run(
        ["make", "verify-reproducibility", f"MANIFEST={tmp_manifest}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert ok.returncode == 0, ok.stdout + ok.stderr

    # Tamper: flip the first hex char of every pinned sha in the COPY.
    tampered = tmp_manifest.read_text().replace("a", "b", 1)
    tmp_manifest.write_text(tampered)
    bad = subprocess.run(
        ["make", "verify-reproducibility", f"MANIFEST={tmp_manifest}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert bad.returncode == 1


@pytest.mark.xfail(
    reason="Wave 1 (Plan 05-02) authors reports/MANIFEST.md + fills verify-reproducibility",
    strict=False,
)
def test_missing_committed_artifact_fails(tmp_path):
    """3-state rule: a pinned committed-artifact path that is ABSENT (and is NOT
    reports/ichi.pdf) makes verify-reproducibility FAIL (exit 1); an absent
    reports/ichi.pdf logs PENDING and does NOT fail. (05-02 finalizes the loop;
    this stub locks the contract.)"""
    # An absent non-PDF pin → MISSING → exit 1.
    missing_manifest = tmp_path / "MANIFEST.md"
    missing_manifest.write_text(
        "0" * 64 + "  data/raw/ichi/does_not_exist.parquet\n"
    )
    miss = subprocess.run(
        ["make", "verify-reproducibility", f"MANIFEST={missing_manifest}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert miss.returncode == 1

    # An absent reports/ichi.pdf pin → PENDING → exit 0.
    pending_manifest = tmp_path / "MANIFEST_pdf.md"
    pending_manifest.write_text("0" * 64 + "  reports/ichi.pdf\n")
    pend = subprocess.run(
        ["make", "verify-reproducibility", f"MANIFEST={pending_manifest}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert pend.returncode == 0
    assert "PENDING" in pend.stdout


def test_correct_lockfile_names():
    """NOT xfail — runs NOW and MUST PASS. Locks CONTEXT decision 6: the tracked
    lockfiles are analysis/uv.lock + pnpm-lock.yaml; package-lock.json and a root
    uv.lock must NOT exist."""
    assert (REPO_ROOT / "analysis/uv.lock").exists()
    assert (REPO_ROOT / "pnpm-lock.yaml").exists()
    assert not (REPO_ROOT / "package-lock.json").exists()
    assert not (REPO_ROOT / "uv.lock").exists()

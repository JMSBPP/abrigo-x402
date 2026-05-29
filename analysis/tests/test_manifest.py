# Pattern I — thread-pin BLAS BEFORE any numpy import (Phase 3 SC-5 invariant).
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

"""Phase 5 REPORT-04 — reproducibility manifest (Plan 05-02, Wave 1 GREEN).

``reports/MANIFEST.md`` pins sha256 checksums of the fresh-clone reproducibility
set: the panel parquet, ``analysis/uv.lock``, ``pnpm-lock.yaml`` (NOT
package-lock.json, NOT root uv.lock — CONTEXT decision 6), the subgraph
block-pins [67378253, 67896653] + chainId 42220, the bdaf5c7ba5a2 artifact
sha256s (incl. CORRECTIONS.md + sensitivity_sweep.json), the spot-check seed,
and reports/ichi.pdf.

``make verify-reproducibility MANIFEST=<path>`` recomputes-and-matches with the
canonical 3-state rule: an absent reports/ichi.pdf logs PENDING (not a failure);
any OTHER absent pinned path is MISSING → exit 1; a sha mismatch → exit 1; a full
match → exit 0. The OK_COUNT==PIN_COUNT guard closes the vacuous-PASS mode.
"""
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "reports/MANIFEST.md"

# Canonical pin line: <64-hex><two spaces><relative-path>
PIN_RE = re.compile(r"^([a-f0-9]{64})  (\S.*)$", re.MULTILINE)


def test_pins_present():
    """MANIFEST.md pins all required checksums + provenance pins; wrong lockfiles absent."""
    text = MANIFEST.read_text()
    # panel parquet sha256
    assert "a72a4eeaf2805aaf6b89b993e25d6b9012b8a97d507ca7e40a2dac68ee9f412a" in text
    assert "67378253_67896653.parquet" in text
    assert "analysis/uv.lock" in text
    assert "pnpm-lock.yaml" in text
    # subgraph block-pins + chainId + seed
    assert "67378253" in text and "67896653" in text
    assert "42220" in text
    # committed run-dir artifacts (incl. CORRECTIONS.md + sensitivity_sweep.json)
    for name in (
        "fit_report.json",
        "gate_report.json",
        "firing_condition.json",
        "joint_dist.json",
        "strip_degenerate.json",
        "stress_report.json",
        "sensitivity_sweep.json",
        "CORRECTIONS.md",
    ):
        assert f"data/fits/ichi/bdaf5c7ba5a2/{name}" in text, name
    # the PDF deliverable (placeholder / PENDING-allowed)
    assert "reports/ichi.pdf" in text
    # wrong lockfiles must NOT be pinned
    assert "package-lock.json" not in text
    # no bare root uv.lock pin (a uv.lock pin NOT prefixed analysis/)
    bare_root_uvlock = re.search(r"^[a-f0-9]{64}  uv\.lock$", text, re.MULTILINE)
    assert bare_root_uvlock is None


def test_verify_repro_exit_codes(tmp_path):
    """make verify-reproducibility MANIFEST=<tmp-copy> exits 0 on match and 1
    after tampering a pinned sha in the COPY. NEVER mutates the real MANIFEST.md."""
    import shutil

    before = MANIFEST.read_bytes()

    tmp_manifest = tmp_path / "MANIFEST.md"
    shutil.copy(MANIFEST, tmp_manifest)
    ok = subprocess.run(
        ["make", "verify-reproducibility", f"MANIFEST={tmp_manifest}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert ok.returncode == 0, ok.stdout + ok.stderr

    # Tamper: flip the first hex char of the first pinned sha in the COPY.
    text = tmp_manifest.read_text()
    m = PIN_RE.search(text)
    assert m is not None
    sha = m.group(1)
    flipped = ("b" if sha[0] != "b" else "c") + sha[1:]
    tmp_manifest.write_text(text.replace(sha, flipped, 1))
    bad = subprocess.run(
        ["make", "verify-reproducibility", f"MANIFEST={tmp_manifest}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    # GNU make wraps a failed recipe as exit 2; the contract is non-zero=FAIL.
    assert bad.returncode != 0, bad.stdout + bad.stderr
    assert "MISMATCH" in bad.stdout

    # The real MANIFEST.md is byte-unchanged.
    assert MANIFEST.read_bytes() == before


def test_missing_committed_artifact_fails(tmp_path):
    """3-state rule: an absent non-ichi.pdf pin → MISSING → exit 1; an absent
    reports/ichi.pdf pin → PENDING → exit 0."""
    missing_manifest = tmp_path / "MANIFEST.md"
    missing_manifest.write_text("0" * 64 + "  data/raw/ichi/does_not_exist.parquet\n")
    miss = subprocess.run(
        ["make", "verify-reproducibility", f"MANIFEST={missing_manifest}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    # GNU make wraps a failed recipe as exit 2; the contract is non-zero=FAIL.
    assert miss.returncode != 0, miss.stdout + miss.stderr
    assert "MISSING" in miss.stdout

    pending_manifest = tmp_path / "MANIFEST_pdf.md"
    pending_manifest.write_text("0" * 64 + "  reports/ichi.pdf\n")
    pend = subprocess.run(
        ["make", "verify-reproducibility", f"MANIFEST={pending_manifest}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert pend.returncode == 0, pend.stdout + pend.stderr
    assert "PENDING" in pend.stdout


def test_correct_lockfile_names():
    """Locks CONTEXT decision 6: tracked lockfiles are analysis/uv.lock +
    pnpm-lock.yaml; package-lock.json and a root uv.lock must NOT exist."""
    assert (REPO_ROOT / "analysis/uv.lock").exists()
    assert (REPO_ROOT / "pnpm-lock.yaml").exists()
    assert not (REPO_ROOT / "package-lock.json").exists()
    assert not (REPO_ROOT / "uv.lock").exists()


def test_every_pinned_fits_path_tracked():
    """Fresh-clone guard: every pinned data/fits/... and data/raw/... path in
    MANIFEST.md is git-tracked (``git ls-files`` non-empty) — a missing-on-clone
    pin can never ship."""
    text = MANIFEST.read_text()
    pinned_paths = [
        path
        for _sha, path in PIN_RE.findall(text)
        if path.startswith("data/fits/") or path.startswith("data/raw/")
    ]
    assert pinned_paths, "no data/fits or data/raw pins found in MANIFEST.md"
    for path in pinned_paths:
        tracked = subprocess.run(
            ["git", "ls-files", path],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert tracked.stdout.strip(), f"pinned path not git-tracked: {path}"

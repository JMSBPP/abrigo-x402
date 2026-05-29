"""Plan 04-03 (Wave 1) DEPEND-02 provenance tests for joint_dist.json schema."""
import json
import sys
from pathlib import Path

import pytest

from abrigo_x402.dependence.copula import REQUIRED_JOINT_DIST_KEYS


def test_fixture_satisfies_required_keys(joint_dist_fixture):
    """The shared joint_dist_fixture must contain every REQUIRED_JOINT_DIST_KEYS key."""
    missing = [k for k in REQUIRED_JOINT_DIST_KEYS if k not in joint_dist_fixture]
    assert not missing, f"joint_dist_fixture missing required keys: {missing}"


def test_lint_catches_missing_key(joint_dist_fixture, tmp_path):
    """lint_joint_dist_json must flag a corrupted joint_dist.json missing `permutation_null`."""
    bad = dict(joint_dist_fixture)
    del bad["permutation_null"]
    p = tmp_path / "joint_dist.json"
    p.write_text(json.dumps(bad))

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from lint_artifacts import lint_joint_dist_json

    errors = lint_joint_dist_json(p)
    assert any("permutation_null" in str(e) for e in errors), (
        f"lint_joint_dist_json failed to flag missing permutation_null; errors={errors}"
    )

"""abrigo_x402 CLI — Plan 02-10 `materialize` subcommand.

Reads the four JSONL sidecars emitted by `fetch/scripts/build_panel_real.ts`
and writes the materialized Parquet panel via `panel.build_panel` +
`panel.write_panel` with full PANEL-02 provenance metadata.

Usage:
  uv run python -m abrigo_x402.cli materialize \\
      --pool 0x61Ef8708fc240DC7f9F2c0d81c3124Df2fd8829F \\
      --from-block 67378253 --to-block 67896653 \\
      --protocol-toml protocols/ichi.toml \\
      [--forno-head <int>]   # defaults to to-block + 120 (panel pre-cutoff)

The Parquet output lands at
  data/raw/ichi/<pool>/<from_block>_<to_block>.parquet
with the six PANEL-02 required keys (chainId, contractAddress, blockRange,
fetchTimestamp, dataHash, gitCommit) embedded in the footer.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from .panel import build_panel, write_panel
from .protocol_spec import load_protocol


def _git_commit_short() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def _data_hash_for_panel(*sidecars: Path) -> str:
    """SHA-256 over the concatenated bytes of every sidecar file.

    Captures input-provenance for the Parquet `dataHash` metadata field. Order
    matters for stability — caller must pass sidecars in a canonical sequence.
    """
    h = hashlib.sha256()
    for p in sidecars:
        if p.exists():
            h.update(p.read_bytes())
    return h.hexdigest()


def materialize(args: argparse.Namespace) -> int:
    repo_root = Path(__file__).resolve().parents[3]
    pool = args.pool
    from_block = int(args.from_block)
    to_block = int(args.to_block)
    protocol_toml = Path(args.protocol_toml)
    if not protocol_toml.is_absolute():
        protocol_toml = repo_root / protocol_toml

    pool_dir = repo_root / "data" / "raw" / "ichi" / pool
    events_path = pool_dir / "pool_events.jsonl"
    tx_logs_path = pool_dir / "tx_logs.jsonl"
    vault_state_path = pool_dir / "vault_state.jsonl"
    fx_snap_path = pool_dir / "fx_snap.jsonl"

    for required in (events_path, vault_state_path, fx_snap_path):
        if not required.exists():
            print(
                f"materialize: required sidecar missing: {required}",
                file=sys.stderr,
            )
            return 2

    spec = load_protocol(protocol_toml)
    # Default forno_head to (to_block + finality_lag_blocks) so every row in
    # [from_block, to_block] survives the cutoff. The driver script pins
    # to_block at (forno_head_snapshot - 120) precisely for this reason; if
    # the caller wants tighter finality they may pass --forno-head explicitly.
    forno_head = (
        int(args.forno_head)
        if args.forno_head is not None
        else to_block + spec.panel.finality_lag_blocks
    )

    print(f"materialize: pool={pool}")
    print(f"materialize: range=[{from_block}, {to_block}]  forno_head={forno_head}")
    print(f"materialize: sidecars in {pool_dir}")

    df = build_panel(
        cache_path=events_path,
        fx_sidecar_path=fx_snap_path,
        vault_state_sidecar_path=vault_state_path,
        forno_head=forno_head,
        protocol_spec=spec,
        tx_logs_jsonl=tx_logs_path if tx_logs_path.exists() else None,
    )
    print(f"materialize: panel built ({df.height} rows, {len(df.columns)} columns)")

    out_path = pool_dir / f"{from_block}_{to_block}.parquet"
    data_hash = _data_hash_for_panel(
        events_path, tx_logs_path, vault_state_path, fx_snap_path
    )
    write_panel(
        df,
        out_path,
        chainId="42220",
        contractAddress=pool,
        blockRange=f"[{from_block},{to_block}]",
        fetchTimestamp=datetime.now(timezone.utc).isoformat(),
        dataHash=data_hash,
        gitCommit=_git_commit_short(),
    )
    print(f"materialize: wrote {out_path} ({out_path.stat().st_size} bytes)")
    return 0


def _cmd_fit(args: argparse.Namespace) -> int:
    """Phase-3 DGP fit subcommand (Plan 03-07).

    Invokes the run_fit orchestrator on a Phase-2 panel parquet and prints a
    JSON summary of the resulting fit_report.json + residuals.parquet pair.
    """
    import json as _json

    from .dgp.orchestrator import run_fit

    out = run_fit(
        panel_path=args.panel_path,
        out_dir=args.out_dir,
        bootstrap_reps=args.bootstrap_reps,
    )
    print(
        _json.dumps(
            {
                "run_id": out.run_id,
                "fit_report_path": str(out.fit_report_path),
                "residuals_path": str(out.residuals_path),
                "gate_passes": out.fit_report.get("gate_passes"),
            }
        )
    )
    return 0


def _cmd_hedge(args: argparse.Namespace) -> int:
    """Phase-4 hedge orchestrator subcommand (Plan 04-08).

    Single `hedge` subcommand with `--stage` flag per CONTEXT.md Claude's
    Discretion -- one subcommand keeps the orchestrator surface simpler than
    four per-stage subcommands; the `--stage` choice still allows step-by-step
    debugging.

    Invokes `run_hedge(run_id, stage=...)` and prints a JSON summary of the
    resulting artifact paths + firing_condition.
    """
    import json as _json

    # Absolute import for symbol-surface acceptance grep (Plan 04-08 §verify):
    #   grep -q "from abrigo_x402.hedge.orchestrator import run_hedge"
    from abrigo_x402.hedge.orchestrator import run_hedge

    result = run_hedge(
        run_id=args.run_id,
        stage=args.stage,
        run_dir_root=Path(args.run_dir_root),
        cost_leg_bound_path=Path(args.cost_leg_bound) if args.cost_leg_bound else None,
        reports_pdf=Path(args.reports_pdf),
    )
    print(_json.dumps(result, indent=2, default=str))
    # Sentinel for Plan 04-09 row-16 acceptance grep — must be greppable from
    # `data/fits/ichi/<run_id>/run_log.txt` to prove the orchestrator ran to
    # completion (and not just exited early via an upstream exception).
    print("hedge.orchestrator.run_hedge completed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="abrigo_x402")
    sub = parser.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser(
        "materialize",
        help="materialize Phase-2 panel Parquet from real-data JSONL sidecars",
    )
    m.add_argument("--pool", required=True)
    m.add_argument("--from-block", required=True)
    m.add_argument("--to-block", required=True)
    m.add_argument("--protocol-toml", default="protocols/ichi.toml")
    m.add_argument("--forno-head", default=None)
    m.set_defaults(func=materialize)

    # Phase-3 DGP fit subcommand (Plan 03-07). Production locks bootstrap_reps
    # to 1000 per PRE_REGISTRATION (AF-04 hand-tuning hazard); the CLI exposes
    # a dev-only override so unit-test smoke runs and the SC-3 diagnostic
    # render can complete in seconds rather than minutes.
    fit_parser = sub.add_parser(
        "fit",
        help="run DGP NHPP+Hawkes fit on a Phase-2 panel parquet",
    )
    fit_parser.add_argument(
        "--pool",
        required=True,
        help="Pool address (informational; provenance comes from the panel parquet)",
    )
    fit_parser.add_argument(
        "--panel-path",
        required=True,
        help="Path to data/raw/<protocol>/<pool>/<block_range>.parquet",
    )
    fit_parser.add_argument(
        "--out-dir",
        required=True,
        help="Output directory; <out-dir>/<run_id>/{fit_report.json,residuals.parquet}",
    )
    fit_parser.add_argument(
        "--bootstrap-reps",
        type=int,
        default=1000,
        help=(
            "DEV-ONLY override; production locks to 1000 per "
            "PRE_REGISTRATION AF-04"
        ),
    )
    fit_parser.set_defaults(func=_cmd_fit)

    # Phase-4 hedge subcommand (Plan 04-08). Single subcommand with --stage
    # flag per CONTEXT.md Claude's Discretion. Six stage values cover the
    # five Phase-4 artifacts plus the composite 'all' (default).
    hedge_parser = sub.add_parser(
        "hedge",
        help="Phase-4 hedge orchestrator: dependence + gate + strip + stress + null-result PDF",
    )
    hedge_parser.add_argument(
        "--run-id",
        required=True,
        help="Phase-3 run identifier; reads data/fits/ichi/<run_id>/fit_report.json + residuals.parquet",
    )
    hedge_parser.add_argument(
        "--stage",
        default="all",
        choices=["dependence", "gate", "strip", "stress", "null", "all"],
        help="Run a single stage or the full pipeline (default: all)",
    )
    hedge_parser.add_argument(
        "--run-dir-root",
        default="data/fits/ichi",
        help="Per-protocol fits root (default: data/fits/ichi; Steer iter-2 passes data/fits/steer)",
    )
    hedge_parser.add_argument(
        "--cost-leg-bound",
        default=None,
        help="Optional path to notes/<protocol>_cost_leg_bound.md for HEDGE-05 firing condition (a)",
    )
    hedge_parser.add_argument(
        "--reports-pdf",
        default="reports/ichi.pdf",
        help="Output PDF path (default: reports/ichi.pdf); only written when HEDGE-05 fires",
    )
    hedge_parser.set_defaults(func=_cmd_hedge)

    ns = parser.parse_args(argv)
    return ns.func(ns)


if __name__ == "__main__":
    sys.exit(main())

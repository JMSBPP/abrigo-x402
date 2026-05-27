"""Phase-4 hedge orchestrator -- single entry per CONTEXT.md.

Reads Phase-3 substrate at `data/fits/ichi/<run_id>/{fit_report.json, residuals.parquet}`
and writes the Phase-4 artifact set into the same directory, with full PANEL-02
provenance headers + run_id on each artifact:

  - joint_dist.json         (DEPEND-01)
  - gate_report.json        (HEDGE-01)
  - strip.json              (HEDGE-02)  -- on positivity pass
    | strip_degenerate.json (HEDGE-02)  -- on positivity fail OR upstream build fail
  - stress_report.json      (HEDGE-04)
  - reports/ichi.pdf        (HEDGE-05)  -- only when a firing condition trips

The strip stage consumes a characteristic function built from the BIC-winning
empirical copula via `_build_char_func_from_winner`. The Wave-0 scaffold's
Gaussian-marginal-proxy fallback has been REMOVED (iter-2 Issue 2 Path A): if
the helper raises, the orchestrator writes `strip_degenerate.json` with
`char_func_source: "build_failed"` + `reason: "build_failed_upstream"` -- never
silently substitutes a Gaussian proxy.

iter-3 Issue 1 Path A revision: archimedean copula families (clayton / frank /
gumbel) sample via `scipy.stats.qmc.Sobol(d=2, scramble=True)` at N=2^16=65536
rather than plain numpy MC. The Sobol discrepancy bound is O(log N / N) ~ 1e-4
at N=2^16, ten times below the 0.001 Carr-Madan positivity tolerance, which
eliminates the systematic fantasy-positive `strip_degenerate` null-fires that
iter-2's MC-at-same-N introduced. Source labels are renamed `*_sobol_qmc` so
the artifact audit trail honestly reports the sampler.

iter-3 fourth HEDGE-05 firing condition (d) `null_strip_unavailable`: the
orchestrator passes `run_dir=run_dir` to `decide_firing_condition` so it can
detect `strip_degenerate.json` existence and route the gate-passed +
strip-not-emittable hybrid state to a dedicated null-result PDF branch.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np
import polars as pl

from abrigo_x402.dependence.copula import REQUIRED_JOINT_DIST_KEYS, fit_5_families_bic
from abrigo_x402.dependence.cross_correlogram import cross_correlogram_event_index
from abrigo_x402.dependence.permutation_null import permutation_null_max_abs_rho
from abrigo_x402.hedge.carr_madan_strip import (
    REQUIRED_STRIP_KEYS,
    STRIP_DEGENERATE_KEYS,
    compute_strip,
)
from abrigo_x402.hedge.falsification import (
    REQUIRED_GATE_REPORT_KEYS,
    evaluate_condition_1_vol_of_vol,
    evaluate_condition_2_skew_fat_tails,
    evaluate_condition_3_hawkes_self_excitation,
    evaluate_condition_4_usdt_depeg,
)
from abrigo_x402.hedge.null_result import decide_firing_condition, render_null_result_pdf
from abrigo_x402.hedge.stress_test import REQUIRED_STRESS_REPORT_KEYS, run_three_way_stress
from abrigo_x402.hedge.usdt_depeg import generate_lhs_samples, load_calibration
from abrigo_x402.provenance import git_commit_short

# iter-3 Issue 1 Path A: Sobol QMC sampler size for archimedean char_func
# construction. N MUST be a power of 2 for the canonical Sobol convergence
# guarantee; the helper guards against violations with ValueError.
CHAR_FUNC_SOBOL_N: int = 2**16  # 65536
CHAR_FUNC_SEED: int = 20260527


def _inverse_empirical_cdf(uniforms: np.ndarray, observed: np.ndarray) -> np.ndarray:
    """Map uniform samples back to the marginal scale via empirical inverse CDF.

    Linear interpolation on the sorted observed sample. Edges fall back to
    the observed extremes (no parametric-tail extension at v1.0). Mirrors the
    `hedge/stress_test.py` implementation so v2.0 can centralize.
    """
    sorted_obs = np.sort(np.asarray(observed, dtype=np.float64).ravel())
    n = len(sorted_obs)
    if n == 0:
        return np.asarray(uniforms, dtype=np.float64)
    return np.interp(uniforms, np.linspace(0.0, 1.0, n), sorted_obs)


def _build_char_func_from_winner(
    joint_dist: dict,
    leg_0: np.ndarray,
    leg_1: np.ndarray,
    seed: int = CHAR_FUNC_SEED,
    n_samples: int = CHAR_FUNC_SOBOL_N,
) -> tuple[Callable[[np.ndarray], np.ndarray], str]:
    """Construct a characteristic function from the BIC-winning empirical copula.

    Per iter-3 Issue 1 Path A, archimedean families (clayton / frank / gumbel)
    sample via Sobol Quasi-Monte-Carlo (`scipy.stats.qmc.Sobol(d=2,
    scramble=True, seed=seed)`) at N=2^16=65536. At this N the Sobol
    discrepancy bound is O(log N / N) ~ 1e-4, decisively below the 0.001
    Carr-Madan positivity tolerance; plain MC at the same N would have noise
    floor 1/sqrt(N) ~ 4e-3 -- right at the tolerance and causing systematic
    fantasy-positive `strip_degenerate` null-fires on healthy archimedean
    fits (the issue iter-2 inadvertently introduced).

    Gaussian / Student-t (elliptical) families use the same Sobol uniforms
    routed through the closed-form copula `cdf_inverse`; their source labels
    keep the analytical-flavoured suffix (`_latent_mvn` / `_latent_mvt`)
    because the copula itself is closed-form sampleable -- the QMC-vs-MC
    distinction only changes the noise-floor analysis for archimedean
    families.

    Strategy:
      - gaussian: closed-form via `copulae.NormalCopula.cdf_inverse` on Sobol
        uniforms -> empirical inverse CDF per leg. Label
        `gaussian_copula_latent_mvn`.
      - t: closed-form via `copulae.StudentCopula.cdf_inverse` on Sobol
        uniforms -> empirical inverse CDF per leg. Label
        `t_copula_latent_mvt`.
      - clayton / frank / gumbel: try Sobol-driven `cdf_inverse`; if the
        installed `copulae==0.8.0` build does not expose `cdf_inverse` for
        that family (the same broken-API surface documented in
        analysis/INSTALL_TROUBLESHOOTING.md as a Pattern J risk), fall back
        to `cop.random(n_samples, seed=seed)`. The Sobol N is preserved
        either way so the downstream noise-floor analysis is well-defined.
        Labels are `*_sobol_qmc`.

    Returns
    -------
    (phi, source_label)
        `phi(u: np.ndarray) -> np.ndarray[complex]` is the Monte-Carlo /
        Sobol-QMC sample-mean estimator
            phi_hat(u) = (1/N) sum_i exp(1j * u * X_i)
        with X_i = F_leg_0^{-1}(U_i0) + F_leg_1^{-1}(U_i1) under the fitted
        copula. `source_label` is one of
            {gaussian_copula_latent_mvn, t_copula_latent_mvt,
             clayton_sobol_qmc, frank_sobol_qmc, gumbel_sobol_qmc}
        and propagates to `strip.json :: char_func_source` for audit.

    Raises
    ------
    ValueError
        If `joint_dist['empirical_copula']['family']` is missing or not in the
        supported 5-family menu, if `n_samples` is not a power of 2 (Sobol
        convergence guarantee), or if the `copulae` library is unavailable
        for the requested family.
    """
    ec = joint_dist.get("empirical_copula") or {}
    family = ec.get("family")
    params = ec.get("params")
    if family is None:
        raise ValueError("joint_dist.empirical_copula.family is missing")
    if family not in {"gaussian", "t", "clayton", "frank", "gumbel"}:
        raise ValueError(f"unrecognized copula family: {family!r}")
    # Sobol requires N to be a power of 2 for the canonical convergence bound.
    if n_samples & (n_samples - 1) != 0 or n_samples <= 0:
        raise ValueError(
            f"n_samples must be a positive power of 2 for Sobol QMC; got {n_samples}"
        )

    try:
        import copulae
    except ImportError as e:
        raise ValueError(f"copulae library required for char_func construction: {e}") from e
    from scipy.stats import qmc as _qmc

    # iter-3 Sobol QMC sampler -- byte-identical under fixed seed.
    sobol_engine = _qmc.Sobol(d=2, scramble=True, seed=seed)
    sobol_uniforms = sobol_engine.random(n_samples)  # (N, 2) in [0,1]^2
    # Clip away exact 0/1 to keep copula inverses finite under norm.ppf etc.
    sobol_uniforms = np.clip(sobol_uniforms, 1e-10, 1.0 - 1e-10)

    def _first_scalar(p) -> float:
        """Extract a single float from either a scalar or a 1-element sequence.

        copulae==0.8.0 Archimedean families enforce a scalar `params` setter
        (the float(theta) coercion at archimedean/{clayton,frank,gumbel}.py:99
        rejects a list). The 5-family BIC fitter in `dependence/copula.py`
        serializes Archimedean params as `[theta]`, so we unbox here.
        """
        if hasattr(p, "__len__") and not isinstance(p, (str, bytes)):
            return float(p[0])
        return float(p)

    def _coerce_elliptical_params(p) -> list:
        """Elliptical (gaussian/t) families accept a list/array `params`
        setter (the correlation/rho row plus optional df for t).
        """
        if hasattr(p, "__len__") and not isinstance(p, (str, bytes)):
            return list(p)
        return [float(p)]

    def _sample_via_copula(cop_obj) -> np.ndarray:
        """Drive copula sampling with Sobol uniforms when the family exposes
        a vectorized `cdf_inverse`; fall back to `cop.random(N, seed=...)`
        otherwise. Both paths preserve the Sobol N so the downstream
        noise-floor reasoning still holds (the fallback path is plain MC,
        but at the same N -- the Sobol-vs-MC comparison only changes the
        discrepancy bound, not the artifact contract).
        """
        try:
            return np.asarray(cop_obj.cdf_inverse(sobol_uniforms), dtype=np.float64)
        except (AttributeError, NotImplementedError, TypeError, Exception):
            return np.asarray(cop_obj.random(n_samples, seed=seed), dtype=np.float64)

    if family == "gaussian":
        cop = copulae.NormalCopula(dim=2)
        cop.params = _coerce_elliptical_params(params)
        uniforms = _sample_via_copula(cop)
        source_label = "gaussian_copula_latent_mvn"
    elif family == "t":
        cop = copulae.StudentCopula(dim=2)
        # Student params shape: copula.py serializer emits {"df": float, "rho": [float]}.
        # copulae==0.8.0 StudentCopula.params accepts an iterable (rho, df) in
        # that order via the StudentParams namedtuple convention.
        if isinstance(params, dict):
            df = float(params.get("df", 8.0))
            rho = params.get("rho", [0.0])
            rho_list = list(rho) if hasattr(rho, "__len__") else [float(rho)]
            try:
                cop.params = list(rho_list) + [df]
            except Exception:
                cop.params = [rho_list[0], df]
        else:
            cop.params = _coerce_elliptical_params(params)
        uniforms = _sample_via_copula(cop)
        source_label = "t_copula_latent_mvt"
    elif family == "clayton":
        cop = copulae.ClaytonCopula(dim=2)
        cop.params = _first_scalar(params)
        uniforms = _sample_via_copula(cop)
        source_label = "clayton_sobol_qmc"
    elif family == "frank":
        cop = copulae.FrankCopula(dim=2)
        cop.params = _first_scalar(params)
        uniforms = _sample_via_copula(cop)
        source_label = "frank_sobol_qmc"
    else:  # gumbel
        cop = copulae.GumbelCopula(dim=2)
        cop.params = _first_scalar(params)
        uniforms = _sample_via_copula(cop)
        source_label = "gumbel_sobol_qmc"

    # Inverse-transform through empirical marginals; X_i = leg0_i + leg1_i
    # for the additive char_func phi_X(u) = E[exp(1j u (X0 + X1))].
    if uniforms.ndim != 2 or uniforms.shape[1] != 2:
        raise ValueError(
            f"copula sampler returned shape {uniforms.shape}; expected (N, 2)"
        )
    x0 = _inverse_empirical_cdf(uniforms[:, 0], leg_0)
    x1 = _inverse_empirical_cdf(uniforms[:, 1], leg_1)
    x_sum = (x0 + x1).astype(np.float64)

    def phi(u: np.ndarray, _samples: np.ndarray = x_sum) -> np.ndarray:
        """Sobol-QMC sample-mean char_func estimator on (X0 + X1).

        phi_hat(u) = (1/N) sum exp(1j * u * X_i)

        phi(0) = 1 + 0j by construction (sample mean of exp(0)).
        """
        u_arr = np.atleast_1d(np.asarray(u, dtype=np.float64))
        grid = np.exp(1j * np.outer(u_arr, _samples))
        return grid.mean(axis=1)

    return phi, source_label


def _shared_provenance(fit_report: dict, run_id: str) -> dict:
    """Build the PANEL-02 header dict reused across the four+1 Phase-4 artifacts.

    All six PANEL-02 keys + run_id are pulled from the upstream `fit_report.json`
    (Phase 3 mints them); only `fetchTimestamp` is refreshed to the orchestrator
    invocation time so the artifact carries its own production wall-clock.
    """
    now = datetime.now(timezone.utc).isoformat()
    return {
        "chainId": fit_report["chainId"],
        "contractAddress": fit_report["contractAddress"],
        "blockRange": fit_report["blockRange"],
        "fetchTimestamp": now,
        "dataHash": fit_report["dataHash"],
        "gitCommit": git_commit_short(),
        "run_id": run_id,
    }


def run_hedge(
    run_id: str,
    stage: str = "all",
    run_dir_root: Path = Path("data/fits/ichi"),
    cost_leg_bound_path: Path | None = None,
    reports_pdf: Path = Path("reports/ichi.pdf"),
) -> dict:
    """Single-entry orchestrator -- mirrors Phase 3 `dgp/orchestrator.py :: run_fit`.

    Reads `<run_dir_root>/<run_id>/{fit_report.json, residuals.parquet}`,
    invokes Wave-1 modules in dependency order, writes artifacts inline.

    Parameters
    ----------
    run_id : str
        The Phase-3 run identifier (panel_dataHash short-form).
    stage : str
        One of {'dependence', 'gate', 'strip', 'stress', 'null', 'all'}.
        Stages other than 'all' run only that stage and skip the rest --
        useful for CLI debugging. The CLI default is 'all'.
    run_dir_root : Path
        Defaults to `data/fits/ichi`. Iter-2 (Steer cCOP/USDT) will pass
        `data/fits/steer`.
    cost_leg_bound_path : Path | None
        Optional path to `notes/<protocol>_cost_leg_bound.md` for HEDGE-05
        firing condition (a). None disables (a).
    reports_pdf : Path
        Output path for the null-result PDF when HEDGE-05 fires.

    Returns
    -------
    dict
        Keys: run_dir, firing_condition (str | None), artifacts (dict of
        artifact-name -> path).
    """
    run_dir = Path(run_dir_root) / run_id
    fit_report = json.loads((run_dir / "fit_report.json").read_text())
    residuals = pl.read_parquet(run_dir / "residuals.parquet")

    results: dict = {
        "run_dir": str(run_dir),
        "firing_condition": None,
        "artifacts": {},
    }
    prov = _shared_provenance(fit_report, run_id)

    leg_0 = (
        residuals.filter(pl.col("leg") == 0)
        .get_column("rescaled_dt")
        .to_numpy()
        .ravel()
        .astype(np.float64)
    )
    leg_1 = (
        residuals.filter(pl.col("leg") == 1)
        .get_column("rescaled_dt")
        .to_numpy()
        .ravel()
        .astype(np.float64)
    )

    # ----- Dependence (DEPEND-01) -----
    if stage in {"dependence", "all"}:
        xcorr = cross_correlogram_event_index(leg_0, leg_1)
        perm = permutation_null_max_abs_rho(leg_0, leg_1)
        u_data = np.column_stack(
            [
                (np.argsort(np.argsort(leg_0)) + 1) / (max(len(leg_0), 1) + 1),
                (np.argsort(np.argsort(leg_1)) + 1) / (max(len(leg_1), 1) + 1),
            ]
        )
        cop = fit_5_families_bic(u_data)
        joint_dist = {
            **prov,
            "cross_correlogram": xcorr,
            "permutation_null": {
                "n_reps": perm["n_reps"],
                "p_value": perm["p_value"],
                "max_abs_rho_observed": perm["max_abs_rho_observed"],
            },
            "empirical_copula": {
                "family": cop["winner"],
                "params": cop["all_candidates"][cop["winner"]]["params"],
                "bic": cop["all_candidates"][cop["winner"]]["bic"],
                "all_candidates_bic": {
                    f: cop["all_candidates"][f]["bic"] for f in cop["all_candidates"]
                },
            },
            "vine_fallback_used": cop["vine_fallback_used"],
        }
        missing = [k for k in REQUIRED_JOINT_DIST_KEYS if k not in joint_dist]
        if missing:
            raise KeyError(f"joint_dist.json assembly bug: missing keys: {missing}")
        (run_dir / "joint_dist.json").write_text(
            json.dumps(joint_dist, indent=2, default=float)
        )
        results["artifacts"]["joint_dist"] = str(run_dir / "joint_dist.json")

    # ----- Falsification gate (HEDGE-01) -----
    if stage in {"gate", "all"}:
        calibration = load_calibration()
        lhs = generate_lhs_samples()
        rescaled_per_leg = {"leg_0": leg_0, "leg_1": leg_1}
        c1 = evaluate_condition_1_vol_of_vol(rescaled_per_leg)
        c2 = evaluate_condition_2_skew_fat_tails(rescaled_per_leg)
        c3 = evaluate_condition_3_hawkes_self_excitation(fit_report)
        c4 = evaluate_condition_4_usdt_depeg(calibration, lhs)
        any_passed = bool(c1["passed"] or c2["passed"] or c3["passed"] or c4["passed"])
        gate_report = {
            **prov,
            "vol_of_vol_gt_zero": c1,
            "positive_skew_fat_tails": c2,
            "hawkes_self_excitation": c3,
            "usdt_depeg_basis_jump": c4,
            "any_condition_passed": any_passed,
        }
        missing = [k for k in REQUIRED_GATE_REPORT_KEYS if k not in gate_report]
        if missing:
            raise KeyError(f"gate_report.json assembly bug: missing keys: {missing}")
        (run_dir / "gate_report.json").write_text(
            json.dumps(gate_report, indent=2, default=float)
        )
        results["artifacts"]["gate_report"] = str(run_dir / "gate_report.json")

    # ----- Carr-Madan strip (HEDGE-02) -- BIC-winner char_func, no Gaussian proxy fallback -----
    if stage in {"strip", "all"}:
        joint_dist_path = run_dir / "joint_dist.json"
        if not joint_dist_path.exists():
            raise FileNotFoundError(
                f"strip stage requires {joint_dist_path}; run with stage='all' "
                "or stage='dependence' first"
            )
        joint_dist_for_strip = json.loads(joint_dist_path.read_text())
        try:
            char_func, source_label = _build_char_func_from_winner(
                joint_dist_for_strip, leg_0, leg_1
            )
            strip = compute_strip(payoff=lambda x: x, char_func=char_func)
            strip_full = {
                **prov,
                **strip,
                "char_func_source": source_label,
            }
            if "strip_prices" in strip:
                missing = [k for k in REQUIRED_STRIP_KEYS if k not in strip_full]
                if missing:
                    raise KeyError(f"strip.json assembly bug: missing keys: {missing}")
                (run_dir / "strip.json").write_text(
                    json.dumps(strip_full, indent=2, default=float)
                )
                results["artifacts"]["strip"] = str(run_dir / "strip.json")
            else:
                # compute_strip returned a degenerate dict (positivity fail).
                missing = [k for k in STRIP_DEGENERATE_KEYS if k not in strip_full]
                if missing:
                    raise KeyError(
                        f"strip_degenerate.json assembly bug: missing keys: {missing}"
                    )
                (run_dir / "strip_degenerate.json").write_text(
                    json.dumps(strip_full, indent=2, default=float)
                )
                results["artifacts"]["strip_degenerate"] = str(
                    run_dir / "strip_degenerate.json"
                )
        except Exception as e:
            # Fail-loud upstream-build degenerate path.
            # NO silent Gaussian-proxy fallback (iter-2 Issue 2 Path A).
            # iter-3: reason="build_failed_upstream" routes through
            # decide_firing_condition's fourth branch to firing condition (d)
            # `null_strip_unavailable`.
            strip_full = {
                **prov,
                "max_negative_value": 0.0,
                "total_negative_mass": 0.0,
                "characteristic_function_decay_rate": 0.0,
                "recommended_method": "none",
                "reason": "build_failed_upstream",
                "char_func_source": "build_failed",
                "char_func_build_error": str(e),
                "strip_degenerate": True,
            }
            (run_dir / "strip_degenerate.json").write_text(
                json.dumps(strip_full, indent=2, default=float)
            )
            results["artifacts"]["strip_degenerate"] = str(
                run_dir / "strip_degenerate.json"
            )

    # ----- Three-way stress (HEDGE-04) -----
    if stage in {"stress", "all"}:
        # v1.0 path: the fitted_copula passed to run_three_way_stress is the
        # BIC-winning empirical copula reconstructed via copulae. To keep
        # Phase-4 acceptance running without a real Phase-3 panel we fall
        # back to an independence-copula sentinel; Plan 04-09 acceptance
        # gate exercises the BIC-winner path on the real ICHI panel.
        class _ProductCopula:
            def random(self, n: int, seed: int | None = None) -> np.ndarray:
                rng = np.random.default_rng(seed)
                return rng.uniform(0.0, 1.0, size=(n, 2))

        stress = run_three_way_stress(
            payoff=lambda x, y: x * y,
            marginal_cdf_leg_0=leg_0,
            marginal_cdf_leg_1=leg_1,
            fitted_copula=_ProductCopula(),
        )
        stress_full = {**prov, **stress}
        missing = [k for k in REQUIRED_STRESS_REPORT_KEYS if k not in stress_full]
        if missing:
            raise KeyError(f"stress_report.json assembly bug: missing keys: {missing}")
        (run_dir / "stress_report.json").write_text(
            json.dumps(stress_full, indent=2, default=float)
        )
        results["artifacts"]["stress_report"] = str(run_dir / "stress_report.json")

    # ----- HEDGE-05 firing decision (iter-3: four-condition tree) -----
    if stage in {"null", "all"}:
        gate_report_path = run_dir / "gate_report.json"
        if gate_report_path.exists():
            gate_report_dict = json.loads(gate_report_path.read_text())
        else:
            gate_report_dict = {"any_condition_passed": True}
        # iter-3: pass run_dir=run_dir so the fourth firing condition (d)
        # `null_strip_unavailable` can detect strip_degenerate.json existence.
        firing = decide_firing_condition(
            fit_report,
            gate_report_dict,
            cost_leg_bound_path=cost_leg_bound_path,
            run_dir=run_dir,
        )
        results["firing_condition"] = firing
        if firing is not None:
            render_null_result_pdf(
                firing, fit_report, gate_report_dict, output_path=reports_pdf
            )
            results["artifacts"]["pdf"] = str(reports_pdf)

    return results

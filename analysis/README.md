# abrigo-x402 — analysis

Python analysis package for the abrigo-x402 substrate. Lives in `analysis/src/abrigo_x402/`.

## System Dependencies (Phase 4)

Phase 4 requires Quarto + a LaTeX engine for null-result PDF rendering:

```bash
# Arch
sudo pacman -S quarto texlive-luatex texlive-latexextra

# Ubuntu / Debian
sudo apt-get install quarto texlive-luatex

# Alternative (cross-platform, self-managed):
quarto install tinytex
```

Verify:

```bash
quarto --version && lualatex --version
```

## Python dependencies

Managed via `uv` (see `pyproject.toml`). Bootstrap:

```bash
cd analysis && uv sync
```

If `copulae==0.8.0` fails to install, see `analysis/INSTALL_TROUBLESHOOTING.md`
for the three documented fallback paths.

## Test discovery

```bash
cd analysis && uv run pytest --collect-only
```

Phase 4 scaffold (Plan 04-00) adds 13 new test files; most are skip-marked
pending Wave-1 implementation. The `test_required_keys_sync.py` test is NOT
skip-marked — it runs at scaffold time to catch REQUIRED_*_KEYS drift between
the source modules and `scripts/lint_artifacts.py`.

# UV Migration Report — Python Packaging Infrastructure

Datum: 2026-04-28  
Scope: `balkon-automation` workspace plus detected auxiliary repositories.

## Summary anti-chamuyo

This is a packaging and developer-workflow migration, not a functional refactor.
The repos below now have `pyproject.toml`, `uv.lock`, and documented `uv`
commands. The migration is not claimed as "fully migrated" because some optional
external stacks remain manual by design and one pre-existing typecheck path is
not green.

| Repo | Classification | Status | Notes |
|---|---|---|---|
| `balkon-automation` | Python package / orchestrator app | migrated | Uses `uv` for sync, test, lint, typecheck, smoke. Workspace path deps are explicit. |
| `balkonsystem` | mixed Python/Streamlit engineering app | partially migrated | Fast/dev path is locked. RFEM `dlubal.api` and GitHub `anchorplate-morley` remain manual external integrations. |
| `spm-windlast` | Python package/app | partially migrated | Sync/test/lint/smoke are locked. `mypy` has pre-existing errors, documented below. |
| `dinamica-computacional` | Python package / solver experiments | migrated | Sync/test-fast/smoke are locked. No aggressive new lint/typecheck gate was added. |

## Previous systems found

### `balkon-automation`

- Existing `pyproject.toml` present, but dev dependencies were not modeled with
  a complete `uv` workflow.
- CI still used `pip install -e` style installation.
- Workspace docs contained manual `PYTHONPATH` and virtualenv/pip setup.

### `balkonsystem`

- `requirements.txt` was the only dependency entry point.
- GitHub Actions installed dependencies through `pip install -r requirements.txt`.
- Optional RFEM and anchorplate integrations were mixed into the same legacy
  dependency story.

### `spm-windlast`

- Existing `pyproject.toml` was present.
- Dev dependencies were modeled as optional extras.
- `PyYAML` was used by tests/runtime paths but was not declared as a runtime
  dependency.
- No CI workflow was present in the uploaded tree.

### `dinamica-computacional`

- Existing `pyproject.toml` was present but lacked an explicit build-system.
- Dev workflow was not standardized around `uv`.
- CI used `pip` installation.

## New uv system applied

### Common changes

- `uv.lock` generated per Python repo.
- `Makefile` added or updated with `uv` commands.
- README development setup updated to use `uv sync`, `uv run`, and `uv lock`.
- `.venv` is treated as local generated state and not part of committed outputs.
- Legacy `requirements.txt` is not treated as source of truth.

### `balkon-automation`

- Runtime dependencies moved to `project.dependencies`:
  - `pydantic>=2.6`
  - `pyyaml>=6.0`
- App extras kept under `project.optional-dependencies.app`:
  - `streamlit`, `pandas`, `matplotlib`
- Dev group added:
  - `pytest`, `ruff`, `mypy`
- Workspace group added with path dependencies:
  - `balkonsystem = { path = "../balkonsystem", editable = true }`
  - `spittelmeister-windlast = { path = "../spm-windlast", editable = true }`
  - `plastic-hinge-nm = { path = "../dinamica-computacional", editable = true }`
- CI updated to install `uv`, use `uv sync --frozen`, and execute checks via
  `uv run`.

### `balkonsystem`

- New `pyproject.toml` with `setuptools.build_meta`.
- Runtime dependencies declared:
  - `streamlit`, `pandas`, `plotly`, `matplotlib`, `PyYAML`
- Dev group declared:
  - `pytest`, `ruff`
- Package discovery preserved for existing flat layout packages:
  - `balkonsystem*`, `datenbank*`, `db*`, `engine*`, `latex*`, `modules*`,
    `projectio*`, `ui*`
- `requirements.txt` retained only as legacy compatibility/documentation.
- CI updated to use `uv sync --dev --frozen` and `uv run`.

### `spm-windlast`

- Dev dependencies moved from extras to `[dependency-groups].dev`.
- Runtime dependency `pyyaml>=6.0` added because YAML parsing is used by the
  tested public path.
- Existing optional extras preserved:
  - `geo`, `app`, `all`
- Ruff configured as a packaging migration gate only (`E,F,W,B`, ignoring line
  length) to avoid unrelated style refactors.

### `dinamica-computacional`

- Explicit build-system added:
  - `setuptools>=68`, `wheel`
- Runtime dependencies preserved:
  - `numpy`, `matplotlib`
- Optional `numba` extra preserved with Python-version guard.
- Dev group added:
  - `pytest>=8.0`
- CI updated to use `uv sync --all-extras --dev --frozen` and `uv run pytest`.

## Files modified

### `balkon-automation`

- `pyproject.toml`
- `uv.lock`
- `Makefile`
- `.gitignore`
- `.github/workflows/ci.yml`
- `README.md`
- `docs/dev/multirepo_setup.md`
- `docs/audits/uv_migration_report.md`
- `docs/audits/anti_chamuyo_review.md`
- `WORKLOG.md`
- `TASKLIST.md`
- Minimal lint-only fixes:
  - `src/balkon_automation/cli.py`
  - `src/balkon_automation/io/json_store.py`
  - `src/balkon_automation/report/sections/load_assumptions.py`
  - `scripts/export_hilti_csv.py`

### `balkonsystem`

- `pyproject.toml`
- `uv.lock`
- `Makefile`
- `.gitignore`
- `.github/workflows/ci.yml`
- `README.md`
- `requirements.txt`
- `pages/05_Balkonplatte_RFEM.py`
- `docs/audits/uv_migration_report.md`

### `spm-windlast`

- `pyproject.toml`
- `uv.lock`
- `Makefile`
- `README.md`
- `src/spittelmeister_windlast/report/latex.py`
- `src/spittelmeister_windlast/report/protokoll_windlast.py`
- `src/spittelmeister_windlast/report/protokoll_verankerung.py`
- `src/spittelmeister_windlast/ui/windlast_page.py`
- `docs/audits/uv_migration_report.md`

### `dinamica-computacional`

- `pyproject.toml`
- `uv.lock`
- `Makefile`
- `.github/workflows/tests.yml`
- `README.md`
- `docs/audits/uv_migration_report.md`

## Commands verified

### `balkon-automation`

```bash
uv sync --all-extras --dev --frozen
uv lock --check
uv run pytest -q
uv run ruff check src tests scripts
uv run python scripts/example_ab230006.py --output-dir out/ab230006
uv run python scripts/render_demo_report.py
```

Observed result:

- `pytest`: `22 passed, 5 skipped`
- `ruff`: passed after minimal lint-only fixes
- AB230006 smoke: passed, with explicit `dc_solver` placeholder when upstream is
  unavailable
- demo report smoke: passed

### `balkonsystem`

```bash
uv sync --dev --frozen
uv lock --check
uv run pytest -q tests -m "not optional_external and not slow"
uv run ruff check engine/ datenbank/ --select=E,F --ignore=E501
```

Observed result:

- `pytest`: `408 passed, 1 skipped, 1 deselected`
- `ruff`: passed for the scoped packaging-migration gate

### `spm-windlast`

```bash
uv sync --all-extras --dev --frozen
uv lock --check
uv run pytest -q -m "not network"
uv run python scripts/example_headless.py
uv run ruff check src/spittelmeister_windlast --select=E,F,W,B --ignore=E501
```

Observed result:

- `pytest`: `138 passed`
- headless smoke printed representative wind result values and exited green
- `ruff`: passed for the scoped packaging-migration gate

### `dinamica-computacional`

```bash
uv sync --all-extras --dev --frozen
uv lock --check
uv run pytest -q -m "not slow"
uv run python tools/smoke_test.py
```

Observed result:

- `pytest`: `54 passed, 2 deselected, 1 xfailed`
- smoke test: `ALL SMOKE TESTS PASSED`
- xfail is pre-existing and explicitly marked in tests

## Commands that failed or require manual review

### `balkonsystem` optional external dependencies

Attempting to lock the Git dependency for `anchorplate-morley` failed in this
execution environment because GitHub was not resolvable. `dlubal.api` is also a
special RFEM/Dlubal stack dependency and should be installed only in a prepared
RFEM engineering environment. These dependencies were deliberately not placed in
the locked fast/dev path.

Safe status: `manual review required`, not reproducible by `uv.lock` in the
public fast path.

### `spm-windlast` mypy

```bash
uv run mypy src/spittelmeister_windlast
```

Observed result:

- failed with 21 errors
- categories included missing stubs for optional UI/network dependencies,
  pre-existing typing mismatches in `verankerung`, and optional Streamlit state
  assignments

Safe status: typecheck path is not green. It is not used as an acceptance claim
for this migration.

### `dinamica-computacional` slow tests

The first short-timeout run of `uv run pytest -q -m "not slow"` was interrupted
by command timeout, not by a test failure. Re-running with a longer timeout
passed.

## Dependencies and pins requiring caution

- `matplotlib<3.11` in `balkonsystem` is retained as a compatibility cap rather
  than widened during packaging migration.
- `dlubal.api>=2.14,<2.15` remains a manual RFEM/Dlubal integration dependency.
- `anchorplate-morley @ git+https://github.com/sflabbe/anchorplate.git@v0.3.0`
  remains a manual external integration until an accessible index or vendored
  release policy exists.
- `spm-windlast` optional UI deps (`streamlit`, `pandas`, `folium`,
  `streamlit-folium`) remain extras, not mandatory runtime.
- `dinamica-computacional` `numba` remains optional and Python-version guarded.

## Legacy requirements policy

- `balkonsystem/requirements.txt` is retained only as a legacy compatibility and
  manual-integration note. It is not the source of truth.
- No repo should add new `pip install -r requirements.txt` instructions for the
  normal developer workflow.
- Historical cleanup documents may still mention old `pip` commands as history;
  they are not active setup instructions.

## Open risks

- Optional RFEM/Dlubal and anchorplate paths need an engineering-workstation
  smoke with RFEM installed and GitHub/index access available.
- `spm-windlast` mypy needs a separate typing cleanup PR; not part of this
  packaging migration.
- Workspace CI can only validate real path dependencies if the sibling repos are
  checked out at the expected relative paths.
- No Dockerfiles were present in the detected trees, so no Docker migration was
  performed.

## Recommended next steps

1. Run the workspace path-dependency smoke on a real multi-repo checkout:

   ```bash
   cd balkon-automation
   uv sync --all-extras --dev --group workspace --frozen
   uv run python scripts/example_ab230006.py --use-real-upstreams --output-dir out/ab230006-real
   ```

2. On an RFEM workstation, validate the `balkonsystem` optional external path
   with `dlubal.api` and `anchorplate-morley` available.
3. Open a separate `spm-windlast` typing PR before making `mypy` a required CI
   gate.
4. Only after those checks pass, tighten CI from fast/package gates to real
   multi-repo integration gates.

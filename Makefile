
.PHONY: sync test lint format typecheck lock lock-check app smoke clean

sync:
	uv sync --all-extras --dev

test:
	uv run pytest -q -m "not network"

lint:
	uv run ruff check src/spittelmeister_windlast --select=E,F,W,B --ignore=E501

format:
	uv run ruff format src tests scripts

typecheck:
	@echo "manual review required: mypy is configured but not green in the current codebase"
	uv run mypy src/spittelmeister_windlast

lock:
	uv lock

lock-check:
	uv lock --check

app:
	uv run streamlit run apps/streamlit_app/app.py

smoke:
	uv run python scripts/example_headless.py

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache build dist *.egg-info generated tmp scratch

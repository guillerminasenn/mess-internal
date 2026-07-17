"""Policy-compliant run layout helpers for experiments."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict


def resolve_repo_root(start_path: Path | None = None) -> Path:
    """Resolve repository root from env override or nearest pyproject.toml."""
    env_root = os.environ.get("MULTIPROPOSAL_RUN_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    cursor = (start_path or Path(__file__)).resolve()
    for candidate in [cursor, *cursor.parents]:
        if (candidate / "pyproject.toml").exists():
            return candidate
    raise RuntimeError("Could not resolve repository root (pyproject.toml not found)")


def ensure_src_paths(repo_root: Path) -> None:
    """Inject local src paths into sys.path for cross-repo imports."""
    src_path = repo_root / "src"
    workspace_root = repo_root.parent
    mcmc_src_path = workspace_root / "mcmc-internal" / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    if str(mcmc_src_path) not in sys.path and mcmc_src_path.exists():
        sys.path.insert(0, str(mcmc_src_path))


def _stable_payload(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def short_hash(payload: Dict[str, Any], prefix: str = "h", n: int = 12) -> str:
    """Create stable short hash ID from a config payload."""
    digest = hashlib.sha1(_stable_payload(payload).encode("utf-8")).hexdigest()
    return f"{prefix}{digest[:n]}"


def build_run_layout(
    repo_root: Path,
    dataset: str,
    data_id: str,
    run_id: str,
    sweep_mode: str,
) -> Dict[str, Path]:
    """Return run directories for estimations and reports, creating them if needed."""
    estimations_dir = repo_root / "estimations" / dataset / data_id / sweep_mode / run_id
    reports_dir = repo_root / "reports" / dataset / data_id / sweep_mode / run_id
    estimations_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    for name in ("diagnostics", "tables", "manifests"):
        (reports_dir / name).mkdir(parents=True, exist_ok=True)
    return {
        "estimations_dir": estimations_dir,
        "reports_dir": reports_dir,
    }

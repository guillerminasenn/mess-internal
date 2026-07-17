"""Reusable parity checklist utilities for migrated experiments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def write_checklist(checks: List[Dict[str, object]], markdown_path: Path, json_path: Path, title: str) -> Dict[str, int]:
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(checks, handle, indent=2)

    total = len(checks)
    passed = sum(1 for item in checks if item.get("exists"))

    lines = [f"# {title}", "", f"- Passed: {passed}/{total}", ""]
    for item in checks:
        mark = "[x]" if item.get("exists") else "[ ]"
        lines.append(f"- {mark} {item['name']}")
        lines.append(f"  - expected: {item['expected_path']}")
        lines.append(f"  - note: {item.get('description', '')}")

    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"total": total, "passed": passed}

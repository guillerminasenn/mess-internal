"""Artifact registry helpers for phase-style experiment scripts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List


@dataclass
class Artifact:
    path: str
    kind: str
    description: str


class ArtifactRegistry:
    """Collect generated artifacts and persist a compact manifest."""

    def __init__(self) -> None:
        self.items: List[Artifact] = []

    def add(self, path: Path, kind: str, description: str) -> None:
        self.items.append(Artifact(path=str(path.resolve()), kind=kind, description=description))

    def write(self, manifests_dir: Path, stem: str) -> tuple[Path, Path]:
        manifests_dir.mkdir(parents=True, exist_ok=True)
        json_path = manifests_dir / f"{stem}.json"
        md_path = manifests_dir / f"{stem}.md"

        payload = [asdict(item) for item in self.items]
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

        lines = ["# Artifacts", ""]
        for item in self.items:
            lines.append(f"- {item.kind}: {item.path}")
            lines.append(f"  - {item.description}")
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return json_path, md_path

    def print_summary(self) -> None:
        print("\nGenerated artifacts:")
        for item in self.items:
            print(f"- [{item.kind}] {item.path}")
            print(f"  {item.description}")

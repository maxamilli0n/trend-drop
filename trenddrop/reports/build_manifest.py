# TD-AUTO: BEGIN build-manifest
from __future__ import annotations
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    out = Path("out")
    out.mkdir(parents=True, exist_ok=True)
    pdf = out / "weekly-report.pdf"
    csv = out / "weekly-report.csv"

    manifest: dict[str, object] = {
        "name": "TrendDrop Weekly Pack",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "artifacts": [],
    }
    if pdf.exists():
        manifest["artifacts"].append({
            "type": "pdf",
            "path": str(pdf),
            "hash": sha256_of(pdf),
        })
    if csv.exists():
        manifest["artifacts"].append({
            "type": "csv",
            "path": str(csv),
            "hash": sha256_of(csv),
        })

    with open(out / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("[build_manifest] wrote out/manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# TD-AUTO: END build-manifest



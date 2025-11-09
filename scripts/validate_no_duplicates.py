# TD-AUTO: BEGIN preflight
import sys, json, os, re, glob, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 1) Ensure we won't create duplicate workflows
workflows = list((ROOT / ".github" / "workflows").glob("*.yml"))
names = set()
dupes = []
for wf in workflows:
    name = wf.name
    if name in names:
        dupes.append(name)
    names.add(name)

# 2) Ensure we are not going to modify PDF template files
pdf_guard_paths = [
    ROOT / "trenddrop" / "reports" / "generate_reports.py",
    ROOT / "utils" / "report.py",
    ROOT / "fonts" / "DejaVuSans.ttf",
]
pdf_modified = [p for p in pdf_guard_paths if not p.exists()]

# 3) Check for existing functions to avoid collisions
function_dirs = [
    ROOT / "supabase" / "edge-functions",
    ROOT / "supabase" / "functions",
]
existing_funcs = set()
for d in function_dirs:
    if d.exists():
        for x in d.iterdir():
            if x.is_dir():
                existing_funcs.add(x.name)

# 4) Planned new names (must not already exist)
planned_funcs = {"stripe-webhook", "payhip-webhook", "report-links", "health-ping", "api-products", "api-leaders"}
collisions = planned_funcs & existing_funcs

# 5) Sanity: PDF output naming conventions still present
expected_outputs = [
    ROOT / "out" / "weekly-report.pdf",
    ROOT / "out" / "weekly-report.csv",
]
missing_outputs = [p.name for p in expected_outputs if not p.exists()]

errors = []
if dupes:
    errors.append(f"Duplicate workflows detected: {sorted(dupes)}")
if pdf_modified:
    errors.append(f"Missing core PDF files (cannot proceed): {list(map(str,pdf_modified))}")
if collisions:
    errors.append(f"Function name collisions: {sorted(collisions)}")
if missing_outputs:
    # Not fatal; warn only (first run may not have outputs)
    print(f"[WARN] Expected outputs not found yet: {missing_outputs}")

if errors:
    print("\n".join(errors))
    sys.exit(1)

print("OK: pre-flight checks passed.")
# TD-AUTO: END preflight



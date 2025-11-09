import os
import zipfile


OUT_DIR = "out"
ZIP_PATH = os.path.join(OUT_DIR, "weekly-pack.zip")


def _first_existing(pathnames: list[str]) -> str | None:
    for name in pathnames:
        full = os.path.join(OUT_DIR, name)
        if os.path.exists(full):
            return full
    return None


pdf_path = _first_existing(["weekly-report.pdf", "latest.pdf"])  # prefer weekly for Gumroad
csv_path = _first_existing(["latest.csv", "weekly-report.csv"])  # prefer latest for data

if not (pdf_path and csv_path):
    raise SystemExit(
        "Missing PDF/CSV. Run `python -m trenddrop.reports.generate_reports` first.\n"
        f"Looked for: {os.path.join(OUT_DIR, 'weekly-report.pdf')} or latest.pdf and "
        f"{os.path.join(OUT_DIR, 'latest.csv')} or weekly-report.csv"
    )

with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as z:
    # Normalize names inside the zip
    z.write(pdf_path, "weekly-report.pdf")
    z.write(csv_path, "latest.csv")

print("✅ Packaged Gumroad release:", ZIP_PATH)



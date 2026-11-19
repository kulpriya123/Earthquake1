
from pathlib import Path
import subprocess
import sys

# Project root directory
BASE_DIR = Path(__file__).resolve().parent

# Pipeline steps
PIPELINE_STEPS = [
    ("1. Data Ingestion", "src/ingest.py"),
    ("2. Data Cleaning", "src/clean_data.py"),
    ("3. Transformation, Aggregation and Joining", "src/transform_data.py"),
    ("4. Publication to Google Sheets", "src/publish.py"),
]

print("=" * 60)
print("EARTHQUAKE DATA PIPELINE")
print("=" * 60)

for step_name, script_path in PIPELINE_STEPS:

    script = BASE_DIR / script_path

    print(f"\nStarting: {step_name}")
    print("-" * 60)

    if not script.exists():
        print(f"ERROR: File not found: {script}")
        sys.exit(1)

    try:
        subprocess.run(
            [sys.executable, str(script)],
            cwd=BASE_DIR,
            check=True
        )

        print(f"Completed: {step_name}")

    except subprocess.CalledProcessError as error:
        print(f"\nPIPELINE FAILED: {step_name}")
        print(f"Exit code: {error.returncode}")
        sys.exit(error.returncode)

print("\n" + "=" * 60)
print("ALL PIPELINE STEPS COMPLETED SUCCESSFULLY!")
print("=" * 60)

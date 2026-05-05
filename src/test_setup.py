from pathlib import Path

project_root = Path(__file__).resolve().parents[1]

required_folders = [
    "data/raw",
    "data/documents",
    "data/processed",
    "sql",
    "src/ingestion",
    "src/database",
    "src/retrieval",
    "src/rag",
    "src/api",
    "src/utils",
    "app",
    "evaluation",
    "notebooks",
    "docs",
    "screenshots",
]

print("Project root:", project_root)
print("\nChecking project folders...\n")

for folder in required_folders:
    path = project_root / folder
    if path.exists():
        print(f"[OK] {folder}")
    else:
        print(f"[MISSING] {folder}")

print("\nSetup check completed.")
import os
import re
import json

ROOT_DIR = r"E:\NGO"
EXCLUDE_DIRS = {".git", ".next", "__pycache__", "node_modules", ".venv", "venv", ".idea", ".vscode"}

backend_usd_matches = []
frontend_usd_matches = []

keywords = [r"\bUSD\b", r"\busd\b", r"US Dollar", r"\b\$\b", r"currency", r"amount"]

for root, dirs, files in os.walk(ROOT_DIR):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for file in files:
        if file.endswith((".py", ".tsx", ".ts", ".jsx", ".js", ".json", ".md", ".env", ".sql")):
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, ROOT_DIR)
            
            # Skip test backup/json output files generated during test runs
            if file in ("db_inspection_report.json", "inspect_db.py"):
                continue

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                lines = content.splitlines()
                for line_no, line in enumerate(lines, 1):
                    # Look for USD specifically or currency defaults
                    if re.search(r"\bUSD\b|\busd\b|US Dollar|\$", line, re.IGNORECASE) or "currency" in line.lower():
                        match_info = {
                            "file": relpath,
                            "line_no": line_no,
                            "line": line.strip()
                        }
                        if relpath.startswith("backend"):
                            backend_usd_matches.append(match_info)
                        elif relpath.startswith("frontend"):
                            frontend_usd_matches.append(match_info)
            except Exception as e:
                pass

report = {
    "backend_matches_count": len(backend_usd_matches),
    "frontend_matches_count": len(frontend_usd_matches),
    "backend_matches": backend_usd_matches,
    "frontend_matches": frontend_usd_matches
}

with open(r"E:\NGO\code_search_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(f"Code search complete. Found {len(backend_usd_matches)} backend matches and {len(frontend_usd_matches)} frontend matches.")

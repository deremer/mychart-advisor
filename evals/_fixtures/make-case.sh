#!/usr/bin/env bash
# Seed the eval workspace (the current directory) with fictional fixture case A.
#   make-case.sh empty        nothing (an empty folder)
#   make-case.sh scaffolded   case folder created, PDFs dropped in, nothing ingested
#   make-case.sh ingested     scaffolded plus extraction scripts run
set -euo pipefail
state="${1:-ingested}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
fixture="$repo/tests/fixtures/case-a"
[[ "$state" == "empty" ]] && exit 0

cat > .facts.json <<'JSON'
{"PATIENT_LABEL": "Alex", "AGE": "61", "RELATIONSHIP": "spouse", "SETTING": "inpatient",
 "FACILITY": "Example General Hospital", "START_DATE": "2025-03-03", "REASON": "yellow eyes and very tired",
 "ATTENDING": "Dana Placeholder, MD", "PORTAL": "Epic MyChart"}
JSON
python3 "$repo/skills/case-setup/scripts/scaffold.py" --root . --facts .facts.json >/dev/null
rm .facts.json
python3 - "$fixture/expected.json" > .advisor/identifiers.txt <<'PY'
import json, sys
print("\n".join(json.load(open(sys.argv[1]))["identifiers"]))
PY
cp "$fixture/Test Results/"* "Test Results/"
cp "$fixture/Care Team Notes/"* "Care Team Notes/"
cp "$fixture/family-recap.md" .
[[ "$state" == "scaffolded" ]] && exit 0

python3 "$repo/skills/ingest-results/scripts/extract_results.py" >/dev/null
python3 "$repo/skills/ingest-results/scripts/extract_notes.py" >/dev/null

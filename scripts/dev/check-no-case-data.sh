#!/usr/bin/env bash
# Blocks real patient data from entering this repo.
#
# Usage:
#   scripts/dev/check-no-case-data.sh           check staged files (pre-commit)
#   scripts/dev/check-no-case-data.sh --all     check every tracked file (CI)
#
# Fails on:
#   - any path under docs/input/
#   - any PDF outside tests/fixtures/
#   - portal folder names or portal-style note file names outside tests/fixtures/
#   - any line of .case-denylist (a gitignored local file) found in the checked content
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
cd "$root"

mode="${1:-staged}"
if [[ "$mode" == "--all" ]]; then
  files="$(git ls-files)"
else
  files="$(git diff --cached --name-only --diff-filter=ACMR)"
fi

fail=0
report() { echo "BLOCKED: $1" >&2; fail=1; }

while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  case "$f" in
    docs/input/*) report "$f is real-case reference material and must never be committed." ;;
  esac
  if [[ "$f" != tests/fixtures/* ]]; then
    shopt -s nocasematch
    [[ "$f" == *.pdf ]] && report "$f is a PDF outside tests/fixtures/."
    [[ "$f" == *"Test Results/"* || "$f" == *"Care Team Notes/"* || "$f" == *"Other Records/"* ]] &&
      report "$f sits in a portal records folder outside tests/fixtures/."
    [[ "$(basename "$f")" =~ \ by\ .+\ at\ [0-9]{1,2}[-:/][0-9]{1,2}[-:/][0-9]{4} ]] &&
      report "$f looks like a portal note export."
    [[ "$f" == .advisor/* || "$f" == */.advisor/* ]] && [[ "$f" != tests/fixtures/* ]] &&
      report "$f is a case identifiers file."
    shopt -u nocasematch
  fi
done <<< "$files"

if [[ -f .case-denylist ]]; then
  while IFS= read -r term; do
    term="${term%%#*}"
    term="$(echo "$term" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    [[ -z "$term" ]] && continue
    while IFS= read -r f; do
      [[ -z "$f" || ! -f "$f" ]] && continue
      if [[ "$mode" == "--all" ]]; then
        content="$(cat "$f")"
      else
        content="$(git show ":$f" 2>/dev/null || true)"
      fi
      if grep -qiF -- "$term" <<< "$content" || grep -qiF -- "$term" <<< "$f"; then
        report "$f matches a .case-denylist term (term not printed)."
      fi
    done <<< "$files"
  done < .case-denylist
fi

if [[ "$fail" -ne 0 ]]; then
  echo "Commit blocked by scripts/dev/check-no-case-data.sh. See AGENTS.md, section 'No real case data'." >&2
  exit 1
fi
echo "check-no-case-data: clean"

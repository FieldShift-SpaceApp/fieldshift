#!/usr/bin/env bash
# scripts/check-public-repo.sh — NFR9 / ADR-5: fails if anything from the private workspace enters the public repo.
# AGENTS.md and CLAUDE.md (team AI protocol) are allowed; agent tool folders are not.
set -euo pipefail
bad=$(git ls-files | grep -E '(^|/)(\.aiox-core|\.aiox|squads|\.claude|\.codex|\.gemini|\.cursor|\.agents?|\.antigravity|\.grok|\.kimi)/|(^|/)pro-(installed-manifest\.yaml|version\.json)$|(^|/)\.env(\..+)?$' \
  | grep -v -E '(^|/)\.env\.example$' || true)
if [ -n "$bad" ]; then
  echo "NFR9: forbidden files in the public repository:"; echo "$bad"; exit 1
fi
echo "NFR9 ok: no forbidden paths"

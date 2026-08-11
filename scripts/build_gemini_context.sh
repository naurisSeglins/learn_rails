#!/usr/bin/env bash
# Concatenates every markdown doc that matters for this project into one file,
# so it can be pasted into Gemini (or any assistant without repo access) to
# close the context gap with an assistant that can read the repo directly.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output="$repo_root/gemini_context.md"

# Read first, in this order: behavioral rules (how any assistant should work
# here), then project status/architecture, then everything else alphabetically.
priority_files=(
  "$(dirname "$repo_root")/CLAUDE.md"
  "$repo_root/CLAUDE.md"
  "$repo_root/GLOBAL_CLAUDE_BACKUP.md"
  "$repo_root/TASKS.md"
  "$repo_root/docs/architecture.md"
  "$repo_root/exercises.md"
  "$repo_root/books.md"
)

is_priority_file() {
  local candidate="$1"
  for pf in "${priority_files[@]}"; do
    [[ "$candidate" == "$pf" ]] && return 0
  done
  return 1
}

write_file_block() {
  local f="$1"
  local rel="${f#"$repo_root"/}"
  echo "================================================================================"
  echo "FILE: $rel"
  echo "================================================================================"
  cat "$f"
  echo
}

{
  echo "# Context bundle for an assistant without repo access — generated $(date '+%Y-%m-%d %H:%M')"
  echo "Paste this whole file in before asking about this project — it's the same docs Claude Code reads directly from disk."
  echo

  for f in "${priority_files[@]}"; do
    [[ -f "$f" ]] && write_file_block "$f"
  done

  while IFS= read -r f; do
    is_priority_file "$f" && continue
    write_file_block "$f"
  done < <(find "$repo_root" \
    -type f -name "*.md" \
    -not -path "*/.venv/*" \
    -not -path "*/.git/*" \
    -not -path "*/.pytest_cache/*" \
    -not -path "*/.ruff_cache/*" \
    -not -path "*/__pycache__/*" \
    -not -path "$output" \
    | sort)
} > "$output"

echo "Wrote $(wc -l < "$output" | tr -d ' ') lines to $output"

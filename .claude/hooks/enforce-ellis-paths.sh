#!/bin/bash
# Per-agent path enforcement: Ellis
# PreToolUse hook on Write|Edit|MultiEdit -- Ellis can only write to commit/changelog targets
set -uo pipefail
[ "${ATELIER_SETUP_MODE:-}" = "1" ] && exit 0
[ -f "${CLAUDE_PROJECT_DIR:-.}/docs/pipeline/.setup-mode" ] && exit 0

INPUT=$(cat)
if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required for atelier-pipeline hooks. Install: brew install jq" >&2
  exit 2
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
case "$TOOL_NAME" in Write|Edit|MultiEdit) ;; *) exit 0 ;; esac

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
[ -z "$FILE_PATH" ] && exit 0

# Normalize absolute paths to project-relative
PROJECT_ROOT="${CURSOR_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-.}}"
FILE_PATH="${FILE_PATH#"$PROJECT_ROOT"/}"

# If still absolute after normalization, it's outside the project root
if [[ "$FILE_PATH" == /* ]]; then
  echo "BLOCKED: File is outside the project root. Attempted: $FILE_PATH" >&2
  exit 2
fi

# Reject path traversal
[[ "$FILE_PATH" == *..* ]] && { echo "BLOCKED: Path traversal detected in $FILE_PATH" >&2; exit 2; }

# Ellis allowlist: changelog, git config files, and CI/CD/infra paths
case "$FILE_PATH" in
  CHANGELOG.md)          exit 0 ;;
  .gitignore)            exit 0 ;;
  .gitattributes)        exit 0 ;;
  .gitmodules)           exit 0 ;;
  .github/*)             exit 0 ;;
  .gitlab-ci.yml)        exit 0 ;;
  .gitlab-ci/*)          exit 0 ;;
  .gitlab/*)             exit 0 ;;
  .circleci/*)           exit 0 ;;
  Jenkinsfile*)          exit 0 ;;
  Dockerfile*)           exit 0 ;;
  docker-compose*)       exit 0 ;;
  deploy/*)              exit 0 ;;
  infra/*)               exit 0 ;;
  terraform/*)           exit 0 ;;
  pulumi/*)              exit 0 ;;
  k8s/*)                 exit 0 ;;
  kubernetes/*)          exit 0 ;;
esac

echo "BLOCKED: Ellis can only write to CHANGELOG.md, git config files (.gitignore, .gitattributes, .gitmodules), and CI/CD paths (.github/, .gitlab*, .circleci/, Jenkinsfile*, Dockerfile*, docker-compose*, deploy/, infra/, terraform/, pulumi/, k8s/, kubernetes/). Attempted: $FILE_PATH" >&2
exit 2

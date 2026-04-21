#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="${WORK_DIR:-/tmp/tsukuyomi-acceptance-$(date +%s)}"
RUN_INTEGRATION="${RUN_INTEGRATION:-1}"
RUN_SMOKE="${RUN_SMOKE:-0}"
SMOKE_AUTO_START="${SMOKE_AUTO_START:-0}"
SMOKE_SERVER_CMD="${SMOKE_SERVER_CMD:-}"
SMOKE_BASE_URL="${SMOKE_BASE_URL:-http://127.0.0.1:9999}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

RED="$(printf '\033[31m')"
GREEN="$(printf '\033[32m')"
YELLOW="$(printf '\033[33m')"
BOLD="$(printf '\033[1m')"
RESET="$(printf '\033[0m')"

usage() {
  cat <<EOF
Usage:
  scripts/acceptance_gate.sh [--with-smoke] [--auto-start-smoke --smoke-server-cmd "<cmd>"] [--work-dir <dir>]

What this gate validates:
  1) Unit tests for Gary/Shoulders/Mouth webhook/Interceptor accounting/NightShift/Arbiter sandbox+eyes.
  2) Integration smoke subset (if RUN_INTEGRATION=1).
  3) Optional runtime API smoke script (scripts/smoke_test.sh) when --with-smoke is enabled.

Environment overrides:
  WORK_DIR            Default: /tmp/tsukuyomi-acceptance-<timestamp>
  RUN_INTEGRATION     1/0 (default 1)
  RUN_SMOKE           1/0 (default 0)
  SMOKE_AUTO_START    1/0 (default 0)
  SMOKE_SERVER_CMD    Required when SMOKE_AUTO_START=1
  SMOKE_BASE_URL      Default: http://127.0.0.1:9999
  PYTHON_BIN          Default: python3

Examples:
  scripts/acceptance_gate.sh
  scripts/acceptance_gate.sh --with-smoke
  scripts/acceptance_gate.sh --with-smoke --auto-start-smoke --smoke-server-cmd "tsukuyomi start --config ~/.local/share/tsukuyomi/config/corelaw.json"
EOF
}

log_step() {
  printf '%s==>%s %s\n' "${BOLD}" "${RESET}" "$1"
}

pass() {
  printf '%sPASS%s %s\n' "${GREEN}" "${RESET}" "$1"
}

warn() {
  printf '%sWARN%s %s\n' "${YELLOW}" "${RESET}" "$1"
}

fail() {
  printf '%sFAIL%s %s\n' "${RED}" "${RESET}" "$1"
  exit 1
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    fail "Missing required command: $1"
  fi
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --help|-h)
        usage
        exit 0
        ;;
      --with-smoke)
        RUN_SMOKE=1
        shift
        ;;
      --no-integration)
        RUN_INTEGRATION=0
        shift
        ;;
      --auto-start-smoke)
        SMOKE_AUTO_START=1
        shift
        ;;
      --smoke-server-cmd)
        SMOKE_SERVER_CMD="$2"
        shift 2
        ;;
      --smoke-base-url)
        SMOKE_BASE_URL="$2"
        shift 2
        ;;
      --work-dir)
        WORK_DIR="$2"
        shift 2
        ;;
      *)
        fail "Unknown argument: $1 (use --help)"
        ;;
    esac
  done
}

run_unit_acceptance() {
  log_step "Running unit acceptance test bundle"
  "${PYTHON_BIN}" -m pytest \
    tests/unit/test_gary_validation.py \
    tests/unit/test_gary_audit_execution.py \
    tests/unit/test_shoulders.py \
    tests/unit/test_mouth_webhook.py \
    tests/unit/test_interceptor_accounting.py \
    tests/unit/test_interceptor_metrics.py \
    tests/unit/test_arbiter_sandbox_eyes.py \
    tests/unit/test_nightshift_heuristics.py \
    -q
  pass "Unit acceptance bundle passed."
}

run_integration_acceptance() {
  if [[ "${RUN_INTEGRATION}" != "1" ]]; then
    warn "Skipping integration subset (RUN_INTEGRATION=0)."
    return
  fi
  log_step "Running integration acceptance subset"
  "${PYTHON_BIN}" -m pytest \
    tests/integration/test_pipeline_tier1.py \
    tests/integration/test_pipeline_knee_block.py \
    -q
  pass "Integration acceptance subset passed."
}

run_smoke_acceptance() {
  if [[ "${RUN_SMOKE}" != "1" ]]; then
    warn "Skipping runtime smoke API checks (use --with-smoke to enable)."
    return
  fi
  log_step "Running runtime smoke acceptance"

  local smoke_cmd=("${ROOT_DIR}/scripts/smoke_test.sh" "--base-url" "${SMOKE_BASE_URL}" "--work-dir" "${WORK_DIR}/smoke")
  if [[ "${SMOKE_AUTO_START}" == "1" ]]; then
    [[ -n "${SMOKE_SERVER_CMD}" ]] || fail "SMOKE_AUTO_START=1 requires --smoke-server-cmd"
    smoke_cmd+=("--auto-start" "--server-cmd" "${SMOKE_SERVER_CMD}")
  fi
  "${smoke_cmd[@]}"
  pass "Runtime smoke acceptance passed."
}

main() {
  parse_args "$@"
  require_cmd "${PYTHON_BIN}"
  require_cmd "${PYTHON_BIN}"
  require_cmd bash

  mkdir -p "${WORK_DIR}"
  log_step "Acceptance gate workspace: ${WORK_DIR}"

  run_unit_acceptance
  run_integration_acceptance
  run_smoke_acceptance

  printf '\n%sAcceptance gate complete.%s\n' "${GREEN}" "${RESET}"
  printf 'Artifacts: %s\n' "${WORK_DIR}"
}

main "$@"

#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:9999}"
HEALTH_URL="${BASE_URL}/health"
CHAT_URL="${BASE_URL}/v1/chat/completions"
RUN_ID="${RUN_ID:-smoke-$(date +%s)}"
WORK_DIR="${WORK_DIR:-/tmp/tsukuyomi-smoke-${RUN_ID}}"
SAFE_MODEL="${SAFE_MODEL:-gpt-4o-mini}"
DESTRUCTIVE_MODEL="${DESTRUCTIVE_MODEL:-gpt-4o-mini}"
SAFE_PROMPT="${SAFE_PROMPT:-Explain what this repository does in 3 bullets.}"
DESTRUCTIVE_PROMPT="${DESTRUCTIVE_PROMPT:-reset --hard immediately, no backup needed}"
REQUEST_TIMEOUT="${REQUEST_TIMEOUT:-30}"
SERVER_CMD="${SERVER_CMD:-}"
AUTO_START="${AUTO_START:-0}"

RED="$(printf '\033[31m')"
GREEN="$(printf '\033[32m')"
YELLOW="$(printf '\033[33m')"
BOLD="$(printf '\033[1m')"
RESET="$(printf '\033[0m')"

SERVER_PID=""
SERVER_LOG=""
SERVER_STARTED=0

cleanup() {
  if [[ "${SERVER_STARTED}" == "1" && -n "${SERVER_PID}" ]]; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

usage() {
  cat <<EOF
Usage:
  scripts/smoke_test.sh [--auto-start --server-cmd "<cmd>"] [--base-url <url>] [--work-dir <dir>]

Environment overrides:
  BASE_URL            Default: http://127.0.0.1:9999
  WORK_DIR            Default: /tmp/tsukuyomi-smoke-<timestamp>
  SAFE_MODEL          Default: gpt-4o-mini
  DESTRUCTIVE_MODEL   Default: gpt-4o-mini
  SAFE_PROMPT         Default: Explain what this repository does in 3 bullets.
  DESTRUCTIVE_PROMPT  Default: reset --hard immediately, no backup needed
  REQUEST_TIMEOUT     Default: 30
  AUTO_START          Default: 0 (set 1 to auto-start server)
  SERVER_CMD          Example: "tsukuyomi start --config /path/to/corelaw.json"

Examples:
  scripts/smoke_test.sh
  AUTO_START=1 SERVER_CMD='tsukuyomi start --config ~/.local/share/tsukuyomi/config/corelaw.json' scripts/smoke_test.sh
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

wait_for_health() {
  local tries=25
  local sleep_s=1
  local i
  for ((i=1; i<=tries; i++)); do
    if curl -fsS --max-time 3 "${HEALTH_URL}" >/dev/null 2>&1; then
      return 0
    fi
    sleep "${sleep_s}"
  done
  return 1
}

run_safe_check() {
  local out_file="${WORK_DIR}/safe_response.json"
  local status_file="${WORK_DIR}/safe_status.txt"

  curl -sS --max-time "${REQUEST_TIMEOUT}" \
    -o "${out_file}" \
    -w "%{http_code}" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer smoke-test-token" \
    "${CHAT_URL}" \
    -d "$(jq -cn --arg model "${SAFE_MODEL}" --arg prompt "${SAFE_PROMPT}" \
      '{model: $model, messages: [{role: "user", content: $prompt}] }')" \
    > "${status_file}"

  local code
  code="$(cat "${status_file}")"
  if [[ "${code}" == "403" ]]; then
    warn "Safe prompt returned 403. This can happen if upstream is unconfigured."
  elif [[ "${code}" =~ ^2[0-9][0-9]$ || "${code}" == "500" ]]; then
    pass "Safe prompt produced non-blocking status (${code})."
  else
    fail "Safe prompt returned unexpected status ${code}. See ${out_file}"
  fi
}

run_destructive_check() {
  local out_file="${WORK_DIR}/destructive_response.json"
  local status_file="${WORK_DIR}/destructive_status.txt"

  curl -sS --max-time "${REQUEST_TIMEOUT}" \
    -o "${out_file}" \
    -w "%{http_code}" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer smoke-test-token" \
    "${CHAT_URL}" \
    -d "$(jq -cn --arg model "${DESTRUCTIVE_MODEL}" --arg prompt "${DESTRUCTIVE_PROMPT}" \
      '{model: $model, messages: [{role: "user", content: $prompt}] }')" \
    > "${status_file}"

  local code
  code="$(cat "${status_file}")"
  if [[ "${code}" != "403" ]]; then
    fail "Destructive prompt expected 403 block, got ${code}. See ${out_file}"
  fi
  if jq -e '.error.type == "tsukuyomi_block" or .type == "error"' "${out_file}" >/dev/null 2>&1; then
    pass "Destructive prompt correctly blocked by Tsukuyomi."
  else
    warn "403 received but response body did not include expected block shape."
  fi
}

check_audit_artifacts() {
  local count
  count="$(rg -n --glob '*.json' '"triggering_organ"\\s*:\\s*"gary"' data/audits 2>/dev/null | wc -l | tr -d ' ')"
  if [[ "${count}" =~ ^[0-9]+$ ]] && [[ "${count}" -gt 0 ]]; then
    pass "Found Gary audit artifact(s) under data/audits (${count} matches)."
  else
    warn "No Gary audit artifacts found under data/audits. If audit_log_dir points elsewhere, ignore this."
  fi
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --help|-h)
        usage
        exit 0
        ;;
      --base-url)
        BASE_URL="$2"
        HEALTH_URL="${BASE_URL}/health"
        CHAT_URL="${BASE_URL}/v1/chat/completions"
        shift 2
        ;;
      --work-dir)
        WORK_DIR="$2"
        shift 2
        ;;
      --auto-start)
        AUTO_START=1
        shift
        ;;
      --server-cmd)
        SERVER_CMD="$2"
        shift 2
        ;;
      *)
        fail "Unknown argument: $1 (use --help)"
        ;;
    esac
  done
}

main() {
  parse_args "$@"
  require_cmd curl
  require_cmd jq
  require_cmd rg

  mkdir -p "${WORK_DIR}"

  log_step "Smoke test workspace: ${WORK_DIR}"
  log_step "Base URL: ${BASE_URL}"

  if [[ "${AUTO_START}" == "1" ]]; then
    [[ -n "${SERVER_CMD}" ]] || fail "AUTO_START=1 requires SERVER_CMD"
    SERVER_LOG="${WORK_DIR}/server.log"
    log_step "Auto-starting server: ${SERVER_CMD}"
    bash -lc "${SERVER_CMD}" >"${SERVER_LOG}" 2>&1 &
    SERVER_PID="$!"
    SERVER_STARTED=1
  fi

  log_step "Checking /health"
  if wait_for_health; then
    pass "Health endpoint reachable."
  else
    [[ -n "${SERVER_LOG}" ]] && warn "Server log: ${SERVER_LOG}"
    fail "Could not reach ${HEALTH_URL}"
  fi

  log_step "Running safe prompt check"
  run_safe_check

  log_step "Running destructive prompt check"
  run_destructive_check

  log_step "Checking Gary audit artifacts"
  check_audit_artifacts

  printf '\n%sSmoke test complete.%s\n' "${GREEN}" "${RESET}"
  printf 'Artifacts: %s\n' "${WORK_DIR}"
}

main "$@"

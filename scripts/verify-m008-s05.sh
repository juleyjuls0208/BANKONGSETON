#!/usr/bin/env bash
# M008/S05 one-command integration verifier.
# Chains S01 → S02 → S03 → S04 verifiers to prove the full login→home→transactions→budget→settings
# rollback flow is coherent with no QR regressions.
# Each phase reports independently; script exits 0 only if all phases pass.

set -euo pipefail

SCRIPT_NAME="verify-m008-s05"

S01_VERIFIER="scripts/verify-m008-s01.sh"
S02_VERIFIER="scripts/verify-m008-s02.sh"
S03_VERIFIER="scripts/verify-m008-s03.sh"
S04_VERIFIER="scripts/verify-m008-s04.sh"

# Windows Git Bash short-path fallback (avoids os error 123 from quoted long paths in some runners)
WINDOWS_GIT_BASH_EXE_SHORT="C:/Progra~1/Git/bin/bash.exe"

log() {
  echo "[${SCRIPT_NAME}] $*"
}

fail_with_guidance() {
  local phase="$1"
  local code="$2"
  shift 2

  log "phase=${phase} status=failed exit_code=${code}"
  for line in "$@"; do
    log "guidance=${line}"
  done
  exit "${code}"
}

require_file() {
  local file="$1"

  if [[ ! -f "${file}" ]]; then
    fail_with_guidance "preflight" 2 \
      "Required file is missing: ${file}" \
      "Restore/create the missing artifact, then re-run: rtk proxy ${WINDOWS_GIT_BASH_EXE_SHORT} scripts/verify-m008-s05.sh"
  fi
}

run_phase() {
  local phase="$1"
  local command_label="$2"
  local guidance_1="$3"
  local guidance_2="$4"
  shift 4

  if [[ "${1:-}" != "--" ]]; then
    fail_with_guidance "preflight" 2 \
      "run_phase invocation is missing '--' delimiter for command arguments" \
      "Fix script wiring and re-run: rtk proxy ${WINDOWS_GIT_BASH_EXE_SHORT} scripts/verify-m008-s05.sh"
  fi
  shift

  log "phase=${phase} status=running"

  set +e
  "$@"
  local code=$?
  set -e

  if [[ ${code} -ne 0 ]]; then
    fail_with_guidance "${phase}" "${code}" \
      "Command failed: ${command_label}" \
      "${guidance_1}" \
      "${guidance_2}"
  fi

  log "phase=${phase} status=passed"
}

run_chained_verifier() {
  local verifier="$1"

  # Prefer the short-path Git Bash exe on Windows to avoid os error 123.
  if [[ -x "${WINDOWS_GIT_BASH_EXE_SHORT}" ]]; then
    rtk proxy "${WINDOWS_GIT_BASH_EXE_SHORT}" "${verifier}"
    return
  fi

  # Fallback to bare bash (may fail on Windows if /bin/bash is unavailable).
  rtk proxy bash "${verifier}"
}

run_preflight() {
  log "phase=preflight status=running"

  require_file "${S01_VERIFIER}"
  require_file "${S02_VERIFIER}"
  require_file "${S03_VERIFIER}"
  require_file "${S04_VERIFIER}"

  log "phase=preflight status=passed"
}

main() {
  log "status=starting"

  run_preflight

  # S01: budget contract (backend + iOS endpoint/payload + retry-visibility continuity).
  run_phase "s01-budget-contract" \
    "rtk proxy ${WINDOWS_GIT_BASH_EXE_SHORT} ${S01_VERIFIER}" \
    "S01 budget contract failed (backend budget route, iOS endpoint/payload markers, or retry-visibility continuity regressed)." \
    "Run ${S01_VERIFIER} directly for guidance, fix the failing phase, then re-run S05." \
    -- run_chained_verifier "${S01_VERIFIER}"

  # S02: native TabView rollback + budget/QR/login regression guards.
  run_phase "s02-tabview-rollback" \
    "rtk proxy ${WINDOWS_GIT_BASH_EXE_SHORT} ${S02_VERIFIER}" \
    "S02 tab-view rollback contract failed, or budget/QR/login regression guard regressed." \
    "Run ${S02_VERIFIER} directly for guidance, fix the failing phase, then re-run S05." \
    -- run_chained_verifier "${S02_VERIFIER}"

  # S03: Home rollback + QR continuity + S02 regression chain.
  run_phase "s03-home-qr-rollback" \
    "rtk proxy ${WINDOWS_GIT_BASH_EXE_SHORT} ${S03_VERIFIER}" \
    "S03 Home rollback contract failed, QR continuity seam regressed, or S02 regression chain failed." \
    "Run ${S03_VERIFIER} directly for guidance, fix the failing phase, then re-run S05." \
    -- run_chained_verifier "${S03_VERIFIER}"

  # S04: transactions/settings rollback + S03 regression chain (which chains S02→S01).
  run_phase "s04-transactions-settings-rollback" \
    "rtk proxy ${WINDOWS_GIT_BASH_EXE_SHORT} ${S04_VERIFIER}" \
    "S04 transactions/settings rollback contract failed, or S03 regression chain (Home/QR/S02/S01) regressed." \
    "Run ${S04_VERIFIER} directly for guidance, fix the failing phase, then re-run S05." \
    -- run_chained_verifier "${S04_VERIFIER}"

  log "status=passed"
}

main "$@"

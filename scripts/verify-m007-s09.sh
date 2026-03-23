#!/usr/bin/env bash
# M007/S09 phased runtime verifier.
# Executes Apple-host runtime checks and emits structured runtime proof artifacts.

set -euo pipefail

SCRIPT_NAME="verify-m007-s09"

S07_VERIFIER="scripts/verify-m007-s07.sh"
RUNTIME_WRITER="scripts/verify-m007-s09-runtime.py"
RUNTIME_PROOF_JSON=".gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json"
RUNTIME_PROOF_MD=".gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md"

IOS_PROJECT="mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj"
IOS_SCHEME="BankongSetonStudent"
IOS_DESTINATION="platform=iOS Simulator,name=iPhone 15"

log() {
  echo "[${SCRIPT_NAME}] $*"
}

utc_now() {
  rtk proxy python -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z'))"
}

record_phase() {
  local phase="$1"
  local status="$2"
  local command="$3"
  local exit_code="$4"
  local started_at="$5"
  local finished_at="$6"
  shift 6

  local guidance_args=()
  for line in "$@"; do
    guidance_args+=(--guidance "$line")
  done

  set +e
  rtk proxy python "${RUNTIME_WRITER}" \
    --proof-json "${RUNTIME_PROOF_JSON}" \
    --proof-md "${RUNTIME_PROOF_MD}" \
    --phase-id "${phase}" \
    --status "${status}" \
    --command "${command}" \
    --exit-code "${exit_code}" \
    --started-at "${started_at}" \
    --finished-at "${finished_at}" \
    "${guidance_args[@]}"
  local code=$?
  set -e

  if [[ ${code} -ne 0 ]]; then
    log "phase=${phase} status=warning runtime_proof_write_failed=${code}"
  fi
}

fail_with_guidance() {
  local phase="$1"
  local code="$2"
  local command="$3"
  local started_at="$4"
  shift 4

  local finished_at
  finished_at="$(utc_now)"

  log "phase=${phase} status=failed exit_code=${code}"
  for line in "$@"; do
    log "guidance=${line}"
  done

  record_phase "${phase}" "fail" "${command}" "${code}" "${started_at}" "${finished_at}" "$@"
  exit "${code}"
}

require_file() {
  local file="$1"

  if [[ ! -f "${file}" ]]; then
    local started_at
    started_at="$(utc_now)"
    fail_with_guidance "preflight" 2 "test -f ${file}" "${started_at}" \
      "Required file is missing: ${file}" \
      "Restore/create the missing artifact, then re-run: rtk proxy sh scripts/verify-m007-s09.sh"
  fi
}

require_path() {
  local path="$1"

  if [[ ! -e "${path}" ]]; then
    local started_at
    started_at="$(utc_now)"
    fail_with_guidance "preflight" 2 "test -e ${path}" "${started_at}" \
      "Required path is missing: ${path}" \
      "Restore the missing project path, then re-run: rtk proxy sh scripts/verify-m007-s09.sh"
  fi
}

run_phase() {
  local phase="$1"
  local command_label="$2"
  local guidance_1="$3"
  local guidance_2="$4"
  shift 4

  if [[ "${1:-}" != "--" ]]; then
    local started_at
    started_at="$(utc_now)"
    fail_with_guidance "preflight" 2 "run_phase ${phase}" "${started_at}" \
      "run_phase invocation is missing '--' delimiter for command arguments" \
      "Fix script wiring and re-run verifier."
  fi
  shift

  local started_at
  started_at="$(utc_now)"

  log "phase=${phase} status=running"
  set +e
  "$@"
  local code=$?
  set -e

  local finished_at
  finished_at="$(utc_now)"

  if [[ ${code} -ne 0 ]]; then
    fail_with_guidance "${phase}" "${code}" "${command_label}" "${started_at}" \
      "${guidance_1}" \
      "${guidance_2}"
  fi

  record_phase "${phase}" "pass" "${command_label}" "${code}" "${started_at}" "${finished_at}" \
    "phase ${phase} completed successfully"
  log "phase=${phase} status=passed"
}

check_apple_tooling() {
  rtk proxy xcodebuild -version
  rtk proxy xcrun --version
}

run_simulator_build() {
  rtk proxy xcodebuild \
    -project "${IOS_PROJECT}" \
    -scheme "${IOS_SCHEME}" \
    -destination "${IOS_DESTINATION}" \
    build
}

run_xctrace_templates() {
  rtk proxy xcrun xctrace list templates
}

verify_artifact_completeness() {
  rtk proxy python -c "import json; from pathlib import Path; p=Path('${RUNTIME_PROOF_JSON}'); md=Path('${RUNTIME_PROOF_MD}'); assert p.exists() and p.stat().st_size>0, 'missing runtime proof json'; assert md.exists() and md.stat().st_size>0, 'missing runtime proof md'; data=json.loads(p.read_text(encoding='utf-8')); required={'s07_baseline','apple_tooling','simulator_build','xctrace_templates'}; ids={phase['id'] for phase in data.get('phases', [])}; missing=sorted(required-ids); assert not missing, missing"
}

main() {
  log "status=starting"

  require_file "${S07_VERIFIER}"
  require_file "${RUNTIME_WRITER}"
  require_path "${IOS_PROJECT}"

  log "phase=s07_baseline status=queued"
  run_phase "s07_baseline" "rtk proxy sh scripts/verify-m007-s07.sh" \
    "S07 baseline gate failed; fix integration/scope regressions before S09 runtime closure." \
    "Re-run baseline directly: rtk proxy sh scripts/verify-m007-s07.sh" \
    -- rtk proxy sh "${S07_VERIFIER}"

  log "phase=apple_tooling status=queued"
  run_phase "apple_tooling" "xcodebuild -version && xcrun --version" \
    "Apple tooling is unavailable in PATH (xcodebuild/xcrun check failed)." \
    "Run on an Apple-capable host with Xcode CLI tools installed (xcode-select --install)." \
    -- check_apple_tooling

  log "phase=simulator_build status=queued"
  run_phase "simulator_build" "xcodebuild -project ${IOS_PROJECT} -scheme ${IOS_SCHEME} -destination '${IOS_DESTINATION}' build" \
    "Simulator build failed for BankongSetonStudent." \
    "Inspect xcodebuild output and fix compile/signing/toolchain issues before retrying." \
    -- run_simulator_build

  log "phase=xctrace_templates status=queued"
  run_phase "xctrace_templates" "xcrun xctrace list templates" \
    "xctrace template discovery failed." \
    "Ensure xcrun/xctrace are installed and accepted license/toolchain setup is complete." \
    -- run_xctrace_templates

  log "phase=artifact_completeness status=queued"
  run_phase "artifact_completeness" "runtime proof artifact completeness assertion" \
    "Runtime proof artifacts are missing required files or phase IDs." \
    "Re-run verifier and inspect ${RUNTIME_PROOF_JSON} for phase coverage diagnostics." \
    -- verify_artifact_completeness

  log "status=passed"
}

main "$@"

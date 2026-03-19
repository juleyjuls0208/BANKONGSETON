#!/usr/bin/env bash
# M006/S04 one-command verifier:
# 1) route regression guardrails
# 2) live-proof verifier execution
# 3) markdown evidence rendering from JSON artifact

set -euo pipefail

BASE_URL="${VERIFY_S04_BASE_URL:-http://127.0.0.1:5010}"
EVIDENCE_JSON="${VERIFY_S04_EVIDENCE_JSON:-.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json}"
EVIDENCE_MD="${VERIFY_S04_EVIDENCE_MD:-.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.md}"
EVIDENCE_SCHEMA="${VERIFY_S04_EVIDENCE_SCHEMA:-.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.schema.json}"

LIVE_FLAGS=()
if [[ "${1:-}" == "--dry-run-preflight" ]]; then
  LIVE_FLAGS+=("--dry-run-preflight")
fi

log() {
  echo "[verify-m006-s04] $*"
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

log "phase=regression status=running"
rtk proxy python -m pytest -q \
  tests/test_cashier_app_pos_route.py \
  tests/test_cashier_app_payment_routes.py \
  tests/test_cashier_app_arduino_routes.py
log "phase=regression status=passed"

log "phase=live-proof status=running base_url=${BASE_URL}"
set +e
rtk proxy python scripts/verify-m006-s04-live.py \
  --base-url "${BASE_URL}" \
  --evidence "${EVIDENCE_JSON}" \
  "${LIVE_FLAGS[@]}"
LIVE_EXIT=$?
set -e
if [[ ${LIVE_EXIT} -eq 0 ]]; then
  log "phase=live-proof status=passed"
else
  log "phase=live-proof status=failed exit_code=${LIVE_EXIT}"
fi

log "phase=evidence status=running output=${EVIDENCE_MD}"
rtk proxy python scripts/render-m006-s04-proof-md.py \
  --evidence-json "${EVIDENCE_JSON}" \
  --output-md "${EVIDENCE_MD}" \
  --schema "${EVIDENCE_SCHEMA}" \
  --base-url "${BASE_URL}"
log "phase=evidence status=passed"

if [[ ${LIVE_EXIT} -ne 0 ]]; then
  fail_with_guidance "live-proof" "${LIVE_EXIT}" \
    "Run with --dry-run-preflight to inspect readiness without endpoint execution." \
    "Inspect ${EVIDENCE_JSON} preflight/errors and required_phase_results to locate the failure stage." \
    "Use ${EVIDENCE_MD} for a concise operator summary."
fi

log "status=passed"
log "artifacts=${EVIDENCE_JSON},${EVIDENCE_MD}"

#!/usr/bin/env python
"""Render human-readable S04 live proof markdown from JSON evidence."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render S04 live proof markdown summary")
    parser.add_argument("--evidence-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:5010")
    return parser.parse_args()


def render_summary(data: Dict[str, Any], json_path: Path, md_path: Path, schema_path: Path, base_url: str) -> str:
    overall = data.get("overall", {}) or {}
    preflight = data.get("preflight", {}) or {}
    phases = data.get("phases", []) or []

    phase_map = {p.get("phase"): p for p in phases if isinstance(p, dict)}
    required_map = overall.get("required_phase_results", {}) or {}

    live_count = int(overall.get("live_success_count", 0) or 0)
    offline_count = int(overall.get("offline_fallback_count", 0) or 0)
    failed_count = int(overall.get("failed_count", 0) or 0)

    if phases and (live_count + offline_count + failed_count == 0):
        for p in phases:
            c = p.get("classification")
            if c == "live_success":
                live_count += 1
            elif c == "offline_fallback":
                offline_count += 1
            else:
                failed_count += 1

    live_ready = bool(overall.get("live_ready"))
    schema_valid = bool(overall.get("schema_valid"))
    dry_run = bool(overall.get("dry_run_preflight"))

    generated_at = data.get("generated_at", "unknown")
    summary_generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    canonical_to_endpoint = {
        "products": "/api/products",
        "rfid_complete_sale": "/api/complete-sale",
        "qr_confirm": "/api/qr/confirm",
        "nfc_complete_sale": "/api/complete-sale-nfc",
    }

    lines = []
    lines.append("# S04 Live Runtime Proof Summary")
    lines.append("")
    lines.append("## Run Metadata")
    lines.append("")
    lines.append(f"- Summary generated at: `{summary_generated_at}`")
    lines.append(f"- Evidence generated at: `{generated_at}`")
    lines.append(f"- Base URL: `{data.get('base_url', base_url)}`")
    lines.append(f"- Wrapper command: `rtk proxy bash scripts/verify-m006-s04.sh{' --dry-run-preflight' if dry_run else ''}`")
    lines.append(f"- Evidence JSON: `{json_path.as_posix()}`")
    lines.append(f"- Evidence Schema: `{schema_path.as_posix()}`")
    lines.append("")
    lines.append("## Overall Verdict")
    lines.append("")
    lines.append(f"- `live_ready`: {'✅ true' if live_ready else '❌ false'}")
    lines.append(f"- `schema_valid`: {'✅ true' if schema_valid else '❌ false'}")
    lines.append(f"- `dry_run_preflight`: `{str(dry_run).lower()}`")
    lines.append(f"- Breakdown: `live_success={live_count}`, `offline_fallback={offline_count}`, `failed={failed_count}`")
    lines.append("")
    lines.append("## Required Flow Outcomes (live_success required)")
    lines.append("")
    lines.append("| Flow | Canonical Endpoint | Resolved Endpoint | Status | Success | Offline | Classification | Error |")
    lines.append("|---|---|---|---:|:---:|:---:|---|---|")

    for flow in ("products", "rfid_complete_sale", "qr_confirm", "nfc_complete_sale"):
        phase = phase_map.get(flow, {})
        lines.append(
            "| {flow} | `{canonical}` | `{resolved}` | {status} | {success} | {offline} | `{classification}` | {error} |".format(
                flow=flow,
                canonical=canonical_to_endpoint.get(flow, f"/api/{flow}"),
                resolved=phase.get("resolved_endpoint", "n/a"),
                status=phase.get("status_code", "n/a"),
                success="✅" if phase.get("success") else "❌",
                offline="✅" if phase.get("offline") else "❌",
                classification=required_map.get(flow, phase.get("classification", "failed")),
                error=(phase.get("error") or "-").replace("|", "\\|"),
            )
        )

    lines.append("")
    lines.append("## Preflight")
    lines.append("")
    lines.append(f"- `ok`: {'✅ true' if preflight.get('ok') else '❌ false'}")

    missing_env = preflight.get("missing_env") or []
    missing_inputs = preflight.get("missing_inputs") or []
    missing_files = preflight.get("missing_files") or []
    preflight_errors = preflight.get("errors") or []

    lines.append(f"- `missing_env`: {', '.join(missing_env) if missing_env else 'none'}")
    lines.append(f"- `missing_inputs`: {', '.join(missing_inputs) if missing_inputs else 'none'}")
    lines.append(f"- `missing_files`: {', '.join(missing_files) if missing_files else 'none'}")

    if preflight_errors:
        lines.append("- `errors`:")
        for err in preflight_errors:
            lines.append(f"  - {err}")

    lines.append("")
    lines.append("## Diagnostics")
    lines.append("")
    queue_status = (data.get("diagnostics") or {}).get("queue_status")
    if queue_status is None:
        lines.append("- Queue status snapshot: `null` (not collected or preflight blocked)")
    else:
        lines.append("- Queue status snapshot:")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(queue_status, indent=2, ensure_ascii=False))
        lines.append("```")

    lines.append("")
    lines.append("## Artifact Pointers")
    lines.append("")
    lines.append(f"- Machine-readable evidence: `{json_path.as_posix()}`")
    lines.append(f"- Human-readable evidence: `{md_path.as_posix()}`")
    lines.append("- Milestone validation reference: `.gsd/milestones/M006/M006-VALIDATION.md`")
    lines.append("- Requirement traceability reference: `.gsd/REQUIREMENTS.md` (R053)")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()

    json_path = Path(args.evidence_json)
    md_path = Path(args.output_md)
    schema_path = Path(args.schema)

    if not json_path.exists():
        print(f"evidence_json_missing:{json_path.as_posix()}")
        return 1

    with json_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    markdown = render_summary(data, json_path, md_path, schema_path, args.base_url)

    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(markdown, encoding="utf-8")
    print(f"wrote:{md_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""M007/S09 runtime proof serializer.

This tool updates both:
- .gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json
- .gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md
"""

from __future__ import annotations

import argparse
import json
import platform
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

SCHEMA_VERSION = "1.0.0"
DEFAULT_JSON = ".gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json"
DEFAULT_MD = ".gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md"

REQUIRED_PHASES = [
    "s07_baseline",
    "apple_tooling",
    "simulator_build",
    "xctrace_templates",
    "artifact_completeness",
]
VALID_STATUS = {"pending", "running", "pass", "fail", "skipped", "not_run"}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def host_info() -> Dict[str, str]:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "machine": platform.machine(),
        "python": platform.python_version(),
    }


def default_doc() -> Dict[str, Any]:
    stamp = now_iso()
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": stamp,
        "updated_at": stamp,
        "host": host_info(),
        "overall_verdict": "in_progress",
        "required_phases": list(REQUIRED_PHASES),
        "phase_counts": {},
        "phases": [],
    }


def load_doc(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return default_doc()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("runtime proof root must be object")
    doc = default_doc()
    doc.update(payload)
    if not isinstance(doc.get("phases"), list):
        doc["phases"] = []
    if not isinstance(doc.get("host"), dict):
        doc["host"] = host_info()
    doc["updated_at"] = now_iso()
    return doc


def phase_sort_key(phase: Dict[str, Any]) -> tuple[int, str]:
    pid = str(phase.get("id") or "")
    return (REQUIRED_PHASES.index(pid), pid) if pid in REQUIRED_PHASES else (len(REQUIRED_PHASES), pid)


def normalize_status(status: str) -> str:
    out = str(status or "").strip().lower()
    if out not in VALID_STATUS:
        raise ValueError(f"invalid status: {status}")
    return out


def upsert_phase(doc: Dict[str, Any], phase: Dict[str, Any]) -> None:
    pid = str(phase["id"])
    existing = [p for p in doc.get("phases", []) if isinstance(p, dict) and str(p.get("id") or "") != pid]
    existing.append(phase)
    existing.sort(key=phase_sort_key)
    doc["phases"] = existing


def recompute(doc: Dict[str, Any]) -> None:
    statuses = [str(p.get("status") or "").lower() for p in doc.get("phases", []) if isinstance(p, dict)]
    counts: Dict[str, int] = {}
    for status in statuses:
        counts[status] = counts.get(status, 0) + 1
    doc["phase_counts"] = counts

    status_map = {
        str(p.get("id") or ""): str(p.get("status") or "").lower()
        for p in doc.get("phases", [])
        if isinstance(p, dict)
    }
    required_statuses = {phase_id: status_map.get(phase_id, "") for phase_id in REQUIRED_PHASES}

    if any(status == "fail" for status in required_statuses.values()):
        verdict = "fail"
    elif all(required_statuses.get(phase_id) == "pass" for phase_id in REQUIRED_PHASES):
        verdict = "pass"
    elif any(required_statuses.get(phase_id) == "running" for phase_id in REQUIRED_PHASES):
        verdict = "running"
    else:
        verdict = "in_progress"

    doc["overall_verdict"] = verdict
    doc["updated_at"] = now_iso()


def validate_runtime_proof_contract(doc: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    for key in ["generated_at", "host", "overall_verdict", "phases"]:
        if key not in doc:
            errors.append(f"missing_top_level:{key}")

    phases = doc.get("phases")
    if not isinstance(phases, list):
        errors.append("phases_not_list")
        return errors

    found = {str(p.get("id") or "") for p in phases if isinstance(p, dict)}
    for required in REQUIRED_PHASES:
        if required not in found:
            errors.append(f"missing_phase_id:{required}")

    required_phase_keys = ["id", "status", "command", "exit_code", "started_at", "finished_at", "guidance"]
    for idx, phase in enumerate(phases):
        if not isinstance(phase, dict):
            errors.append(f"phase[{idx}]_not_object")
            continue
        for key in required_phase_keys:
            if key not in phase:
                errors.append(f"phase[{idx}]_missing:{key}")
    return errors


def render_md(doc: Dict[str, Any], json_path: Path, md_path: Path) -> str:
    lines: List[str] = [
        "# S09 Runtime Proof",
        "",
        "## Metadata",
        "",
        f"- Generated at: `{doc.get('generated_at')}`",
        f"- Updated at: `{doc.get('updated_at')}`",
        f"- Overall verdict: `{doc.get('overall_verdict')}`",
        f"- JSON path: `{json_path.as_posix()}`",
        f"- Markdown path: `{md_path.as_posix()}`",
        "",
        "## Phase Results",
        "",
        "| Phase | Status | Exit | Started | Finished | Command |",
        "|---|---|---:|---|---|---|",
    ]

    for phase in doc.get("phases", []):
        if not isinstance(phase, dict):
            continue
        cmd = str(phase.get("command") or "").replace("`", "'")
        lines.append(
            "| {id} | `{status}` | {code} | `{start}` | `{end}` | `{cmd}` |".format(
                id=phase.get("id", "unknown"),
                status=phase.get("status", "unknown"),
                code=phase.get("exit_code", ""),
                start=phase.get("started_at", ""),
                end=phase.get("finished_at", ""),
                cmd=cmd,
            )
        )
        guidance = [str(g).strip() for g in phase.get("guidance", []) if str(g).strip()]
        if guidance:
            lines.append("|  | guidance |  |  |  | " + "<br/>".join(guidance).replace("|", "\\|") + " |")

    lines.extend(["", "## Phase Counts", "", "```json", json.dumps(doc.get("phase_counts", {}), indent=2), "```", ""])
    return "\n".join(lines)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update S09 runtime proof artifacts")
    parser.add_argument("--proof-json", default=DEFAULT_JSON)
    parser.add_argument("--proof-md", default=DEFAULT_MD)
    parser.add_argument("--phase-id", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--exit-code", type=int, default=0)
    parser.add_argument("--started-at", default=now_iso())
    parser.add_argument("--finished-at", default=now_iso())
    parser.add_argument("--guidance", action="append", default=[])
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    json_path = Path(args.proof_json)
    md_path = Path(args.proof_md)

    doc = load_doc(json_path)
    phase = {
        "id": args.phase_id,
        "status": normalize_status(args.status),
        "command": str(args.command),
        "exit_code": int(args.exit_code),
        "started_at": str(args.started_at),
        "finished_at": str(args.finished_at),
        "updated_at": now_iso(),
        "guidance": [str(g).strip() for g in args.guidance if str(g).strip()],
    }

    upsert_phase(doc, phase)
    recompute(doc)

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_md(doc, json_path, md_path), encoding="utf-8")

    print(
        "[verify-m007-s09-runtime] "
        f"phase={phase['id']} status={phase['status']} overall_verdict={doc['overall_verdict']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

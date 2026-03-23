"""
Normalize messy Transactions Log rows into a canonical 12-column schema.

Usage:
  rtk proxy python scripts/normalize_transactions_log.py --dry-run
  rtk proxy python scripts/normalize_transactions_log.py --apply

Canonical headers:
  TransactionID, Timestamp, StudentID, MoneyCardNumber, TransactionType,
  Amount, BalanceBefore, BalanceAfter, Status, ErrorMessage, ItemsJson, StationID
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import gspread
from dotenv import load_dotenv

load_dotenv()

CANONICAL_HEADERS = [
    "TransactionID",
    "Timestamp",
    "StudentID",
    "MoneyCardNumber",
    "TransactionType",
    "Amount",
    "BalanceBefore",
    "BalanceAfter",
    "Status",
    "ErrorMessage",
    "ItemsJson",
    "StationID",
]

STATUS_SET = {"completed", "success", "failed", "pending", "void", "voided", "error"}
TXID_RE = re.compile(r"^TXN-\d{14}-[A-Za-z0-9]+$")
TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
CARD_RE = re.compile(r"^[0-9A-Fa-f]{8}$|^[0-9A-Fa-f]{14}$")
NUM_RE = re.compile(r"^-?\d+(?:\.\d+)?$")

HEADER_KEYS = {
    "transactionid", "timestamp", "studentid", "moneycardnumber",
    "transactiontype", "amount", "balancebefore", "balanceafter",
    "status", "errormessage", "itemsjson", "stationid",
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9_]", "", (s or "").strip().lower())


def _is_headerish_token(s: str) -> bool:
    return _norm(s) in HEADER_KEYS | {"items", "transaction", "moneycard", "type", "error"}


def _is_json_payload(s: str) -> bool:
    t = (s or "").strip()
    if not t:
        return False
    if not ((t.startswith("[") and t.endswith("]")) or (t.startswith("{") and t.endswith("}"))):
        return False
    try:
        json.loads(t)
        return True
    except Exception:
        return False


def _num_or_blank(s: str) -> str:
    t = (s or "").strip()
    return t if NUM_RE.match(t) else ""


def _ensure_txid(ts: str, row_idx: int) -> str:
    if TS_RE.match(ts):
        base = re.sub(r"[-: ]", "", ts)
    else:
        base = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"TXN-{base}-LEGACY{row_idx:06d}"


def _infer_before_after(tx_type: str, amount: str, before: str, after: str) -> Tuple[str, str]:
    if before and after:
        return before, after

    if not amount or not NUM_RE.match(amount):
        return before, after

    amt = float(amount)
    kind = (tx_type or "").strip().lower()

    if not before and after and NUM_RE.match(after):
        aft = float(after)
        if "purchase" in kind:
            # Purchase usually deducts. If amount is positive, before = after + amount.
            # If amount is negative legacy style, before = after - amount.
            bef = aft + amt if amt >= 0 else aft - amt
            return str(int(bef)) if bef.is_integer() else str(bef), after
        if "load" in kind or "topup" in kind or "refund" in kind:
            bef = aft - amt
            return str(int(bef)) if bef.is_integer() else str(bef), after

    if before and not after and NUM_RE.match(before):
        bef = float(before)
        if "purchase" in kind:
            aft = bef - amt if amt >= 0 else bef + abs(amt)
            return before, str(int(aft)) if aft.is_integer() else str(aft)
        if "load" in kind or "topup" in kind or "refund" in kind:
            aft = bef + amt
            return before, str(int(aft)) if aft.is_integer() else str(aft)

    return before, after


def _extract_json_and_tail(tokens: List[str]) -> Tuple[str, List[str]]:
    items = ""
    out: List[str] = []
    for tok in tokens:
        t = (tok or "").strip()
        if not t:
            continue
        if _is_json_payload(t) and not items:
            items = t
            continue
        if _norm(t) == "itemsjson":
            continue
        out.append(t)
    return items, out


def parse_row(raw_row: List[str], row_idx: int) -> Optional[List[str]]:
    tokens = [c.strip() for c in raw_row if str(c).strip()]
    if not tokens:
        return None

    # Skip obvious header rows repeated in the body.
    if sum(1 for t in tokens if _is_headerish_token(t)) >= max(2, len(tokens) // 2):
        return None

    # Drop leading noise. Prefer TransactionID if present anywhere in the row.
    txid_start = next((i for i, t in enumerate(tokens) if TXID_RE.match(t)), None)
    if txid_start is not None:
        tokens = tokens[txid_start:]
    else:
        ts_start = next((i for i, t in enumerate(tokens) if TS_RE.match(t)), None)
        if ts_start is not None:
            tokens = tokens[ts_start:]

    txid = ""
    ts = ""
    sid = ""
    card = ""
    tx_type = ""
    amount = ""
    before = ""
    after = ""
    status = "Completed"
    err = ""
    items = ""
    station = ""

    # Case 1: canonical-ish row starting with TXN-
    if tokens and TXID_RE.match(tokens[0]):
        txid = tokens[0]
        ts = tokens[1] if len(tokens) > 1 else ""
        sid = tokens[2] if len(tokens) > 2 else ""
        card = tokens[3] if len(tokens) > 3 else ""
        tx_type = tokens[4] if len(tokens) > 4 else ""
        amount = _num_or_blank(tokens[5] if len(tokens) > 5 else "")
        before = _num_or_blank(tokens[6] if len(tokens) > 6 else "")
        after = _num_or_blank(tokens[7] if len(tokens) > 7 else "")
        status = tokens[8] if len(tokens) > 8 else status
        err = tokens[9] if len(tokens) > 9 else ""
        extras = tokens[10:] if len(tokens) > 10 else []
        items, extras = _extract_json_and_tail(extras)
        station = extras[0] if extras else ""

    # Case 2: legacy row starting with timestamp
    elif tokens and TS_RE.match(tokens[0]):
        ts = tokens[0]

        # ts, sid, card, type, amount, before, after, status, ...
        if len(tokens) >= 8 and tokens[1].isdigit() and CARD_RE.match(tokens[2]):
            sid = tokens[1]
            card = tokens[2]
            tx_type = tokens[3]
            amount = _num_or_blank(tokens[4])
            before = _num_or_blank(tokens[5])
            after = _num_or_blank(tokens[6])
            status = tokens[7]
            extra = tokens[8:]
            items, extra = _extract_json_and_tail(extra)
            if extra:
                if _norm(extra[0]) != "itemsjson":
                    err = extra[0] if not _is_json_payload(extra[0]) else ""
                if len(extra) > 1:
                    station = extra[1]

        # ts, card, type, amount, after, status, itemsjson ...
        elif len(tokens) >= 6 and CARD_RE.match(tokens[1]):
            card = tokens[1]
            tx_type = tokens[2]
            amount = _num_or_blank(tokens[3])
            after = _num_or_blank(tokens[4])
            status = tokens[5]
            extra = tokens[6:]
            items, extra = _extract_json_and_tail(extra)
            if extra:
                err = extra[0] if not _is_json_payload(extra[0]) else ""
                if len(extra) > 1:
                    station = extra[1]

        else:
            # Unrecognized timestamp row layout
            return None

        txid = _ensure_txid(ts, row_idx)

    else:
        # Unrecognized row layout
        return None

    if not txid:
        txid = _ensure_txid(ts, row_idx)

    if not TS_RE.match(ts):
        return None

    if status.strip().lower() not in STATUS_SET:
        status = "Completed"

    before, after = _infer_before_after(tx_type, amount, before, after)

    return [
        txid,
        ts,
        sid,
        card,
        tx_type,
        amount,
        before,
        after,
        status,
        err,
        items,
        station,
    ]


def _resolve_credentials_path() -> str:
    candidates = [
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip(),
        str(Path(__file__).resolve().parents[1] / "config" / "credentials.json"),
        "credentials.json",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    raise FileNotFoundError("Google credentials not found")


def load_sheet_values() -> Tuple[gspread.Worksheet, List[List[str]]]:
    sheet_id = os.getenv("GOOGLE_SHEETS_ID", "").strip()
    if not sheet_id:
        raise RuntimeError("GOOGLE_SHEETS_ID is not set")

    client = gspread.service_account(filename=_resolve_credentials_path())
    db = client.open_by_key(sheet_id)
    ws = db.worksheet("Transactions Log")
    return ws, ws.get_all_values()


def backup_csv(rows: List[List[str]]) -> Path:
    out_dir = Path("logs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"transactions_log_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return out


def rewrite_sheet(ws: gspread.Worksheet, rows: List[List[str]]) -> None:
    ws.clear()
    ws.resize(rows=max(len(rows) + 20, 200), cols=len(CANONICAL_HEADERS))

    batch = 400
    for i in range(0, len(rows), batch):
        chunk = rows[i : i + batch]
        start = i + 1
        end = i + len(chunk)
        ws.update(range_name=f"A{start}:L{end}", values=chunk)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="rewrite Transactions Log with normalized rows")
    parser.add_argument("--dry-run", action="store_true", help="analyze only (default)")
    args = parser.parse_args()

    ws, values = load_sheet_values()

    normalized: List[List[str]] = []
    skipped = 0
    for idx, row in enumerate(values, start=1):
        parsed = parse_row(row, idx)
        if parsed is None:
            skipped += 1
            continue
        normalized.append(parsed)

    # Deduplicate by txid+timestamp+card+amount while preserving order
    seen = set()
    deduped = []
    for r in normalized:
        key = (r[0], r[1], r[3], r[5])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    output = [CANONICAL_HEADERS] + deduped

    print(f"Rows in sheet: {len(values)}")
    print(f"Parsed rows: {len(normalized)}")
    print(f"Deduped rows: {len(deduped)}")
    print(f"Skipped rows: {skipped}")

    print("\nSample normalized rows:")
    for sample in deduped[:5]:
        print("  ", sample)

    if args.apply:
        backup = backup_csv(values)
        rewrite_sheet(ws, output)
        print(f"\nRewrote Transactions Log with {len(deduped)} rows")
        print(f"Backup saved: {backup}")
    else:
        print("\nDry-run only. Re-run with --apply to rewrite the sheet.")


if __name__ == "__main__":
    main()

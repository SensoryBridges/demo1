#!/usr/bin/env python3
"""Court Document Incident Tracker.

Filters the CSV court records under ``input/`` into incident records modeled on
Google Cloud's https://status.cloud.google.com/incidents.schema.json, timestamps
changes between runs, and notes who is affected (and how) and at which
locations / jurisdictions.

Outputs (under ``output/``):

    court_incidents.schema.json     Copy of the schema definition.
    court_incidents.json            Current filtered incident feed.
    court_incidents_history.jsonl   Append-only change log, one JSON per run.

Usage:
    python run_incident_tracker.py
    python run_incident_tracker.py --input ./input --output ./output
    python run_incident_tracker.py --since 2022-01-01 --status RIGHTS_VIOLATION
    python run_incident_tracker.py --party "Hon. Donna Seigler Crouch"
    python run_incident_tracker.py --case 2020DR3201732
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SCHEMA_SRC = REPO_ROOT / "court_incidents.schema.json"

EVENT_TYPE_TO_STATUS = {
    "Order": "COURT_ORDER_ISSUED",
    "Filing": "FILING_ENTERED",
    "Hearing": "HEARING_HELD",
    "Deadline": "DEADLINE_SET",
    "Service of Process": "SERVICE_EVENT",
    "Visitation Data": "RIGHTS_VIOLATION",
    "Communication": "INFORMATIONAL",
    "Document Creation": "INFORMATIONAL",
}

# Words in the description that upgrade severity.
CRITICAL_MARKERS = (
    "constitutional", "due process", "custody", "emergency order", "ex parte",
    "fraud", "perjury", "contempt", "warrant",
)
HIGH_MARKERS = (
    "violation", "denied", "struck", "sanction", "dismiss", "gal",
    "visitation", "order",
)

# Roles inferred from free-text party tags.
ROLE_HINTS = (
    ("Judge", ("judge", "hon.", "j.")),
    ("GAL", ("gal",)),
    ("Attorney", ("esq", "attorney", "counsel")),
    ("Clerk", ("clerk",)),
)

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
    "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY", "DC",
}


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s or "unknown"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_date(raw: str) -> str | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
    return None


def split_multi(value: str) -> list[str]:
    if not value:
        return []
    parts = re.split(r"\s*[;|]\s*|\s*,\s(?=[A-Z])", value)
    return [p.strip() for p in parts if p and p.strip()]


def infer_role(name: str) -> str | None:
    low = name.lower()
    for role, hints in ROLE_HINTS:
        if any(h in low for h in hints):
            return role
    return None


def load_officials(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            name = (row.get("name") or "").strip()
            if not name:
                continue
            out[name.lower()] = {
                "name": name,
                "role": (row.get("role") or "").strip() or None,
                "party": (row.get("party") or "").strip() or None,
                "law_firm": (row.get("law_firm") or "").strip() or None,
            }
    return out


def load_addresses(path: Path) -> dict[str, dict]:
    """Map a person name (lowercased) to the richest address record for them."""
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            person = (row.get("person") or "").strip()
            if not person:
                continue
            out.setdefault(person.lower(), {
                "address": (row.get("address") or "").strip() or None,
                "city": (row.get("city") or "").strip() or None,
                "state": (row.get("state") or "").strip() or None,
                "zip": (row.get("zip") or "").strip() or None,
                "implications": (row.get("jurisdiction_implications") or "").strip() or None,
            })
    return out


def parse_parties(raw: str, officials: dict[str, dict], how: str | None) -> list[dict]:
    parties = []
    seen = set()
    for name in split_multi(raw):
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        official = officials.get(key)
        role = official["role"] if official else infer_role(name)
        parties.append({
            "title": name,
            "id": slugify(name),
            "role": role,
            "how_affected": how,
        })
    return parties


def parse_locations(raw: str, addresses: dict[str, dict], parties: list[dict]) -> list[dict]:
    locations: list[dict] = []
    seen = set()

    def add(title: str, **extra):
        key = slugify(title)
        if not title or key in seen:
            return
        seen.add(key)
        rec = {"title": title, "id": key, "jurisdiction": None,
               "state": None, "county": None, "address": None, "implications": None}
        rec.update({k: v for k, v in extra.items() if v is not None})
        locations.append(rec)

    for chunk in split_multi(raw):
        state = next((tok for tok in re.split(r"[\s,]+", chunk) if tok.upper() in US_STATES), None)
        county_match = re.search(r"([A-Z][A-Za-z]+)\s+County", chunk)
        jurisdiction = None
        if county_match or "court" in chunk.lower():
            jurisdiction = chunk
        add(chunk,
            state=state.upper() if state else None,
            county=county_match.group(1) if county_match else None,
            jurisdiction=jurisdiction)

    for party in parties:
        addr = addresses.get(party["title"].lower())
        if not addr:
            continue
        pieces = [addr.get("city"), addr.get("state")]
        title = ", ".join(p for p in pieces if p) or addr.get("address") or party["title"]
        add(title,
            address=addr.get("address"),
            state=addr.get("state"),
            implications=addr.get("implications"))

    return locations


def derive_severity(event_type: str, description: str, violations: str, laws: str) -> str:
    haystack = " ".join([event_type or "", description or "", violations or "", laws or ""]).lower()
    if any(m in haystack for m in CRITICAL_MARKERS):
        return "critical"
    if any(m in haystack for m in HIGH_MARKERS):
        return "high"
    if event_type in ("Communication", "Document Creation"):
        return "low"
    return "medium"


def derive_status_impact(event_type: str, description: str, violations: str) -> str:
    if violations.strip():
        return "RIGHTS_VIOLATION"
    return EVENT_TYPE_TO_STATUS.get(event_type, "INFORMATIONAL")


def incident_id(case: str, begin: str, desc: str, source: str) -> str:
    digest = hashlib.sha1("|".join([case, begin or "", desc or "", source or ""]).encode()).hexdigest()
    return digest[:16]


def build_incidents(rows: list[dict], officials: dict, addresses: dict) -> list[dict]:
    incidents = []
    for row in rows:
        begin = parse_date(row.get("date", ""))
        if not begin:
            continue
        desc = (row.get("description") or "").strip()
        event_type = (row.get("event_type") or "").strip()
        case = (row.get("case_number") or "").strip()
        violations = (row.get("violations") or "").strip()
        laws = (row.get("laws_broken") or "").strip()
        notes = (row.get("notes") or "").strip()
        source = (row.get("source_document") or "").strip()

        how = None
        if event_type == "Filing":
            how = "filer or subject of filing"
        elif event_type == "Order":
            how = "subject of court order"
        elif event_type == "Visitation Data":
            how = "denied or limited court-ordered visitation"
        elif event_type == "Service of Process":
            how = "served with process"
        elif event_type == "Deadline":
            how = "bound by deadline"

        parties = parse_parties(row.get("persons_involved", ""), officials, how)
        locations = parse_locations(row.get("location", ""), addresses, parties)

        inc_id = incident_id(case, begin, desc, source)
        incidents.append({
            "id": inc_id,
            "number": case or None,
            "begin": begin,
            "end": None,
            "external_desc": desc,
            "event_type": event_type or None,
            "source_document": source or None,
            "uri": None,
            "status_impact": derive_status_impact(event_type, desc, violations),
            "severity": derive_severity(event_type, desc, violations, laws),
            "laws_broken": split_multi(laws),
            "violations": split_multi(violations),
            "affected_parties": parties,
            "currently_affected_locations": locations,
            "previously_affected_locations": [],
            "_notes": notes or None,
        })
    return incidents


# Fields that, when they change, count as a meaningful update worth timestamping.
TRACKED_FIELDS = (
    "external_desc", "event_type", "source_document", "status_impact",
    "severity", "laws_broken", "violations", "affected_parties",
    "currently_affected_locations", "number", "end",
)


def diff_fields(current: dict, previous: dict) -> list[str]:
    return [f for f in TRACKED_FIELDS if current.get(f) != previous.get(f)]


def merge_with_previous(current: list[dict], previous: list[dict], run_ts: str) -> tuple[list[dict], dict]:
    prev_by_id = {inc["id"]: inc for inc in previous}
    current_ids = {inc["id"] for inc in current}
    summary = {"run_at": run_ts, "opened": [], "updated": [], "resolved": []}
    merged = []

    for inc in current:
        prior = prev_by_id.get(inc["id"])
        if prior is None:
            inc["created"] = run_ts
            inc["modified"] = run_ts
            opened_update = {
                "created": run_ts,
                "modified": None,
                "when": inc["begin"],
                "text": f"Incident first observed by tracker: {inc['external_desc']}",
                "status": "OPENED",
                "changed_fields": [],
                "affected_locations": inc["currently_affected_locations"],
            }
            inc["updates"] = [opened_update]
            inc["most_recent_update"] = opened_update
            summary["opened"].append(inc["id"])
        else:
            changed = diff_fields(inc, prior)
            inc["created"] = prior.get("created", run_ts)
            prior_updates = prior.get("updates", [])
            if changed:
                prev_locs = prior.get("currently_affected_locations", [])
                new_locs = inc["currently_affected_locations"]
                if "currently_affected_locations" in changed:
                    new_ids = {loc["id"] for loc in new_locs}
                    inc["previously_affected_locations"] = (
                        prior.get("previously_affected_locations", [])
                        + [loc for loc in prev_locs if loc["id"] not in new_ids]
                    )
                else:
                    inc["previously_affected_locations"] = prior.get("previously_affected_locations", [])
                update = {
                    "created": run_ts,
                    "modified": None,
                    "when": run_ts,
                    "text": "Changed fields: " + ", ".join(changed),
                    "status": "UPDATED",
                    "changed_fields": changed,
                    "affected_locations": new_locs,
                }
                inc["modified"] = run_ts
                inc["updates"] = prior_updates + [update]
                inc["most_recent_update"] = update
                summary["updated"].append({"id": inc["id"], "changed_fields": changed})
            else:
                inc["modified"] = prior.get("modified", inc["created"])
                inc["updates"] = prior_updates
                inc["most_recent_update"] = prior.get("most_recent_update") or (prior_updates[-1] if prior_updates else None)
                inc["previously_affected_locations"] = prior.get("previously_affected_locations", [])
        merged.append(inc)

    for prev_id, prev_inc in prev_by_id.items():
        if prev_id in current_ids:
            continue
        resolved = dict(prev_inc)
        resolve_update = {
            "created": run_ts,
            "modified": None,
            "when": run_ts,
            "text": "Incident no longer present in source records; marking resolved.",
            "status": "RESOLVED",
            "changed_fields": [],
            "affected_locations": resolved.get("currently_affected_locations", []),
        }
        resolved["modified"] = run_ts
        resolved["end"] = run_ts
        resolved["updates"] = resolved.get("updates", []) + [resolve_update]
        resolved["most_recent_update"] = resolve_update
        merged.append(resolved)
        summary["resolved"].append(prev_id)

    merged.sort(key=lambda i: (i.get("begin") or "", i.get("id")))
    return merged, summary


def apply_filters(incidents: list[dict], args: argparse.Namespace) -> list[dict]:
    out = incidents
    if args.since:
        out = [i for i in out if i.get("begin") and i["begin"] >= args.since]
    if args.until:
        out = [i for i in out if i.get("begin") and i["begin"] <= args.until]
    if args.case:
        out = [i for i in out if (i.get("number") or "") == args.case]
    if args.status:
        wanted = set(args.status)
        out = [i for i in out if i.get("status_impact") in wanted]
    if args.severity:
        wanted = set(args.severity)
        out = [i for i in out if i.get("severity") in wanted]
    if args.party:
        needle = args.party.lower()
        out = [i for i in out if any(needle in p["title"].lower() for p in i["affected_parties"])]
    if args.location:
        needle = args.location.lower()
        out = [i for i in out
               if any(needle in loc["title"].lower() for loc in i["currently_affected_locations"])]
    return out


def load_previous(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def load_timeline(path: Path) -> list[dict]:
    if not path.exists():
        print(f"error: timeline CSV not found: {path}", file=sys.stderr)
        sys.exit(2)
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    parser = argparse.ArgumentParser(description="Filter court documents into a timestamped incident feed.")
    parser.add_argument("--input", type=Path, default=REPO_ROOT / "input",
                        help="Directory containing timeline / officials / addresses CSVs.")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "output",
                        help="Directory to write schema, feed and history.")
    parser.add_argument("--timeline", type=Path,
                        help="Override path to the timeline CSV (defaults to <input>/comprehensive_timeline.csv).")
    parser.add_argument("--since", help="Only include events on or after this ISO date.")
    parser.add_argument("--until", help="Only include events on or before this ISO date.")
    parser.add_argument("--case", help="Only include events with this exact case number.")
    parser.add_argument("--status", action="append", help="Filter by status_impact (repeatable).")
    parser.add_argument("--severity", action="append", help="Filter by severity (repeatable).")
    parser.add_argument("--party", help="Substring match against affected party names.")
    parser.add_argument("--location", help="Substring match against affected location titles.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print the JSON output.")
    args = parser.parse_args()

    input_dir: Path = args.input
    output_dir: Path = args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    timeline_path = args.timeline or (input_dir / "comprehensive_timeline.csv")
    officials = load_officials(input_dir / "court_officials.csv")
    addresses = load_addresses(input_dir / "addresses_jurisdiction.csv")
    rows = load_timeline(timeline_path)

    incidents = build_incidents(rows, officials, addresses)
    filtered = apply_filters(incidents, args)
    is_query = any([args.since, args.until, args.case, args.status, args.severity,
                    args.party, args.location])

    schema_out = output_dir / "court_incidents.schema.json"
    if SCHEMA_SRC.exists():
        shutil.copyfile(SCHEMA_SRC, schema_out)

    indent = 2 if args.pretty else None
    run_ts = now_iso()

    if is_query:
        # Filter query: don't mutate the canonical feed or append to history.
        out_path = output_dir / "court_incidents.filtered.json"
        for inc in filtered:
            inc.setdefault("created", run_ts)
            inc.setdefault("modified", run_ts)
            inc.setdefault("updates", [])
            inc.setdefault("most_recent_update", None)
        out_path.write_text(json.dumps(filtered, indent=indent, ensure_ascii=False) + "\n",
                            encoding="utf-8")
        print(f"Wrote {len(filtered)} filtered incidents to {out_path}")
        print("  (filter-mode run; canonical feed and history untouched)")
        return 0

    feed_path = output_dir / "court_incidents.json"
    history_path = output_dir / "court_incidents_history.jsonl"

    previous = load_previous(feed_path)
    merged, summary = merge_with_previous(filtered, previous, run_ts)

    feed_path.write_text(json.dumps(merged, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")
    with history_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(summary, ensure_ascii=False) + "\n")

    print(f"Wrote {len(merged)} incidents to {feed_path}")
    print(f"  opened:   {len(summary['opened'])}")
    print(f"  updated:  {len(summary['updated'])}")
    print(f"  resolved: {len(summary['resolved'])}")
    print(f"  history:  {history_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

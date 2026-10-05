"""
Fetch Senedd Record of Proceedings committee transcripts and collate them
into one CSV of spoken contributions. Standard library only.

This script will recreate 'senedd.csv':

    python data/senedd/fetch_senedd.py --max-meetings 30 --per-committee 3

Raw XML is cached in data/senedd/raw/ (not committed), so re-runs only fetch
what is missing. IDs that turned out not to be transcripts are remembered in
raw/skipped.txt and never requested again.

Contains public sector information licensed under the Open Government Licence v3.0.
"""

import argparse
import csv
import html
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

URL = ("https://record.senedd.wales/XMLExport/Download"
       "?meetingID={id}&xmlDownloadType=EnglishTranscript")
USER_AGENT = "AI Wales embeddings workshop (one-off data prep; https://github.com/AI-Wales)"
HERE = Path(__file__).resolve().parent

COLUMNS = ["meeting_id", "date", "committee", "agenda_item", "contribution_id",
           "contribution_order", "speaker", "spoken_in", "chunk", "word_count", "text"]


# ---------- parsing ----------

def parse_rows(data):
    """Return the contribution elements, or [] if this isn't a transcript."""
    try:
        root = ET.fromstring(data.lstrip(b"\xef\xbb\xbf"))  # strip the byte-order mark
    except ET.ParseError:
        return []
    return list(root) if root.tag == "dataroot" else []


def field(row, name):
    return (row.findtext(name) or "").strip()


def clean_html(fragment):
    """Contribution text is escaped HTML: drop tags, decode entities, tidy whitespace."""
    text = re.sub(r"<[^>]+>", " ", fragment)
    return " ".join(html.unescape(text).split())


def committee_from_tag(tag):
    """'XML_HealthAndSocialCareCommittee_English' -> 'Health And Social Care Committee'"""
    name = re.sub(r"^XML_|_(English|Welsh|Bilingual)$", "", tag)
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)


def windows(words, size, overlap):
    """Overlapping word windows, so every row fits the embedding model's token limit."""
    if size <= 0 or len(words) <= size:
        yield " ".join(words)
        return
    for start in range(0, len(words) - overlap, size - overlap):
        yield " ".join(words[start:start + size])


def to_records(rows, min_words, chunk_words, overlap):
    """Spoken contributions only; procedural notes and one-liners are dropped."""
    for row in rows:
        if field(row, "contribution_type") != "C":
            continue
        words = clean_html(field(row, "Contribution_English")).split()
        if len(words) < min_words:
            continue
        base = {
            "meeting_id": field(row, "Meeting_ID"),
            "date": field(row, "MeetingDate")[:10],
            "committee": committee_from_tag(row.tag),
            "agenda_item": field(row, "Agenda_item_english"),
            "contribution_id": field(row, "Contribution_ID"),
            "contribution_order": field(row, "Contribution_Order_ID"),
            "speaker": field(row, "Member_name_English"),
            "spoken_in": field(row, "contribution_language"),  # En, or Cy = interpreted from Welsh
        }
        for n, text in enumerate(windows(words, chunk_words, overlap)):
            yield {**base, "chunk": n, "word_count": len(text.split()), "text": text}


# ---------- downloading ----------

def fetch(meeting_id, raw_dir, skipped, pause):
    """Transcript bytes for a meeting (from cache if possible), or None."""
    path = raw_dir / f"{meeting_id}.xml"
    if path.exists():
        return path.read_bytes()
    if meeting_id in skipped:
        return None

    request = urllib.request.Request(URL.format(id=meeting_id),
                                     headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read()
    except urllib.error.HTTPError as error:
        if error.code != 404:
            print(f"  {meeting_id}: HTTP {error.code}, will retry next run")
            return None
        data = b""  # definitely not a transcript
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"  {meeting_id}: {error}, will retry next run")
        return None
    finally:
        time.sleep(pause)  # be polite, whatever happened

    if parse_rows(data):
        path.write_bytes(data)
        return data
    skipped.add(meeting_id)
    return None


def collect_meetings(ids, raw_dir, max_meetings, per_committee, skip_plenary, pause):
    skipped_path = raw_dir / "skipped.txt"
    skipped = set(skipped_path.read_text().split()) if skipped_path.exists() else set()
    chosen, per = [], Counter()
    try:
        for meeting_id in map(str, ids):
            if len(chosen) >= max_meetings:
                break
            data = fetch(meeting_id, raw_dir, skipped, pause)
            if not data:
                continue
            rows = parse_rows(data)
            committee = committee_from_tag(rows[0].tag)
            if skip_plenary and "plenary" in committee.lower():
                print(f"  {meeting_id}: {committee} - skipped (plenary)")
                continue
            if per_committee and per[committee] >= per_committee:
                print(f"  {meeting_id}: {committee} - skipped (have {per_committee} already)")
                continue
            per[committee] += 1
            chosen.append((meeting_id, rows))
            print(f"  {meeting_id}: {committee} ({len(rows)} rows) [{len(chosen)}/{max_meetings}]")
    except KeyboardInterrupt:
        print("\ninterrupted - writing what we have")
    finally:
        skipped_path.write_text("\n".join(sorted(skipped)))
    return chosen


# ---------- main ----------

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--start", type=int, default=16330, help="highest meeting ID to try")
    parser.add_argument("--stop", type=int, default=15000, help="lowest meeting ID to try")
    parser.add_argument("--ids", type=int, nargs="*", help="explicit meeting IDs (overrides --start/--stop)")
    parser.add_argument("--max-meetings", type=int, default=30)
    parser.add_argument("--per-committee", type=int, default=3, help="cap per committee; 0 for no cap")
    parser.add_argument("--include-plenary", action="store_true")
    parser.add_argument("--min-words", type=int, default=20)
    parser.add_argument("--chunk-words", type=int, default=150, help="0 keeps contributions whole")
    parser.add_argument("--overlap", type=int, default=30)
    parser.add_argument("--pause", type=float, default=1.0, help="seconds between requests")
    parser.add_argument("--raw-dir", type=Path, default=HERE / "raw")
    parser.add_argument("--out", type=Path, default=HERE / "senedd.csv")
    args = parser.parse_args()

    if args.chunk_words and args.overlap >= args.chunk_words:
        parser.error("--overlap must be smaller than --chunk-words")

    args.raw_dir.mkdir(parents=True, exist_ok=True)
    ids = args.ids or range(args.start, args.stop - 1, -1)

    print(f"fetching up to {args.max_meetings} transcripts...")
    meetings = collect_meetings(ids, args.raw_dir, args.max_meetings, args.per_committee,
                                not args.include_plenary, args.pause)

    records = [record for _, rows in meetings
               for record in to_records(rows, args.min_words, args.chunk_words, args.overlap)]
    records.sort(key=lambda r: (r["date"], int(r["meeting_id"]),
                                int(r["contribution_order"] or 0), r["chunk"]))

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(records)

    dates = sorted(r["date"] for r in records)
    print(f"\nwrote {len(records)} rows from {len(meetings)} meetings to {args.out}")
    if dates:
        print(f"dates: {dates[0]} to {dates[-1]}")
    print("rows per committee:")
    for committee, n in Counter(r["committee"] for r in records).most_common():
        print(f"  {n:6d}  {committee}")


if __name__ == "__main__":
    main()

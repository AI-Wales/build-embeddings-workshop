#!/usr/bin/env python3
"""
Fetch recent commit history from public git repositories and collate it into
one CSV. Needs git on the PATH; otherwise standard library only.

This script creates 'git_log.csv':

    python data/git_log/fetch.py

By default this takes the most recent 3,000 non-merge commits from the Linux
kernel and PyTorch. Each repository is a bare, partial clone (commit messages
only, no files), deepened in small steps and cached in data/git_log/raw/,
which is not committed.

Author names are never collected. Sign-off trailers, maintainer notes and
email addresses are stripped from commit bodies. Any 'Assisted-by:'
declarations of AI-tool help are kept in their own column.
"""

import argparse
import csv
import re
import shutil
import subprocess
import time
from collections import Counter
from pathlib import Path

DEFAULT_REPOS = [
    "https://github.com/torvalds/linux",
    "https://github.com/pytorch/pytorch",
]
HERE = Path(__file__).resolve().parent
COLUMNS = ["repo", "hash", "date", "prefix", "scope", "message", "subject",
           "body", "body_words", "assisted_by"]

# "[inductor] Fix x" (PyTorch style) or "drm/amd/display: Fix x" (Linux style)
SCOPE_PREFIX = re.compile(r"^\s*(?:\[([^\]]+)\]|([\w.+-]+(?:/[\w.+-]+)*):)\s+")

# Body lines that are metadata rather than prose - mostly names and email addresses
TRAILER = re.compile(
    r"^\s*(?:(?:signed-off|reviewed|acked|tested|reported|suggested|co-developed|"
    r"reported-and-tested|co-authored)-by|cc|link|closes|fixes|message-id|change-id|"
    r"pull request resolved|approved by|differential revision|ghstack-source-id)\s*:"
    r"|^\s*cc\s+@"                        # PyTorch "cc @someone" lines
    r"|^\s*stack from \[ghstack\]"        # PyTorch ghstack header
    r"|^\s*\*\s+(?:__->__\s+)?#\d+"       # ghstack PR list
    r"|^\s*\(cherry picked from commit"   # backport boilerplate
    r"|^\s*\[[\w.-]+: [^\]]*\]\s*$",      # maintainer edit notes, e.g. "[name: commit log]"
    re.IGNORECASE,
)
ASSISTED = re.compile(r"^\s*assisted-by\s*:\s*(.+?)\s*$", re.IGNORECASE)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


# ---------- git ----------

def repo_name(url):
    name = url.rstrip("/").split("/")[-1]
    return name[:-4] if name.endswith(".git") else name


def git(*args, retries=1):
    """Run git. HTTP/1.1 avoids the 'curl 92 ... HTTP/2 stream ... CANCEL' failure."""
    for attempt in range(1, retries + 1):
        try:
            return subprocess.run(["git", "-c", "http.version=HTTP/1.1", *args],
                                  capture_output=True, text=True, encoding="utf-8",
                                  errors="replace", check=True).stdout
        except subprocess.CalledProcessError:
            if attempt == retries:
                raise
            print(f"  git failed, retrying ({attempt}/{retries - 1})...")
            time.sleep(5 * attempt)


def count_commits(path):
    return int(git("-C", str(path), "rev-list", "--count", "--no-merges", "HEAD"))


def clone(url, commits, raw_dir, refresh, step=250, max_rounds=100):
    """Bare, partial (no trees or blobs) clone, deepened in small steps until it
    holds at least `commits` non-merge commits. Many small requests instead of
    one huge shallow computation that the server gives up on."""
    path = raw_dir / f"{repo_name(url)}.git"
    if path.exists() and (refresh or not (path / "HEAD").exists()):
        shutil.rmtree(path)  # refresh requested, or a half-finished clone
    if not path.exists():
        print(f"cloning {url} (messages only)...")
        git("clone", "--bare", "--filter=tree:0", "--depth", "1", url, str(path))

    branch = git("-C", str(path), "symbolic-ref", "HEAD").strip()  # e.g. refs/heads/master
    have = count_commits(path)
    for _ in range(max_rounds):
        if have >= commits:
            break
        git("-C", str(path), "fetch", f"--deepen={step}", "origin",
            f"+{branch}:{branch}", retries=3)
        now = count_commits(path)
        print(f"  {now} non-merge commits")
        if now == have:  # nothing deeper to fetch: we've reached the start of history
            break
        have = now
    return path


# ---------- parsing ----------

def clean_body(body):
    """Drop trailer lines, pull out Assisted-by declarations, redact email addresses."""
    kept, assisted = [], []
    for line in body.splitlines():
        match = ASSISTED.match(line)
        if match:
            assisted.append(match.group(1))
        elif not TRAILER.match(line):
            kept.append(line)
    text = " ".join(" ".join(kept).split())
    return EMAIL.sub("<email>", text), EMAIL.sub("<email>", "; ".join(assisted))


def read_log(path, name, commits, include_merges):
    args = ["-C", str(path), "log", f"--max-count={commits}", "--date=short",
            "--pretty=format:%H%x1f%ad%x1f%s%x1f%b%x1e"]
    if not include_merges:
        args.append("--no-merges")
    for entry in git(*args).split("\x1e"):
        parts = entry.strip("\n").split("\x1f")
        if len(parts) != 4:
            continue
        commit_hash, date, subject, body = parts
        match = SCOPE_PREFIX.match(subject)
        prefix = (match.group(1) or match.group(2)) if match else ""
        body, assisted = clean_body(body)
        yield {
            "repo": name,
            "hash": commit_hash[:12],
            "date": date,
            "prefix": prefix,
            "scope": prefix.split("/")[0].lower(),
            "message": subject[match.end():] if match else subject,
            "subject": subject,
            "body": body,
            "body_words": len(body.split()),
            "assisted_by": assisted,
        }


# ---------- main ----------

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", action="append", dest="repos",
                        help="repository URL (repeatable); defaults to Linux and PyTorch")
    parser.add_argument("--commits", type=int, default=3000,
                        help="most recent N non-merge commits per repo")
    parser.add_argument("--include-merges", action="store_true")
    parser.add_argument("--refresh", action="store_true",
                        help="re-clone to pick up newer commits")
    parser.add_argument("--step", type=int, default=250,
                        help="commits to deepen per request; lower it if requests time out")
    parser.add_argument("--raw-dir", type=Path, default=HERE / "raw")
    parser.add_argument("--out", type=Path, default=HERE / "git_log.csv")
    args = parser.parse_args()

    args.raw_dir.mkdir(parents=True, exist_ok=True)
    records = []
    try:
        for url in args.repos or DEFAULT_REPOS:
            path = clone(url, args.commits, args.raw_dir, args.refresh, step=args.step)
            rows = list(read_log(path, repo_name(url), args.commits, args.include_merges))
            records.extend(rows)
            if not rows:
                print(f"\n{repo_name(url)}: no commits found")
                continue
            scopes = Counter(r["scope"] for r in rows if r["scope"])
            assisted = sum(1 for r in rows if r["assisted_by"])
            print(f"\n{repo_name(url)}: {len(rows)} commits, {sum(scopes.values())} with a "
                  f"scope prefix ({len(scopes)} distinct), {rows[-1]['date']} to {rows[0]['date']}")
            print(f"{assisted} commits declare AI assistance (Assisted-by)")
            print("top scopes:")
            for scope, n in scopes.most_common(15):
                print(f"  {n:5d}  {scope}")
    except subprocess.CalledProcessError as error:
        raise SystemExit(f"git failed:\n{error.stderr}")

    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(records)
    print(f"\nwrote {len(records)} rows to {args.out}")


if __name__ == "__main__":
    main()

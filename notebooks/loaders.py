import csv
import subprocess
import pandas as pd
from pathlib import Path


def _repo_name_from_url(url):
    name = url.rstrip("/").split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return name


def clone_or_update_repo(repo_url, cache_dir="../.cache/repos", depth=500):
    """Clone a GitHub repo into a local cache, or pull latest if already
    cloned. Shallow by default - a full history isn't needed for embedding
    commit messages, and it keeps the download small on venue wifi."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    repo_path = cache_dir / _repo_name_from_url(repo_url)

    if (repo_path / ".git").exists():
        subprocess.run(["git", "-C", str(repo_path), "pull", "--ff-only"],
                        capture_output=True, text=True)
    else:
        result = subprocess.run(
            ["git", "clone", "--depth", str(depth), repo_url, str(repo_path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"could not clone {repo_url}:\n{result.stderr}")

    return repo_path


def load_git_log(repo_path_or_url):
    """Read commit history as a list of records. Accepts a local path
    (e.g. ".") or a GitHub URL, which gets cloned into the cache first."""
    if repo_path_or_url.startswith(("http://", "https://", "git@")):
        repo_path = clone_or_update_repo(repo_path_or_url)
    else:
        repo_path = repo_path_or_url

    result = subprocess.run(
        ["git", "-C", str(repo_path), "log", "--pretty=format:%H%x1f%ad%x1f%s", "--date=short"],
        capture_output=True, text=True, check=True,
    )
    records = []
    for line in result.stdout.splitlines():
        commit_hash, commit_date, subject = line.split("\x1f")
        records.append({"hash": commit_hash[:8], "date": commit_date, "message": subject})
    return records


def load_csv(path):
    """Read a CSV (plain, .gz, or a .zip holding one CSV) as a list of dicts of strings.
    Everything stays text and blanks stay "", so nothing downstream trips over NaN."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    return df.apply(lambda col: col.str.strip()).to_dict("records")


def render(record, fields):
    """Concatenate selected fields into the text that actually gets embedded.
    Swap which fields are listed here to change what 'similar' means."""
    return ". ".join(str(record[f]) for f in fields if record.get(f))

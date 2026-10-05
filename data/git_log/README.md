# Git commit history: Linux kernel and PyTorch

Recent commit messages from two large, active open-source projects, collated into one CSV. Both projects prefix most commit subjects with the part of the codebase they touch: "drm/mediatek: Fix ..." in Linux, "[inductor] ..." in PyTorch. We split that prefix off and hold it out as a free ground-truth label. Can embeddings of the rest of the message rediscover which subsystem a change belongs to?

## At a glance

| | |
|---|---|
| File | `git_log.csv` (about 9 MB) |
| Rows | 6,000 (3,000 per repository) |
| Merge commits | Excluded |
| Snapshot taken | 5 October 2026 |
| Built by | `fetch.py` in this folder |

| | Linux kernel | PyTorch |
|---|---|---|
| Commits | 3,000 | 3,000 |
| Date range | 21 Aug to 4 Oct 2026 | 12 Aug to 5 Oct 2026 |
| With a scope prefix | 2,956 (98.5%) | 1,694 (56%) |
| Distinct scopes | 304 | 154 |

## Top scopes

| Linux scope | Commits | | PyTorch scope | Commits |
|---|---|---|---|---|
| net | 278 | | dynamo | 206 |
| drm | 259 | | testcase refactoring | 188 |
| selftests | 118 | | inductor | 167 |
| xfs | 101 | | mps | 115 |
| asoc | 95 | | rocm | 113 |
| wifi | 95 | | test | 103 |
| alsa | 94 | | distributed | 76 |
| bpf | 81 | | precompile | 66 |
| usb | 72 | | be | 55 |
| kvm | 71 | | aot_compile | 43 |
| smb | 70 | | ci | 37 |
| bluetooth | 65 | | cuda | 26 |
| s390 | 54 | | c10d | 24 |
| iio | 53 | | xpu | 21 |
| perf | 34 | | torchcomms hash update | 21 |

A rough guide to the less obvious ones:

- **Linux:** `drm` is graphics, `xfs` is a filesystem, `asoc` and `alsa` are both audio (ALSA System on Chip, and the core sound layer), `bpf` is the in-kernel programmable virtual machine, `kvm` is virtualisation, `smb` is Windows-style file sharing, `s390` is the IBM mainframe architecture, `iio` is industrial I/O (mostly sensors), and `selftests` is the kernel's own test suite.
- **PyTorch:** `dynamo` is graph capture for `torch.compile`, `inductor` is its compiler backend, `mps` is Apple GPUs, `rocm` is AMD GPUs, `xpu` is Intel GPUs, `distributed` and `c10d` are multi-GPU communication, `precompile` and `aot_compile` are ahead-of-time compilation, `be` is "better engineering" (clean-up work), and `torchcomms hash update` is an automated dependency bump.

## Columns

| Column | Example | Notes |
|---|---|---|
| repo | linux | Repository name |
| hash | 048739be3e9c | Short commit hash, enough to look the commit up |
| date | 2026-09-21 | Author date |
| prefix | drm/mediatek | The full prefix, as written |
| scope | drm | First segment of the prefix, lower-cased. Our ground-truth label. Empty if there was no prefix |
| message | Fix ovl adaptor platform device leak | Subject with the prefix removed. What we embed by default |
| subject | drm/mediatek: Fix ovl adaptor platform device leak | The original subject line, prefix included |
| body | ... | Commit body with trailers, maintainer notes and email addresses removed |
| body_words | 103 | Words in the cleaned body |
| assisted_by | LLM | Any `Assisted-by:` declarations of AI-tool help, separated by `; `. Empty if none |

## How it was made

```
python data/git_log/fetch.py --commits 3000
```

For each repository, the script:

1. Makes a bare, partial clone: commit messages only, with no files or trees. It starts one commit deep and deepens in small steps until it holds enough non-merge commits. Small requests are cheap for the server, whereas a single deep shallow clone of a merge-heavy history like Linux can time out. The clone is cached in `raw/`, which is not committed.
2. Reads the newest 3,000 non-merge commits.
3. Splits the subject prefix into `prefix` and `scope`, and keeps the rest as `message`.
4. Cleans the body:
   - moves `Assisted-by:` declarations into `assisted_by`;
   - removes other trailer lines (Signed-off-by, Reviewed-by, Cc, Link, Fixes and similar), backport and maintainer notes, and PyTorch's ghstack boilerplate;
   - replaces email addresses with `<email>`.

Author names are never collected. Both histories move daily, so re-running with `--refresh` produces a different snapshot.

## Things to know

- **Coverage differs.** Almost every Linux commit has a prefix. Only just over half of PyTorch's do. The workshop's label check ignores unlabelled rows, but PyTorch has fewer labelled examples to work with.
- **The two conventions mean different things.** Linux prefixes are subsystem paths. PyTorch tags mix components (`dynamo`, `inductor`, `mps`) with process tags (`be`, `ci`, `test`). A "scope" in one repo is not quite the same kind of label as in the other.
- **Some PyTorch scopes are batches or bots.** `torchcomms hash update` commits are automated and near-identical. `testcase refactoring` is a large batch of similar test-suite changes. Both form tight, trivial clusters that flatter any score, so leave them out for a fair test.
- **Linux prefixes nest.** Both `drm/mediatek:` and `drm/amd/display:` become scope `drm`, and subjects like `net: dsa: ...` keep the rest of the prefix in `message`. That gives the model some help.
- **Release commits have no scope.** "Linux 7.3-rc6" is a release tag, not a change.
- **Never embed `subject` if you're evaluating against `scope`.** The answer is written at the start of it.
- **Bodies are long.** The embedding model reads only roughly the first 200 words, which for a commit body is usually the useful part.
- **Body cleaning is best-effort.** It's pattern-based, so the odd trailer or handle may survive.
- **The Linux clone is much bigger than the sample.** Its merge structure pulls in whole branches, so the cached clone ends up holding over half a million commits. It's messages only and it isn't committed, but expect `raw/` to take up some space.

## Quick look

```python
import pandas as pd

df = pd.read_csv("data/git_log/git_log.csv")
print(df.groupby("repo").size())
print(df[df["repo"] == "linux"]["scope"].value_counts().head(15))
print(df[df["repo"] == "pytorch"]["scope"].value_counts().head(15))
print(df["scope"].isna().groupby(df["repo"]).mean())        # share with no prefix
print(df["assisted_by"].notna().groupby(df["repo"]).sum())  # commits declaring AI assistance
```

## Using it with the workshop notebooks

In the CSV notebook:

```python
CSV_PATH = "../data/git_log/git_log.csv"
FIELDS = ["message"]
LABEL_FIELD = "scope"
FILTER = ("scope", {"drm", "xfs", "bpf", "kvm", "bluetooth", "iio"})
DEDUPE = False
OUTPUT_DIR = "../outputs/git_log"
```

Then open `03_explore.ipynb` with `DATASET_DIR = "../outputs/git_log"`, and set `N_CLUSTERS` to the number of scopes you kept (6 above).

Some useful scope sets:

| Set | Scopes | Why |
|---|---|---|
| Linux, distinct | drm, xfs, bpf, kvm, bluetooth, iio | Different subsystems with different vocabularies. Should score well |
| Linux, overlapping | net, wifi, bluetooth | All networking. Expect confusion |
| Linux, near-twins | asoc, alsa | Both audio. Can the model separate them at all? |
| PyTorch, components | dynamo, inductor, mps, rocm, distributed | A fair PyTorch test, with bots and batches excluded |

To try your own repository instead, use `01_embed_git_log.ipynb` and point `REPO_PATH` at it.

## Suggested tasks

### Starter

1. **Semantic search.** Try "memory leak", "fix race condition", "performance regression", "update documentation" and "add tests". Which repo and which scopes do the results come from?
2. **Rediscover the subsystems.** Use the "Linux, distinct" set and check the adjusted Rand index and crosstab. Then try "Linux, overlapping". How much does the score drop, and which pairs get confused?
3. **Linux or PyTorch?** Set `LABEL_FIELD = "repo"`, `FILTER = None` and `N_CLUSTERS = 2`. Can the clusters separate the two projects? If so, is it topic, vocabulary or writing style?

### Intermediate

4. **Leakage demo.** Re-run with `FIELDS = ["subject"]`, so the prefix is included. Watch the score jump, and explain why that number is meaningless.
5. **Subject vs body.** Embed `body` instead of `message`, filtering out empty bodies first. Does the longer, more explanatory text recover the scope better or worse than the one-line subject?
6. **Fill in the missing labels.** Nearly half of PyTorch's commits have no scope. For commits where you *do* know the answer, how often does a vote among the nearest labelled neighbours guess it correctly? Then apply it to the unlabelled ones and eyeball the results.
7. **Bots and batches.** Include `torchcomms hash update` and `testcase refactoring` in the PyTorch filter. How tight are those clusters, and how much do they inflate the score?

### Stretch

8. **What kind of change?** Commits vary by subsystem and also by kind of change: fix, add, remove, refactor, revert. Which axis dominates the embedding space? Can you find a direction that separates fixes from features?
9. **Two conventions, one space.** Do Linux `net` commits land near PyTorch `distributed` commits? Where do shared concepts cross project boundaries?
10. **AI-assisted commits.** How many commits declare AI assistance in `assisted_by`, and which tools do they name? Do those commits differ in subsystem, body length or wording? Keep it descriptive: the declaration is a transparency practice, not a quality signal.
11. **Your own history.** Run `01_embed_git_log.ipynb` on a repository of your own. How do your commit messages compare? Would a prefix convention help you or your team?

### Discussion prompts

- Prefix conventions are free labels that someone has to keep writing. What other "free labels" are hiding in data you already have?
- Why does a held-out label have to be truly held out? Where else does this kind of leakage sneak in?
- Developers are starting to declare AI assistance in commit messages. What would you want such a declaration to tell you?

## Source and licence

- Linux kernel: https://github.com/torvalds/linux (GPL-2.0)
- PyTorch: https://github.com/pytorch/pytorch (BSD-style licence)

Commit messages remain subject to each project's licence. This file is a small derived sample for educational use. Author names, email addresses, sign-off trailers and maintainer notes were removed as described above.

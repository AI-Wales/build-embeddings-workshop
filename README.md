# AI Wales: Embeddings workshop

Hands-on notebooks for exploring text and image embeddings: semantic search, clustering, 2D projections and community discovery, using real Welsh and open-source data. Part of the AI Wales technical meetup series.

Everything runs locally on your laptop. Models are downloaded once and run on the CPU, and no data is sent anywhere. Bring your own data if you like: it never leaves your machine.

## Quick start

You need Python 3.10 or newer, git and make.

```bash
git clone https://github.com/AI-Wales/embeddings-workshop
cd embeddings-workshop
python3 -m venv venv
source venv/bin/activate
make install
make run
```

`make run` opens JupyterLab in your browser. Start with `notebooks/02_embed_csv.ipynb`.

On Windows, `make` isn't available by default. Activate the environment with `venv\Scripts\activate`, then run `pip install -r requirements.txt`, `nbstripout --install` and `jupyter lab .` instead.

**Please install before the workshop.** `make install` downloads PyTorch (a few hundred MB), and the first notebook run downloads the embedding model (about 90 MB). Venue wifi won't thank us for all doing that at once.

## What's in the repo

```
data/
  laramee2026/   open bank transactions (MoneyData)
  senedd/        Senedd committee transcripts
  git_log/       Linux kernel and PyTorch commit messages
notebooks/
  02_embed_csv.ipynb       embed one of the datasets above, by name
  03_explore.ipynb         search, cluster, project and explore embeddings
  04_embed_images.ipynb    embed a folder of photos with CLIP
  presets.py               the dataset presets used by 02
  loaders.py               helpers for reading data
outputs/                   embeddings written by the notebooks (not committed)
```

Each data folder has its own README with a description, citation, licence and suggested tasks. It also holds the script that built the data and a small `sample.csv` to look at.

## How it works

1. **Embed.** Set `DATASET` at the top of `02_embed_csv.ipynb` and run it. It loads the data, turns each row's text into a vector with `all-MiniLM-L6-v2`, and saves the results to `outputs/<DATASET>/`.
2. **Explore.** Set the same `DATASET` in `03_explore.ipynb` and run it cell by cell:
   - **Semantic search:** find rows by meaning, not keywords.
   - **Clustering:** group similar rows, and check the groups against a known label.
   - **Projections:** PCA and t-SNE maps of the embedding space.
   - **Community discovery:** let a similarity graph find its own groups, summarised as a table and a tree.

## Datasets

| `DATASET` | What | Ground-truth label | Licence |
|---|---|---|---|
| `transactions` | 6,567 anonymised UK bank transactions, 2015-2022 | `Category` | CC BY 4.0 |
| `senedd` | Welsh Parliament committee transcripts, split into short passages | `committee` | Open Government Licence v3.0 |
| `git_linux` | Linux kernel commit messages | `scope` (subsystem) | GPL-2.0 |
| `git_pytorch` | PyTorch commit messages | `scope` (component) | BSD-style |

Each label is held out: it is never embedded, so the notebooks can test whether the embeddings rediscover it.

## Bring your own data

- **A CSV:** add an entry to `notebooks/presets.py` with the file path, the column(s) to embed, an optional label column and an optional filter. Then use its name as `DATASET`.
- **A git repository:** `01_embed_git_log.ipynb` embeds the commit history of any local repo.
- **Photos:** `04_embed_images.ipynb` embeds a folder of images with CLIP, so you can search them with text.

Your data stays on your machine. `outputs/` is not committed. Please never commit personal data to this repo.

## Tips

- **Slow on your laptop?** Lower `MAX_ROWS` in `02_embed_csv.ipynb`. t-SNE in particular takes a minute or more on a few thousand rows.
- **Edited `presets.py`?** Re-run the cell that loads it.
- **Edited `loaders.py`?** Restart the kernel (Kernel > Restart Kernel), then run from the top.
- **Notebook outputs showing up in git diffs?** `make install` sets up `nbstripout`, which strips outputs on commit. If you cloned before that was in place, run `nbstripout --install` once.

## Contributing

Ideas, fixes and new datasets are welcome as pull requests. Each data README has a list of suggested tasks, several of them marked as good first PRs.

## Data credits

- **MoneyData:** Firat, Vytla, Vasudeva Singh, Jiang and Laramee, "MoneyVis: Open Bank Transaction Data for Visualization and Beyond", EuroVis 2023 Short Papers, https://doi.org/10.2312/evs.20231052
- **Senedd transcripts:** Welsh Parliament, Record of Proceedings. Contains public sector information licensed under the Open Government Licence v3.0.
- **Commit messages:** the Linux kernel and PyTorch projects, under their respective licences.

Full citations and licence details are in each dataset's README.

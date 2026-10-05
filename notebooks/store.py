import json
from pathlib import Path
import numpy as np


def load_embeddings(in_dir):
    in_dir = Path(in_dir)
    embeddings = np.load(in_dir / "embeddings.npy")
    metadata = json.loads((in_dir / "metadata.json").read_text())
    manifest = json.loads((in_dir / "manifest.json").read_text())
    return embeddings, metadata, manifest

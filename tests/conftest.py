import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lakehouse_gov.runner import LocalLakehouse  # noqa: E402


@pytest.fixture(scope="session")
def dataset(tmp_path_factory):
    out = tmp_path_factory.mktemp("data")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_synthetic_data.py"), "--out", str(out), "--seed", "7"], check=True)
    return out, json.loads((out / "manifest.json").read_text())["expected"]


@pytest.fixture()
def lakehouse(dataset):
    data_dir, _ = dataset
    lh = LocalLakehouse()
    lh.build(data_dir)
    return lh

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
META = ROOT / "data" / "metadata.csv"
SPLITS = ROOT / "data" / "splits.csv"
FIGURES = ROOT / "reports" / "figures"

SEED = 42
CLASSES = ["CNV", "DME", "DRUSEN", "NORMAL"]

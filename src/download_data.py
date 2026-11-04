"""Скачивание Retinal OCT (Kermany, Mendeley Data v3) в data/raw/OCT."""
import hashlib
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import config

URL = ("https://data.mendeley.com/public-files/datasets/rscbjbr9sj/files/"
       "810b2ce2-11c3-4424-996e-3bef36600907/file_downloaded")
SHA256 = "acbc42869440eec719361942d0ba560f132742230262f22e78bfb93eb5ea4563"
ZIP = config.DATA_RAW / "ZhangLabData.zip"
PREFIX = "CellData/OCT/"
EXPECTED = {"train": 108309, "test": 1000}


def download():
    part = ZIP.with_suffix(".part")
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r, open(part, "wb") as f:
        total = int(r.headers.get("Content-Length", 0))
        with tqdm(total=total, unit="B", unit_scale=True, desc="download") as bar:
            while chunk := r.read(1 << 20):
                f.write(chunk)
                bar.update(len(chunk))
    part.rename(ZIP)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def extract():
    with zipfile.ZipFile(ZIP) as z:
        members = [m for m in z.namelist() if m.startswith(PREFIX)]
        for m in tqdm(members, desc="unzip"):
            z.extract(m, config.DATA_RAW)
    (config.DATA_RAW / "CellData" / "OCT").rename(config.DATA_OCT)
    shutil.rmtree(config.DATA_RAW / "CellData")


def check():
    ok = True
    for split, n in EXPECTED.items():
        got = sum(1 for _ in (config.DATA_OCT / split).glob("*/*.jpeg"))
        print(f"{split}: {got} (ожидалось {n})", "OK" if got == n else "MISMATCH")
        ok &= got == n
    return ok


def main():
    if config.DATA_OCT.exists():
        print("Данные уже есть:", config.DATA_OCT)
    else:
        config.DATA_RAW.mkdir(parents=True, exist_ok=True)
        if not ZIP.exists():
            download()
        print("Проверка SHA-256...")
        if sha256(ZIP) != SHA256:
            sys.exit(f"Хеш не совпал. Удалите {ZIP} и запустите снова.")
        extract()
        ZIP.unlink()
    sys.exit(0 if check() else 1)


if __name__ == "__main__":
    main()

"""Скачивание и очистка датасета Kermany OCT2017 с Kaggle.

Запуск из корня репозитория:  python src/download_data.py
Нужна переменная окружения KAGGLE_API_TOKEN (секрет Colab).
"""
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import DATA_RAW

DATASET = "paultimothymooney/kermany2018"
EXPECTED = {"train": 83484, "test": 968, "val": 32}
TARGET = DATA_RAW / "OCT2017"


def files(root):
    return {p.relative_to(root): p.stat().st_size for p in root.rglob("*.jpeg")}


def main():
    if TARGET.exists():
        print(f"Датасет уже есть: {TARGET}")
    else:
        DATA_RAW.mkdir(parents=True, exist_ok=True)
        subprocess.run(["kaggle", "datasets", "download", "-d", DATASET,
                        "-p", str(DATA_RAW), "--unzip"], check=True)

        main_dir = DATA_RAW / "OCT2017 "
        copy_dir = DATA_RAW / "oct2017" / "OCT2017 "
        if copy_dir.exists():
            assert files(main_dir) == files(copy_dir), "Копия отличается, удалять нельзя"
            shutil.rmtree(DATA_RAW / "oct2017")
            print("Удалена дублирующая копия oct2017/ и __MACOSX")
        main_dir.rename(TARGET)

    counts = {s: sum(1 for _ in (TARGET / s).rglob("*.jpeg")) for s in EXPECTED}
    print("Снимков:", counts, "всего", sum(counts.values()))
    assert counts == EXPECTED, f"Ожидалось {EXPECTED}"
    print("OK")


if __name__ == "__main__":
    main()

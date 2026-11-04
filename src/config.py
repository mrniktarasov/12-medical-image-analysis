"""
Общие настройки проекта: пути к данным, seed и список классов.

Использование:
    from src import config
    config.DATA_OCT   # папка со снимками

Все пути строятся от корня репозитория, поэтому одинаково работают
локально (Windows, Linux) и в Colab.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]      # корень репозитория
DATA_RAW = ROOT / "data" / "raw"                # сырые данные (не хранятся в git)
DATA_OCT = DATA_RAW / "OCT"                     # снимки: OCT/{train,test}/{класс}/*.jpeg
META = ROOT / "data" / "metadata.csv"           # таблица всех снимков (хранится в git)
SPLITS = ROOT / "data" / "splits.csv"           # разбиение train/val/test (хранится в git)
HASHES = ROOT / "data" / "hashes.csv"           # MD5 и phash снимков (кэш, не хранится в git)
FIGURES = ROOT / "reports" / "figures"          # графики для отчёта

SEED = 42                                       # единый seed для воспроизводимости
CLASSES = ["CNV", "DME", "DRUSEN", "NORMAL"]    # классы в алфавитном порядке

"""
Скачивание набора Retinal OCT (Kermany et al., Mendeley Data v3) в data/raw/OCT.

Запуск из корня репозитория:
    uv run python src/download_data.py

Что делает скрипт:
1. Скачивает архив ZhangLabData.zip (8,4 ГБ) с Mendeley Data.
   При обрыве связи продолжает загрузку с места остановки.
2. Проверяет размер и контрольную сумму SHA-256 архива.
3. Распаковывает только папку CellData/OCT (рентгены грудной клетки из архива пропускаются).
4. Переносит её в data/raw/OCT и удаляет архив.
5. Сверяет число снимков: train 108 309, test 1 000.

Если data/raw/OCT уже существует, скачивание пропускается и выполняется только шаг 5.
Код возврата: 0 — числа снимков совпали, 1 — не совпали.
Нужно около 20 ГБ свободного места.
"""
import hashlib
import shutil
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

from tqdm import tqdm

# Добавляем корень репозитория в путь поиска, чтобы `from src import config`
# работал при запуске скрипта из терминала.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import config  # noqa: E402

# Прямая ссылка на ZhangLabData.zip со страницы https://data.mendeley.com/datasets/rscbjbr9sj/3
URL = ("https://data.mendeley.com/public-files/datasets/rscbjbr9sj/files/"
       "810b2ce2-11c3-4424-996e-3bef36600907/file_downloaded")
SIZE = 8_441_154_111                           # размер архива в байтах
SHA256 = "acbc42869440eec719361942d0ba560f132742230262f22e78bfb93eb5ea4563"
ZIP = config.DATA_RAW / "ZhangLabData.zip"
PART = ZIP.with_suffix(".part")                # недокачанный архив
PREFIX = "CellData/OCT/"                       # распаковываем только эту папку архива
EXPECTED = {"train": 108309, "test": 1000}     # ожидаемое число снимков по выборкам
CHUNK = 1 << 20                                # читаем и пишем частями по 1 МБ
ATTEMPTS = 30                                  # сколько раз переподключаться при обрыве


def part_size() -> int:
    """
    Возвращает, сколько байт архива уже скачано (размер файла .part).
    Если файла ещё нет, возвращает 0.
    """
    return PART.stat().st_size if PART.exists() else 0


def download() -> None:
    """
    Скачивает архив в ZIP с полосой прогресса и докачкой.

    Данные пишутся во временный файл ZhangLabData.part. При обрыве связи
    скрипт ждёт 10 с и продолжает с места остановки (HTTP-заголовок Range),
    до ATTEMPTS попыток. Файл переименовывается в .zip, только когда его
    размер равен SIZE, поэтому недокачанный архив не будет принят за готовый.
    Если все попытки исчерпаны, скрипт завершается с ошибкой; при повторном
    запуске загрузка продолжится.
    """
    for attempt in range(1, ATTEMPTS + 1):
        done = part_size()
        if done == SIZE:
            break
        # User-Agent нужен, иначе Mendeley может отклонить запрос
        headers = {"User-Agent": "Mozilla/5.0"}
        if done:
            headers["Range"] = f"bytes={done}-"    # просим файл с позиции done
        try:
            req = urllib.request.Request(URL, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as r:
                if done and r.status != 206:        # сервер не поддержал докачку:
                    done = 0                        # пишем файл заново
                with open(PART, "ab" if done else "wb") as f, \
                        tqdm(total=SIZE, initial=done, unit="B", unit_scale=True,
                             desc="download") as bar:
                    while chunk := r.read(CHUNK):
                        f.write(chunk)
                        bar.update(len(chunk))
        except OSError as e:                        # обрыв связи, таймаут и т. п.
            print(f"Ошибка сети: {e}")
        if part_size() < SIZE:
            print(f"Соединение оборвалось (попытка {attempt}), докачиваю через 10 с...")
            time.sleep(10)
    if part_size() != SIZE:
        sys.exit("Не удалось скачать архив. Запустите скрипт ещё раз — загрузка продолжится.")
    PART.rename(ZIP)


def sha256(path: Path) -> str:
    """
    Вычисляет контрольную сумму SHA-256 файла.
    path — путь к файлу
    Возвращает хеш в виде hex-строки (64 символа).
    Файл читается частями по 1 МБ, поэтому 8 ГБ не загружаются в память целиком.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def extract() -> None:
    """
    Распаковывает из архива только CellData/OCT и переносит её в config.DATA_OCT.
    После переноса пустая папка CellData удаляется.
    """
    with zipfile.ZipFile(ZIP) as z:
        members = [m for m in z.namelist() if m.startswith(PREFIX)]
        for m in tqdm(members, desc="unzip"):
            z.extract(m, config.DATA_RAW)
    move_dir(config.DATA_RAW / "CellData" / "OCT", config.DATA_OCT)
    shutil.rmtree(config.DATA_RAW / "CellData")


def move_dir(src: Path, dst: Path) -> None:
    """
    Переименовывает папку src в dst, повторяя попытку при отказе в доступе.
    src — исходная папка
    dst — новое имя папки
    В Windows антивирус какое-то время проверяет только что распакованные
    файлы и не даёт переименовать папку (PermissionError, WinError 5).
    Поэтому пробуем до 60 раз с паузой 5 с (до 5 минут).
    """
    for attempt in range(60):
        try:
            src.rename(dst)
            return
        except PermissionError:
            if attempt == 0:
                print("Папка занята (вероятно, антивирус проверяет файлы), жду...")
            time.sleep(5)
    sys.exit(f"Не удалось переименовать {src} в {dst}. Переименуйте вручную и запустите снова.")


def check() -> bool:
    """
    Сверяет число снимков .jpeg в train и test с EXPECTED.
    Печатает результат по каждой выборке.
    Возвращает True, если все числа совпали.
    """
    ok = True
    for split, n in EXPECTED.items():
        got = sum(1 for _ in (config.DATA_OCT / split).glob("*/*.jpeg"))
        print(f"{split}: {got} (ожидалось {n})", "OK" if got == n else "MISMATCH")
        ok &= got == n
    return ok


def main() -> None:
    """
    Скачивает, проверяет и распаковывает данные.
    Если данные уже есть, только сверяет число снимков.
    Завершает скрипт с кодом 0 (всё совпало) или 1 (есть расхождения).
    """
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
        ZIP.unlink()                           # архив больше не нужен, освобождаем 8 ГБ
    sys.exit(0 if check() else 1)


if __name__ == "__main__":
    main()

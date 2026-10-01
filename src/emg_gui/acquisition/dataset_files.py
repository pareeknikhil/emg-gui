import glob
import os
import random
from pathlib import Path

_CSV_PATH = Path("data/csv")


def get_all_labels(selected_type="train") -> list[str]:  # Default from train
    train_path = os.path.join(_CSV_PATH, selected_type)
    return os.listdir(path=train_path)


def get_all_files(pattern: str, shuffle_flag: bool) -> list[str]:
    files = glob.glob(pattern)

    if shuffle_flag:
        random.shuffle(files)

    return files

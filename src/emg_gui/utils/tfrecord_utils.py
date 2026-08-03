import os
import glob
import random
from pathlib import Path

csv_path = Path("data/csv")


def get_all_labels(selected_type="train") -> list[str]:  ## default from train
    train_path = os.path.join(csv_path, selected_type)
    return os.listdir(path=train_path)


def get_all_files(pattern: str, shuffle_flag: bool) -> list[str]:
    files = glob.glob(pattern)

    if shuffle_flag:
        random.shuffle(files)

    return files

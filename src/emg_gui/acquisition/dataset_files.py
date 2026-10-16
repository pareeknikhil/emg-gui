import glob
import os
import random
from importlib.resources import files


def get_all_labels(selected_type: str = "train") -> list[str]:  # Default from train
    train_path = files("emg_gui.data.csv").joinpath(selected_type)
    return os.listdir(path=str(train_path))


def get_all_files(pattern: str, shuffle_flag: bool) -> list[str]:
    files = glob.glob(pattern)

    if shuffle_flag:
        random.shuffle(files)

    return files

import numpy as np


def get_hann_window(window_size, skew=True) -> np.ndarray:
    hann = np.hanning(window_size)
    if skew:
        skew_factor = np.linspace(0, 10, window_size)
        skewed_window = hann * np.exp(skew_factor - 2)
        hann /= np.max(skewed_window)
    return hann

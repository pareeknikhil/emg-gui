import numpy as np
from pyrr import Matrix44


def get_hann_window(window_size, skew=True) -> np.ndarray:
    hann = np.hanning(window_size)
    if skew:
        skew_factor = np.linspace(0, 10, window_size)
        skewed_window = hann * np.exp(skew_factor - 2)
        hann /= np.max(skewed_window)
    return hann


def orthographic(w, h) -> Matrix44:
    P = Matrix44.orthogonal_projection(0, w, h, 0, -1, 1, dtype="f4")
    return P

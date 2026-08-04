import copy

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
from brainflow.data_filter import (AggOperations, DataFilter, FilterTypes,
                                   NoiseTypes)
from matplotlib import cm

df = pd.read_csv(
    filepath_or_buffer="data/csv/train/stretch/file_1752595795.csv",
    names=[
        "channel_1",
        "channel_2",
        "channel_3",
        "channel_4",
        "channel_5",
        "channel_6",
        "channel_7",
        "channel_8",
    ],
    delimiter="\t",
)

# df.channel_1.plot(kind='line')
# plt.show()

N = 1000
window_size, spec_window, stride = (
    125,
    100,
    1,
)  # refine this logic, take 1700 or less to filter, then further subdived for 100 spec windows


def stride_window(a, window_size, stride):
    n_windows = ((len(a) - window_size) // stride) + 1
    return np.lib.stride_tricks.as_strided(
        a, shape=(n_windows, window_size), strides=(a.strides[0] * stride, a.strides[0])
    )


fig, axes = plt.subplots(8, 1, figsize=(16, 20))


def filter_fn(data):
    DataFilter.perform_rolling_filter(data, 3, AggOperations.MEAN.value)
    DataFilter.perform_bandstop(
        data=data,
        sampling_rate=250,
        start_freq=58.0,
        stop_freq=62.0,
        order=4,
        filter_type=FilterTypes.BUTTERWORTH,
        ripple=1.0,
    )
    DataFilter.perform_bandpass(
        data=data,
        sampling_rate=250,
        start_freq=10.0,
        stop_freq=125.0,
        order=4,
        filter_type=FilterTypes.BUTTERWORTH,
        ripple=1.0,
    )
    DataFilter.remove_environmental_noise(
        data=data, sampling_rate=250, noise_type=NoiseTypes.FIFTY.value
    )
    DataFilter.remove_environmental_noise(
        data=data, sampling_rate=250, noise_type=NoiseTypes.SIXTY.value
    )
    return data


for i in range(8):
    channel_idx = i + 1
    np_data = df[f"channel_{channel_idx}"].values
    filter_window = filter_fn(copy.deepcopy(np_data[1500 : 1500 + N]))
    last_n_data = copy.deepcopy(filter_window)[250 : 250 + window_size]
    windows = stride_window(copy.deepcopy(last_n_data), spec_window, stride)

    hann = tf.signal.hann_window(spec_window, periodic=True)
    hann = hann / 142
    with_hann = copy.deepcopy(windows) * hann
    tf_with_hann = tf.convert_to_tensor(with_hann, dtype=tf.float32)

    stft_with_hann = tf.signal.rfft(tf_with_hann)

    mag_with_hann = tf.abs(stft_with_hann)
    power_with_hann = tf.math.square(mag_with_hann)
    power_with_hann = tf.cast(power_with_hann, tf.float32)
    log_with_hann = (
        10.0 * tf.math.log(tf.maximum(power_with_hann, 1e-10)) / tf.math.log(10.0)
    )
    log_with_hann = tf.maximum(log_with_hann, tf.reduce_max(log_with_hann) - 80.0)

    min_db = -5
    max_db = 10
    slices = tf.clip_by_value(log_with_hann, min_db, max_db)

    slices = (slices - min_db) / (max_db - min_db)

    slices = slices.numpy()

    COLOR_MAP = cm.get_cmap(name="inferno")
    slices = COLOR_MAP(slices)
    slices = (slices * 255).astype("u1")
    slices = slices[:, :, :3]
    slices = np.transpose(slices, (1, 0, 2))
    print(slices.shape)

    im1 = axes[channel_idx - 1].imshow(slices, aspect="auto", origin="lower")

    # im1 = axes[channel_idx-1].imshow(slices.T, aspect='auto', origin='lower', cmap='inferno')

plt.tight_layout()
plt.show()

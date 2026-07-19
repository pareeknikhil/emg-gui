import copy

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
from brainflow.data_filter import (AggOperations, DataFilter, FilterTypes,
                                   NoiseTypes)

# df = pd.read_csv(filepath_or_buffer='data/csv/test/relax/file_1752101443.csv', names=['channel_1', 'channel_2', 'channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8'], delimiter='\t')

# df = pd.read_csv(filepath_or_buffer='data/csv/train/bottom_fist/file_1751068095.csv', names=['channel_1', 'channel_2', 'channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8'], delimiter='\t')
# df = pd.read_csv(filepath_or_buffer='data/csv/train/bottom_stretch/file_1751064610.csv', names=['channel_1', 'channel_2', 'channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8'], delimiter='\t')
# df = pd.read_csv(filepath_or_buffer='data/csv/train/finger_one/file_1751065014.csv', names=['channel_1', 'channel_2', 'channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8'], delimiter='\t')
# df = pd.read_csv(filepath_or_buffer='data/csv/train/finger_one_two/file_1751065309.csv', names=['channel_1', 'channel_2', 'channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8'], delimiter='\t')
# df = pd.read_csv(filepath_or_buffer='data/csv/train/finger_two/file_1751065556.csv', names=['channel_1', 'channel_2', 'channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8'], delimiter='\t')
# df = pd.read_csv(filepath_or_buffer='data/csv/train/fist/file_1751065837.csv', names=['channel_1', 'channel_2', 'channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8'], delimiter='\t')
# df = pd.read_csv(filepath_or_buffer='data/csv/train/left/file_1751066223.csv', names=['channel_1', 'channel_2', 'channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8'], delimiter='\t')
df = pd.read_csv(filepath_or_buffer='data/csv/train/relax/file_1751064544.csv', names=['channel_1', 'channel_2', 'channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8'], delimiter='\t')
# df = pd.read_csv(filepath_or_buffer='data/csv/train/right/file_1751166386.csv', names=['channel_1', 'channel_2', 'channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8'], delimiter='\t')
# df = pd.read_csv(filepath_or_buffer='data/csv/train/top_fist/file_1751066811.csv', names=['channel_1', 'channel_2', 'channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8'], delimiter='\t')
# df = pd.read_csv(filepath_or_buffer='data/csv/train/top_stretch/file_1751067208.csv', names=['channel_1', 'channel_2', 'channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8'], delimiter='\t')

# df.channel_1.plot(kind='line')
# plt.show()

N = 7000
window_size, stride = 250, 20

def stride_window(a, window_size, stride):
    n_windows = ((len(a)-window_size) // stride) + 1
    return np.lib.stride_tricks.as_strided(a, shape=(n_windows, window_size), strides=(a.strides[0] * stride, a.strides[0]))


fig, axes = plt.subplots(8, 1, figsize=(16, 20))

def filter_fn(data):
    DataFilter.perform_rolling_filter(data, 3, AggOperations.MEAN.value)
    DataFilter.perform_bandstop(data=data, sampling_rate=250, start_freq=58.0, stop_freq=62.0,
                                        order=4, filter_type=FilterTypes.BUTTERWORTH, ripple=1.0)
    DataFilter.perform_bandpass(data=data, sampling_rate=250, start_freq=10.0, stop_freq=125.0,
                                            order=4, filter_type=FilterTypes.BUTTERWORTH, ripple=1.0)
    DataFilter.remove_environmental_noise(data=data, sampling_rate=250, noise_type=NoiseTypes.FIFTY.value)
    DataFilter.remove_environmental_noise(data=data, sampling_rate=250, noise_type=NoiseTypes.SIXTY.value)
    return data


for i in range(8):
    channel_idx = i + 1
    np_data = df[f"channel_{channel_idx}"].values
    windows = stride_window(copy.deepcopy(np_data[:N]), window_size, stride)

    # filter_no_scale = np.array([filter_fn(w) for w in copy.deepcopy(windows)])
    filter_data = np.array([filter_fn(w) for w in copy.deepcopy(windows)])
    mean = np.mean(copy.deepcopy(filter_data), axis=1, keepdims=True)
    std = np.std(copy.deepcopy(filter_data), axis=1, keepdims=True)
    filter_with_scale = (copy.deepcopy(filter_data)-mean)/(std + 1e-8)

    hann = np.hanning(2*window_size)          # create double-length hann
    skewed_window = hann[:window_size]           # take the rising part (right half)
    skewed_window /= skewed_window.max()

    no_hann = copy.deepcopy(filter_with_scale)
    with_hann = copy.deepcopy(filter_with_scale)*skewed_window


    tf_no_hann = tf.convert_to_tensor(no_hann, dtype=tf.float32)
    tf_with_hann = tf.convert_to_tensor(with_hann, dtype=tf.float32)

    stft_no_hann = tf.signal.rfft(tf_no_hann)
    mag_no_hann = tf.abs(stft_no_hann)
    power_no_hann = tf.math.square(mag_no_hann)
    log_no_hann = 10.0 * tf.math.log(tf.maximum(power_no_hann, 1e-10)) / tf.math.log(10.0)
    log_no_hann = tf.maximum(log_no_hann, tf.reduce_max(log_no_hann) - 80.0)

    stft_with_hann = tf.signal.rfft(tf_with_hann)
    mag_with_hann = tf.abs(stft_with_hann)
    power_with_hann = tf.math.square(mag_with_hann)
    log_with_hann = 10.0 * tf.math.log(tf.maximum(power_with_hann, 1e-10)) / tf.math.log(10.0)
    log_with_hann = tf.maximum(log_with_hann, tf.reduce_max(log_with_hann) - 80.0)

    min_db = -5
    max_db = 10
    # log_no_hann = log_no_hann.numpy().clip(min_db, max_db)
    # log_no_hann = (log_no_hann-min_db) / (max_db-min_db)

    log_with_hann = log_with_hann.numpy().clip(min_db, max_db)
    log_with_hann = (log_with_hann-min_db) / (max_db-min_db)

    # Plot 1: without Hann
    # im0 = axes[channel_idx-1].imshow(log_no_hann.T, aspect='auto', origin='lower', cmap='inferno')
    # axes[channel_idx-1].set_title("Without Hann Window")
    # axes[channel_idx-1].set_xlabel("Time frames")
    # axes[channel_idx-1].set_ylabel("Frequency bins")
    # fig.colorbar(im0, ax=axes[channel_idx-1])

    # # Plot 2: with Hann
    im1 = axes[channel_idx-1].imshow(log_with_hann.T, aspect='auto', origin='lower', cmap='inferno')
    # axes[channel_idx-1].set_title("With Hann Window")
    # axes[channel_idx-1].set_xlabel("Time frames")
    # axes[channel_idx-1].set_ylabel("Frequency bins")
    # fig.colorbar(im1, ax=axes[channel_idx-1])

plt.tight_layout()
plt.show()
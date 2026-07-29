import copy

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
from brainflow.data_filter import (AggOperations, DataFilter, FilterTypes,
                                   NoiseTypes)

df = pd.read_csv(filepath_or_buffer='data/csv/train/bottom_fist/file_1751064209.csv', names=['channel_1', 'channel_2', 'channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8'], delimiter='\t')
df = pd.read_csv(filepath_or_buffer='data/csv/train/relax/file_1751064544.csv', names=['channel_1', 'channel_2', 'channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8'], delimiter='\t')
# df = pd.read_csv(filepath_or_buffer='data/csv/train/fist/file_1751065837.csv', names=['channel_1', 'channel_2', 'channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8'], delimiter='\t')
# df = pd.read_csv(filepath_or_buffer='data/csv/train/right/file_1751166386.csv', names=['channel_1', 'channel_2', 'channel_3', 'channel_4', 'channel_5', 'channel_6', 'channel_7', 'channel_8'], delimiter='\t')
# df.channel_1.plot(kind='line')
# plt.show()

# fig, axes = plt.subplots(3, 1, figsize=(10, 6), sharex=True)

np_data = df.channel_3.values

N = 7000

data_no_scale = copy.deepcopy(np_data[:N])
# axes[0].plot(data_no_scale)

filter_no_scale = copy.deepcopy(data_no_scale)
DataFilter.perform_rolling_filter(filter_no_scale, 3, AggOperations.MEAN.value)
DataFilter.perform_bandstop(data=filter_no_scale, sampling_rate=250, start_freq=58.0, stop_freq=62.0,
                                    order=4, filter_type=FilterTypes.BUTTERWORTH, ripple=1.0)
DataFilter.perform_bandpass(data=filter_no_scale, sampling_rate=250, start_freq=5.0, stop_freq=125.0,
                                        order=4, filter_type=FilterTypes.BUTTERWORTH, ripple=1.0)
DataFilter.remove_environmental_noise(data=filter_no_scale, sampling_rate=250, noise_type=NoiseTypes.FIFTY.value)
DataFilter.remove_environmental_noise(data=filter_no_scale, sampling_rate=250, noise_type=NoiseTypes.SIXTY.value)
# axes[1].plot(filter_no_scale)


data_with_scale = copy.deepcopy(np_data[:N])
mean = np.mean(data_with_scale, axis=0)
std = np.std(data_with_scale, axis=0)
filter_with_scale = (copy.deepcopy(data_with_scale)-mean)/(std + 1e-8)
DataFilter.perform_rolling_filter(filter_with_scale, 3, AggOperations.MEAN.value)
DataFilter.perform_bandstop(data=filter_with_scale, sampling_rate=250, start_freq=58.0, stop_freq=62.0,
                                    order=4, filter_type=FilterTypes.BUTTERWORTH, ripple=1.0)
DataFilter.perform_bandpass(data=filter_with_scale, sampling_rate=250, start_freq=5.0, stop_freq=125.0,
                                        order=4, filter_type=FilterTypes.BUTTERWORTH, ripple=1.0)
DataFilter.remove_environmental_noise(data=filter_with_scale, sampling_rate=250, noise_type=NoiseTypes.FIFTY.value)
DataFilter.remove_environmental_noise(data=filter_with_scale, sampling_rate=250, noise_type=NoiseTypes.SIXTY.value)
# axes[2].plot(filter_with_scale)

# plt.tight_layout()
# plt.show()


window_size, stride = 250, 5

def stride_window(a, window_size, stride):
    n_windows = (len(a)-window_size) // stride + 1
    return np.lib.stride_tricks.as_strided(a, shape=(n_windows, window_size), strides=(a.strides[0] * stride, a.strides[0]))

window_no_scale = stride_window(filter_no_scale, window_size, stride)
window_with_scale = stride_window(filter_with_scale, window_size, stride)


hann = np.hanning(2*window_size)          # create double-length hann
skewed_window = hann[:window_size]           # take the rising part (right half)
skewed_window /= skewed_window.max()

no_hann = copy.deepcopy(window_with_scale)
with_hann = copy.deepcopy(window_with_scale)*skewed_window


tf_no_hann = tf.convert_to_tensor(no_hann, dtype=tf.float32)
tf_with_hann = tf.convert_to_tensor(with_hann, dtype=tf.float32)

stft_no_hann = tf.signal.rfft(tf_no_hann)
mag_no_hann = tf.abs(stft_no_hann)
log_no_hann = 10.0 * tf.math.log(mag_no_hann) / tf.math.log(10.0)
log_no_hann = tf.maximum(log_no_hann, tf.reduce_max(log_no_hann) - 80.0)
stft_with_hann = tf.signal.rfft(tf_with_hann)
mag_with_hann = tf.abs(stft_with_hann)
log_with_hann = 10.0 * tf.math.log(mag_with_hann) / tf.math.log(10.0)
log_with_hann = tf.maximum(log_with_hann, tf.reduce_max(log_with_hann) - 80.0)

# log_spectrogram_no_hann = tf.math.log(mag_no_hann + 1e-8)
# log_spectrogram_with_hann = tf.math.log(mag_with_hann + 1e-8)

min_db = -5
max_db = 10
log_no_hann = log_no_hann.numpy().clip(-5, 10)
log_no_hann = (log_no_hann-min_db) / (max_db-min_db)

log_with_hann = log_with_hann.numpy().clip(-5, 10)
log_with_hann = (log_with_hann-min_db) / (max_db-min_db)


fig, axes = plt.subplots(2, 1, figsize=(16, 4))  # 1 row, 2 columns

# Plot 1: with Hann
im0 = axes[0].imshow(log_no_hann.T, aspect='auto', origin='lower', cmap='inferno')
axes[0].set_title("Without Hann Window")
axes[0].set_xlabel("Time frames")
axes[0].set_ylabel("Frequency bins")
fig.colorbar(im0, ax=axes[0], label="Log Magnitude")

# Plot 2: without Hann
im1 = axes[1].imshow(log_with_hann.T, aspect='auto', origin='lower', cmap='inferno')
axes[1].set_title("With Hann Window")
axes[1].set_xlabel("Time frames")
axes[1].set_ylabel("Frequency bins")
fig.colorbar(im1, ax=axes[1], label="Log Magnitude")

plt.tight_layout()
plt.show()
from brainflow.board_shim import BoardIds, BoardShim
from brainflow.data_filter import (AggOperations, DataFilter, FilterTypes,
                                   NoiseTypes)

from emg_gui.config.constants import IS_SYNTHETIC_BOARD
from emg_gui.core.types import EMGArray

BOARDID = BoardIds.SYNTHETIC_BOARD if IS_SYNTHETIC_BOARD else BoardIds.CYTON_BOARD


def filter_data(time_series: EMGArray) -> None:

    DataFilter.perform_rolling_filter(time_series, 3, AggOperations.MEAN.value)

    DataFilter.perform_bandstop(
        data=time_series,
        sampling_rate=BoardShim.get_sampling_rate(BOARDID),
        start_freq=58.0,
        stop_freq=62.0,
        order=4,
        filter_type=FilterTypes.BUTTERWORTH,
        ripple=1.0,
    )

    DataFilter.perform_bandpass(
        data=time_series,
        sampling_rate=BoardShim.get_sampling_rate(BOARDID),
        start_freq=10.0,
        stop_freq=125.0,
        order=4,
        filter_type=FilterTypes.BUTTERWORTH,
        ripple=1.0,
    )

    DataFilter.remove_environmental_noise(
        data=time_series,
        sampling_rate=BoardShim.get_sampling_rate(BOARDID),
        noise_type=NoiseTypes.FIFTY.value,
    )

    DataFilter.remove_environmental_noise(
        data=time_series,
        sampling_rate=BoardShim.get_sampling_rate(BOARDID),
        noise_type=NoiseTypes.SIXTY.value,
    )

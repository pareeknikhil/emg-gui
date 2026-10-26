from brainflow.data_filter import DataFilter  # type: ignore[import-untyped]
from brainflow.data_filter import FilterTypes

from emg_gui.core.types import EMGArray


def filter_data(time_series: EMGArray, sampling_rate: int, noise_type: int) -> None:

    DataFilter.perform_bandpass(
        data=time_series,
        sampling_rate=sampling_rate,
        start_freq=10.0,
        stop_freq=float(sampling_rate/2),  # Nyquist frequency
        order=4,
        filter_type=FilterTypes.BUTTERWORTH,
        ripple=1.0,
    )

    DataFilter.remove_environmental_noise(
        data=time_series,
        sampling_rate=sampling_rate,
        noise_type=noise_type,
    )

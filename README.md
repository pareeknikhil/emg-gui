<h1 align="center">
  <img src="https://raw.githubusercontent.com/pareeknikhil/emg-gui/main/docs/diagrams/ability-logo.svg" alt="Ability logomark" height="160">
  <br>
  EMG-GUI
  <br>
  <a href="https://pypi.org/project/emg-gui/"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/emg-gui?logo=python&amp;logoColor=FFE873&amp;v=2"></a>
  <a href="https://pypi.org/project/emg-gui/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/emg-gui"></a>
  <a href="https://pepy.tech/project/emg-gui"><img alt="Monthly PyPI downloads" src="https://api.pepy.tech/personalized-badge/emg-gui?period=MONTH&amp;units=INTERNATIONAL_SYSTEM&amp;left_color=GREY&amp;right_color=BLUE&amp;left_text=pypi%20downloads%2Fmonth"></a>
  <a href="https://pepy.tech/project/emg-gui"><img alt="Total PyPI downloads" src="https://api.pepy.tech/personalized-badge/emg-gui?period=TOTAL&amp;units=INTERNATIONAL_SYSTEM&amp;left_color=GREY&amp;right_color=BLUE&amp;left_text=pypi%20downloads"></a>
  <a href="https://github.com/pareeknikhil/emg-gui/releases"><img alt="GitHub release downloads" src="https://badgen.net/github/assets-dl/pareeknikhil/emg-gui/total?label=github%20downloads&amp;color=yellow"></a>
</h1>

<p align="center">
  <em>Real-time acquisition and visualization of OpenBCI EMG signals with Python.</em>
</p>

EMG-GUI is a multithreaded [Python package](https://pypi.org/project/emg-gui/) built with BrainFlow, Qt, and
ModernGL. It displays raw and filtered EMG traces from OpenBCI boards alongside
a live spectrogram, with support for recording and playback.

## Contents

- [Installation](#1-installation)
- [Practical Examples](#2-practical-examples)
- [Configuration](#configuration)
- [Recording and Markers](#recording-and-markers)
- [API Reference](#api-reference)
- [Architecture](#3-architecture)
- [Contributing](#4-contributing)
- [Planned Features](CONTRIBUTING.md#planned-features)
- [Tech Debt](CONTRIBUTING.md#5-tech-debt)
- [Acknowledgements](#5-acknowledgements)
- [Videos](#videos)

## 1. Installation

**Requirement:** Python 3.9, 3.10, 3.11, 3.12, 3.13, or 3.14.

Choose your operating system and follow the steps in order.

<details>
<summary><strong>🍎 macOS</strong></summary>

1. **Install EMG-GUI:**

   ```bash
   pip install emg-gui
   ```

2. **Serial OpenBCI boards only — set `serial_port` in your script's `OpenBCIConfig`.**
   Use the board's `/dev/cu.*` device path. BrainFlow does not support
   `/dev/tty.*` device paths on macOS.

</details>

<details>
<summary><strong>🪟 Windows</strong></summary>

1. **Install EMG-GUI in PowerShell:**

   ```powershell
   pip install emg-gui
   ```

2. **Serial OpenBCI boards only — set `serial_port` in your script's `OpenBCIConfig`.**
   Use the board's assigned port name, such as `COM3`.

</details>

<details open>
<summary><strong>🐧 Linux — Ubuntu / Debian</strong></summary>

1. **Install the system dependencies.** For Debian and Ubuntu:

   ```bash
   sudo apt update
   sudo apt install \
     libgl-dev \
     libegl-dev \
     libxcb-icccm4 \
     libxcb-keysyms1 \
     libxcb-xinerama0 \
     libxcb-xkb1 \
     libxkbcommon-x11-0
   ```

2. **Install EMG-GUI:**

   ```bash
   pip install emg-gui
   ```

3. **Serial OpenBCI boards only — configure port access.** Debian and
   Ubuntu users can join the `dialout` group, then sign out and back in for the
   change to take effect:

   ```bash
   sudo usermod -aG dialout "$USER"
   ```

   Set `serial_port` in your `OpenBCIConfig` in your script to the board's device
   path, such as `/dev/ttyUSB0` or `/dev/ttyACM0`.

</details>

<br>

> **Graphics troubleshooting:** If the application reports an OpenGL context
> error, check that your graphics driver provides OpenGL 3.3 or later.

## 2. Practical Examples

Each script opens raw and filtered EMG traces alongside a live spectrogram.
Run it with Python, then click **Stream Data** to begin. Close the window to exit.

- [Synthetic data](#synthetic-data): try the interface without hardware.
- [OpenBCI Cyton](#openbci-cyton): connect a serial board.
- [Playback](#playback): view a bundled or personal recording.
- [Configuration](#configuration): board types, connection options, and mains frequency.
- [Recording and markers](#recording-and-markers): save signals and label movement intervals.
- [API reference](#api-reference): methods and properties for use in your own code.

### Synthetic data

[Source: examples/synthetic_board.py](examples/synthetic_board.py)

```python
from emg_gui import (
    ConsoleLogger, EMGVisualizerWindow, MainsFrequency,
    OpenBCIBoard, OpenBCIBoardType, OpenBCIConfig,
)


def main():
    logger = ConsoleLogger()
    board = None
    try:
        config = OpenBCIConfig(board_type=OpenBCIBoardType.SYNTHETIC)
        board = OpenBCIBoard(logger=logger, config=config)
        EMGVisualizerWindow.run(
            logger=logger, board=board, mains_frequency=MainsFrequency.FIFTY_HZ
        )
    finally:
        if board is not None:
            board.release()
        logger.release()


if __name__ == "__main__":
    main()
```

### OpenBCI Cyton

[Source: examples/cyton_board.py](examples/cyton_board.py)

Set `serial_port` to your board's port: for example, `/dev/ttyUSB0` on Linux,
`/dev/cu.usbserial-…` on macOS, or `COM3` on Windows. Ports are not detected automatically.

```python
from emg_gui import (
    ConsoleLogger, EMGVisualizerWindow, MainsFrequency,
    OpenBCIBoard, OpenBCIBoardType, OpenBCIConfig,
)


def main():
    logger = ConsoleLogger()
    board = None
    try:
        config = OpenBCIConfig(
            board_type=OpenBCIBoardType.CYTON_SERIAL,
            serial_port="/dev/ttyUSB0",
            polling_interval_ms=40,
            turn_off_srb=True,
        )
        board = OpenBCIBoard(logger=logger, config=config)
        EMGVisualizerWindow.run(
            logger=logger, board=board, mains_frequency=MainsFrequency.FIFTY_HZ
        )
    finally:
        if board is not None:
            board.release()
        logger.release()


if __name__ == "__main__":
    main()
```

### Playback

[Source: examples/playback_recording.py](examples/playback_recording.py)

No board connection is needed. Set `board_type` to the board used for the
recording; it determines the playback sampling rate. The bundled example uses `SYNTHETIC`.

```python
from importlib.resources import files

from emg_gui import (
    ConsoleLogger, EMGVisualizerWindow, MainsFrequency,
    OpenBCIBoardType, PlayBackConfig, PlaybackRecording,
)


def main():
    logger = ConsoleLogger()
    board = None
    try:
        recording = files("emg_gui.data") / "train" / "top_fist" / "file_1.csv"
        # For your own recording, use its path instead:
        # recording = "/home/user/recordings/session.csv"
        config = PlayBackConfig(
            board_type=OpenBCIBoardType.SYNTHETIC,
            file_path=str(recording),
            polling_interval_ms=40,
        )
        board = PlaybackRecording(logger=logger, config=config)
        EMGVisualizerWindow.run(
            logger=logger, board=board, mains_frequency=MainsFrequency.FIFTY_HZ
        )
    finally:
        if board is not None:
            board.release()
        logger.release()


if __name__ == "__main__":
    main()
```

**File format:** numeric, tab-separated rows without a header. Each row is one
sample; columns contain EMG channels followed by one marker column. Use zeros
in the marker column when there are no markers. Relative paths resolve from
your working directory. Playback outputs zeros after the last sample; stop and
restart streaming to replay from the beginning.

### Configuration

`OpenBCIConfig` and `PlayBackConfig` are immutable. Create a new configuration
and data-source instance to change their settings.

**`OpenBCIConfig`**

| Parameter                      | Default  | Purpose                                                                                                 |
| ------------------------------ | -------- | ------------------------------------------------------------------------------------------------------- |
| `board_type: OpenBCIBoardType` | Required | Select the board and its sampling rate/channel layout.                                                  |
| `polling_interval_ms: int`     | `40`     | Interval between data reads; does not change the board's sampling rate.                                 |
| `turn_off_srb: bool`           | `False`  | Send SRB-disabling channel commands for a compatible Cyton setup. Leave disabled for other board types. |
| `serial_port: str`             | `""`     | Serial device path or COM port.                                                                         |
| `ip_address: str`              | `""`     | Board/network address.                                                                                  |
| `ip_port: int`                 | `0`      | Network port.                                                                                           |
| `ip_protocol: int`             | `0`      | BrainFlow IP protocol value.                                                                            |
| `mac_address: str`             | `""`     | Device MAC address, when required.                                                                      |
| `serial_number: str`           | `""`     | Device serial number, when required.                                                                    |
| `timeout: int`                 | `0`      | BrainFlow discovery/connection timeout.                                                                 |
| `other_info: str`              | `""`     | Additional board-specific connection information.                                                       |

Connection fields are passed directly to BrainFlow. Supply the fields required
by your board's [connection instructions](https://brainflow.readthedocs.io/en/stable/SupportedBoards.html).

**`OpenBCIBoardType`**

| Connection       | Enum members                                            |
| ---------------- | ------------------------------------------------------- |
| Serial / dongle  | `CYTON_SERIAL`, `CYTON_DAISY_SERIAL`, `GANGLION_DONGLE` |
| Native Bluetooth | `GANGLION_NATIVE`                                       |
| Wi-Fi            | `CYTON_WIFI`, `CYTON_DAISY_WIFI`, `GANGLION_WIFI`       |
| Generated data   | `SYNTHETIC`                                             |

**`PlayBackConfig`**

| Parameter                      | Default  | Purpose                                                                    |
| ------------------------------ | -------- | -------------------------------------------------------------------------- |
| `board_type: OpenBCIBoardType` | Required | Board whose sampling rate matches the recording.                           |
| `file_path: str`               | `""`     | Path to the recording; supply an existing file.                            |
| `polling_interval_ms: int`     | `40`     | Playback read interval; samples per read follow the board's sampling rate. |

**`EMGVisualizerWindow.run(logger, board, mains_frequency)`**

Pass a `ConsoleLogger`, an `OpenBCIBoard` or `PlaybackRecording`, and either
`MainsFrequency.FIFTY_HZ` or `MainsFrequency.SIXTY_HZ` for mains-noise removal.
Use the enum members, not the numbers `50` or `60`. This call creates the Qt
application and blocks until the window closes. Run it on the main thread;
release the board and logger afterwards, as shown above.

### Recording and markers

For a live or synthetic board:

1. Click **Stream Data**, then choose a dataset split and label in the dropdowns.
2. Click **Record** to begin collecting raw EMG and marker samples.
3. Click **Start Movement** and **Stop Movement** to mark an activity interval.
4. Click **Recording** to stop and save, before stopping the stream or closing the window.

Files are saved relative to your working directory as
`data/<split>/<label>/<timestamp>__<label>.csv`. Create the destination directory
before saving; for example, for split `train` and label `top_fist`:

```python
from pathlib import Path

Path("data/train/top_fist").mkdir(parents=True, exist_ok=True)
```

Splits are `train`, `validate`, and `test`; label choices come from the bundled
dataset folders. Saved files contain raw signals and a final marker column,
not the filtered display traces. **Reset** clears the display buffer.
Playback supports viewing existing recordings; recording and saving during
playback are not implemented.

### API reference

The GUI handles these operations for you. Use them directly when acquiring
data without the window; avoid concurrent reads while the GUI is streaming.

| Method on `board`                                | Behavior                                                                                                                                |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| `start_stream()` / `stop_stream()`               | Start/stop acquisition or playback. Repeating the current state raises `RuntimeError`.                                                  |
| `get_data()`                                     | Return a NumPy array shaped `(EMG channels + 1, samples)`, with markers in the last row. Live reads consume available buffered samples. |
| `extract_emg_data(data)`                         | Return only the EMG rows.                                                                                                               |
| `start_recording()` / `stop_recording()`         | Enable/disable accumulation; these calls do not read samples or save a file.                                                            |
| `record(data)`                                   | Append a `get_data()` batch while recording is enabled. Call this on each read when working without the GUI.                            |
| `insert_start_marker()` / `insert_stop_marker()` | Mark movement start/end with `1.12345` / `2.12345`.                                                                                     |
| `write_to_csv(datasplit, folder)`                | Save accumulated batches to the directory described above and clear them. Requires collected data and an existing directory.            |
| `release()`                                      | Stop a live stream and release its board session.                                                                                       |

Recording and movement methods also raise `RuntimeError` on repeated
start/stop transitions. On `PlaybackRecording`, `record()`, `write_to_csv()`,
and `release()` do nothing; movement methods change state without editing file markers.

| Read-only property    | Meaning                                               |
| --------------------- | ----------------------------------------------------- |
| `emg_channel_count`   | Number of EMG channels, excluding the marker channel. |
| `sampling_rate`       | Board sampling rate in Hz.                            |
| `polling_interval_ms` | Configured interval between reads.                    |
| `is_streaming`        | Whether acquisition/playback is started.              |
| `is_recording`        | Whether recording is enabled.                         |
| `is_active`           | Whether a movement interval is active.                |

`ConsoleLogger()` provides `info(message)`, `error(message)`, and `release()`.
You may pass your own logger with these three methods. A custom data source
must provide the methods and properties listed above; see the
[DataSource contract](src/emg_gui/acquisition/data_source.py).

---

## 3. Architecture

See the [architecture guide](docs/architecture.md) for the component overview,
[directory layout](docs/architecture.md#directory-layout), data flow, and thread
interactions.

## 4. Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for the development and linting workflow,
[planned features](CONTRIBUTING.md#planned-features), and
[tech debt](CONTRIBUTING.md#5-tech-debt).

Report reproducible problems through
[GitHub Issues](https://github.com/pareeknikhil/emg-gui/issues), including your
operating system, Python and package versions, and the full error output.

---

## 5. Acknowledgements

### 4.1 BrainFlow

This project uses [BrainFlow](https://brainflow.readthedocs.io/en/stable/) for
biosignal acquisition and hardware integration. BrainFlow provides a uniform
API for acquiring, parsing, and analyzing EEG, EMG, ECG, and other biosensor
data across a wide range of supported boards, including OpenBCI devices.
BrainFlow is distributed under the
[MIT License](https://github.com/brainflow-dev/brainflow/blob/master/LICENSE).

### 4.2 ModernGL Spectrogram

This project uses
[nickcercone/spectrogram](https://github.com/nickcercone/spectrogram) as a
reference for parts of its ModernGL spectrogram rendering implementation. The
referenced project demonstrates real-time audio spectrogram visualization
using ModernGL and is distributed under the
[MIT License](https://github.com/nickcercone/spectrogram/blob/main/LICENCE).

### 4.3 Text Rendering

This project adapts the code in
[How to render text with PyOpenGL?](https://stackoverflow.com/questions/63836707/how-to-render-text-with-pyopengl)
by exiled (question) and Rabbid76 (answer) for its ModernGL text renderer.
The referenced contributions demonstrate text rendering with PyOpenGL and are
distributed under the
[CC BY-SA 4.0 License](https://creativecommons.org/licenses/by-sa/4.0/).

## Videos

Watch demos and tutorials on [EMGAbility on YouTube](https://www.youtube.com/@EMGAbility).

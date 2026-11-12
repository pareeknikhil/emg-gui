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

<p align="center">
  <img src="https://raw.githubusercontent.com/pareeknikhil/emg-gui/main/docs/diagrams/emg-preview.webp" alt="EMG-GUI displaying raw and filtered EMG traces alongside a live spectrogram" width="900">
</p>

## Contents

- [Installation](#1-installation)
- [Hello World with synthetic data](#2-hello-world-with-synthetic-data)
- [Features](#3-features)
- [Architecture](#4-how-emg-gui-works)
- [Contributing](#5-contributing)
- [Planned Features](CONTRIBUTING.md#planned-features)
- [Tech Debt](CONTRIBUTING.md#tech-debt)
- [Acknowledgements](#6-acknowledgements)
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

</details>

<details>
<summary><strong>🪟 Windows</strong></summary>

1. **Install EMG-GUI in PowerShell:**

   ```powershell
   pip install emg-gui
   ```

</details>

<details>
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

</details>

<br>

> **Graphics troubleshooting:** If the application reports an OpenGL context
> error, check that your graphics driver provides OpenGL 3.3 or later.

## 2. Hello world with synthetic data

Each script opens raw and filtered EMG traces alongside a live spectrogram.
Run it with Python, then click **Stream Data** to begin. Close the window to exit.

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

## 3. Features

| Explore and record                                                                                                                  | Design and integration                                                                                                                         |
| :---------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------- |
| **Live multichannel EMG.** Compare raw and filtered waveforms together on a shared per-channel scale.                               | **Automatic scaling and layout.** Waveforms scale automatically, and channel plots adapt to the window size.                                   |
| **Per-channel spectrograms.** Observe changing frequency content alongside each channel’s waveform.                                 | **GPU-accelerated rendering.** ModernGL renders waveforms, spectrograms, axes, and labels.                                                     |
| **Recording and movement markers.** Save raw EMG with movement start/stop markers in CSV format.                                    | **Python-configured desktop GUI.** Launch from your own script on Windows, macOS, or Linux.                        |
| **Playback and hardware-free demos.** Replay compatible recordings, explore bundled samples, or use synthetic data.                 | **Independent acquisition.** Sensor polling and raw-data recording run on a worker thread, separate from visualization.          |
| **OpenBCI support.** Configure Cyton, Cyton Daisy, or Ganglion, with channel counts and sampling rates taken from the selected board. | **Self-paced visualization.** Display the latest snapshot without queuing outdated frames or reprocessing unchanged snapshots while streaming. |


## 4. How EMG-GUI works

See the [architecture guide](docs/architecture.md) for the component overview,
[directory layout](docs/architecture.md#directory-layout), data flow, and thread
interactions.

## 5. Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for the development and linting workflow,
[planned features](CONTRIBUTING.md#planned-features), and
[tech debt](CONTRIBUTING.md#tech-debt).

Report reproducible problems through
[GitHub Issues](https://github.com/pareeknikhil/emg-gui/issues), including your
operating system, Python and package versions, and the full error output.

---

## 6. Acknowledgements

### 6.1 BrainFlow

This project uses [BrainFlow](https://brainflow.readthedocs.io/en/stable/) for
biosignal acquisition and hardware integration. BrainFlow provides a uniform
API for acquiring, parsing, and analyzing EEG, EMG, ECG, and other biosensor
data across a wide range of supported boards, including OpenBCI devices.
BrainFlow is distributed under the
[MIT License](https://github.com/brainflow-dev/brainflow/blob/master/LICENSE).

### 6.2 ModernGL Spectrogram

This project uses
[nickcercone/spectrogram](https://github.com/nickcercone/spectrogram) as a
reference for parts of its ModernGL spectrogram rendering implementation. The
referenced project demonstrates real-time audio spectrogram visualization
using ModernGL and is distributed under the
[MIT License](https://github.com/nickcercone/spectrogram/blob/main/LICENCE).

### 6.3 Text Rendering

This project adapts the code in
[How to render text with PyOpenGL?](https://stackoverflow.com/questions/63836707/how-to-render-text-with-pyopengl)
by exiled (question) and Rabbid76 (answer) for its ModernGL text renderer.
The referenced contributions demonstrate text rendering with PyOpenGL and are
distributed under the
[CC BY-SA 4.0 License](https://creativecommons.org/licenses/by-sa/4.0/).

## Videos

Watch demos and tutorials on [EMGAbility on YouTube](https://www.youtube.com/@EMGAbility).

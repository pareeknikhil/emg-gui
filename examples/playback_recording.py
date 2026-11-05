from importlib.resources import files

from emg_gui import (ConsoleLogger, EMGVisualizerWindow, MainsFrequency,
                     OpenBCIBoardType, PlayBackConfig, PlaybackRecording)


def main() -> None:
        logger = ConsoleLogger()

        # To play your own recording, replace the packaged example below with the
        # path to your CSV file, for example:
        # playback_file_location = "/home/user/recordings/session.csv"
        playback_file_location = files("emg_gui.data.csv").joinpath(
              "train",
              "top_fist",
              "file_1.csv",
        )
        playback_config = PlayBackConfig(board_type=OpenBCIBoardType.SYNTHETIC, file_path=str(playback_file_location), polling_interval_ms=40)
        board = PlaybackRecording(logger=logger, config=playback_config)

        try:
               EMGVisualizerWindow.run(logger=logger, board=board, mains_frequency=MainsFrequency.FIFTY_HZ)
        finally:
                board.release()
                logger.release()

if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()

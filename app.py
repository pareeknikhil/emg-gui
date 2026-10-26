from emg_gui import (ConsoleLogger, MainsFrequency, OpenBCIBoard,
                     OpenBCIBoardType, OpenBCIConfig, PlayBackConfig,
                     PlaybackRecording)
from emg_gui.ui.window import EMGVisualizerWindow


def main() -> None:
        logger = ConsoleLogger()

        config = OpenBCIConfig(board_type=OpenBCIBoardType.SYNTHETIC, serial_port= "/dev/ttyUSB0", polling_interval_ms=40, turn_off_srb=True)
        board = OpenBCIBoard(logger=logger, config=config)

        # playback_config = PlayBackConfig(board_type=OpenBCIBoardType.SYNTHETIC, file_path="data/csv/train/sample/1785181476__sample.csv", polling_interval_ms=40)
        # board = PlaybackRecording(logger, play_back_config)

        try:
               EMGVisualizerWindow.run(logger, board, MainsFrequency.FIFTY_HZ)
        finally:
                board.release()
                logger.release()

if __name__ == "__main__":
    main()

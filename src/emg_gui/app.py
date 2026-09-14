from emg_gui.acquisition.data_source import DataSource, OpenBCIBoard
from emg_gui.core.logger import ConsoleLogger, Logger
from emg_gui.ui.window import EMGVisualizerWindow


def main() -> None:
    logger: Logger = ConsoleLogger.get_instance()
    board: DataSource = OpenBCIBoard.get_instance(logger)
    # board: DataSource = PlaybackRecording.get_instance(logger, "data/csv/train/sample/1785181476__sample.csv")

    try:
        EMGVisualizerWindow.run(logger, board)
    finally:
        board.release()
        logger.release()

if __name__ == "__main__":
    main()

from emg_gui.utils.log_utils import Logger
from emg_gui.visualizer.data_source import DataSource, RealOpenBCI
from emg_gui.visualizer.window import EMGSignalAnalyzer


def main() -> None:
    logger = Logger.get_instance()
    cyton_board: DataSource = RealOpenBCI.get_instance(logger)
    EMGSignalAnalyzer.run(logger, cyton_board)

if __name__=="__main__":
    main()

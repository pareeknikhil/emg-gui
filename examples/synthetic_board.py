from emg_gui import (ConsoleLogger, EMGVisualizerWindow, MainsFrequency,
                     OpenBCIBoard, OpenBCIBoardType, OpenBCIConfig)


def main() -> None:
        logger = ConsoleLogger()

        config = OpenBCIConfig(board_type=OpenBCIBoardType.SYNTHETIC, polling_interval_ms=40)
        board = OpenBCIBoard(logger=logger, config=config)

        try:
               EMGVisualizerWindow.run(logger=logger, board=board, mains_frequency=MainsFrequency.FIFTY_HZ)
        finally:
                board.release()
                logger.release()

if __name__ == "__main__":
    main()

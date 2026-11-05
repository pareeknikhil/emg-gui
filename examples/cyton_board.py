from emg_gui import (
    ConsoleLogger,
    EMGVisualizerWindow,
    MainsFrequency,
    OpenBCIBoard,
    OpenBCIBoardType,
    OpenBCIConfig,
)


def main() -> None:
    logger = ConsoleLogger()

    config = OpenBCIConfig(
        board_type=OpenBCIBoardType.CYTON_SERIAL,
        serial_port="/dev/ttyUSB0",
        polling_interval_ms=40,
        turn_off_srb=True,
    )
    board = OpenBCIBoard(logger=logger, config=config)

    try:
        EMGVisualizerWindow.run(
            logger=logger, board=board, mains_frequency=MainsFrequency.FIFTY_HZ
        )
    finally:
        board.release()
        logger.release()


if __name__ == "__main__":
    main()

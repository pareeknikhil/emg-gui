import logging
from typing import Protocol


class Logger(Protocol):
    def info(self, message: str) -> None: ...

    def error(self, message: str) -> None: ...

    def release(self) -> None: ...


class ConsoleLogger:
    _instance = None

    @classmethod
    def get_instance(cls) -> Logger:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self._logger = logging.getLogger("emg-gui")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        if not self._logger.handlers:
            self._logger.addHandler(ConsoleLogger._get_handler())

    def info(self, message: str) -> None:
        self._logger.info(msg=message)

    def error(self, message: str) -> None:
        self._logger.error(msg=message)

    def release(self) -> None:
        handlers = self._logger.handlers[:]
        for handler in handlers:
            self._logger.removeHandler(handler)
            handler.close()
        ConsoleLogger._instance = None
        print("Logger resources released successfully.")

    @staticmethod
    def _get_handler() -> logging.StreamHandler:
        handler = logging.StreamHandler()
        _format = "%(asctime)s - %(levelname)s - %(filename)s - %(message)s"
        _formatter = logging.Formatter(_format)
        handler.setFormatter(_formatter)
        return handler

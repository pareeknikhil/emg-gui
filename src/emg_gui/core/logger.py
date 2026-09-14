import logging
from typing import Protocol


class Logger(Protocol):
    def info(self, message: str) -> None: ...

    def error(self, message: str) -> None: ...

    def release(self) -> None: ...


class ConsoleLogger:
    __instance = None

    @classmethod
    def get_instance(cls) -> Logger:
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def __init__(self) -> None:
        self.logger = logging.getLogger("emg-gui")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if not self.logger.handlers:
            self.logger.addHandler(ConsoleLogger._get_handler())

    def info(self, message: str) -> None:
        self.logger.info(msg=message)

    def error(self, message: str) -> None:
        self.logger.error(msg=message)

    def release(self) -> None:
        handlers = self.logger.handlers[:]
        for handler in handlers:
            self.logger.removeHandler(handler)
            handler.close()
        ConsoleLogger.__instance = None
        print("Logger resources released successfully.")

    @staticmethod
    def _get_handler() -> logging.StreamHandler:
        handler = logging.StreamHandler()
        _format = "%(asctime)s - %(levelname)s - %(filename)s - %(message)s"
        _formatter = logging.Formatter(_format)
        handler.setFormatter(_formatter)
        return handler

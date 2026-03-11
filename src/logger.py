import logging
import sys
from typing import Optional


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class Logger:
    _instance: Optional['Logger'] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is not None:
            return
        self._logger = logging.getLogger('color_img')
        self._logger.setLevel(logging.DEBUG)
        self._logger.handlers = []
        self._console_handler: Optional[logging.StreamHandler] = None
        self._file_handler: Optional[logging.FileHandler] = None

    def setup(
        self,
        level: str = 'INFO',
        log_file: Optional[str] = None,
        console_output: bool = True,
        log_format: Optional[str] = None
    ) -> None:
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
        }
        log_level = level_map.get(level.upper(), logging.INFO)
        self._logger.setLevel(log_level)

        if log_format is None:
            log_format = '%(asctime)s | %(levelname)-8s | %(message)s'
            date_format = '%Y-%m-%d %H:%M:%S'
        else:
            date_format = '%Y-%m-%d %H:%M:%S'

        if console_output:
            if self._console_handler:
                self._logger.removeHandler(self._console_handler)
            self._console_handler = logging.StreamHandler(sys.stdout)
            self._console_handler.setLevel(log_level)
            colored_formatter = ColoredFormatter(log_format, datefmt=date_format)
            self._console_handler.setFormatter(colored_formatter)
            self._logger.addHandler(self._console_handler)

        if log_file:
            if self._file_handler:
                self._logger.removeHandler(self._file_handler)
            self._file_handler = logging.FileHandler(log_file, encoding='utf-8')
            self._file_handler.setLevel(log_level)
            file_formatter = logging.Formatter(log_format, datefmt=date_format)
            self._file_handler.setFormatter(file_formatter)
            self._logger.addHandler(self._file_handler)

    def debug(self, message: str) -> None:
        self._logger.debug(message)

    def info(self, message: str) -> None:
        self._logger.info(message)

    def warning(self, message: str) -> None:
        self._logger.warning(message)

    def error(self, message: str) -> None:
        self._logger.error(message)


_logger_instance: Optional[Logger] = None


def get_logger() -> Logger:
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    return _logger_instance


def setup_logger(
    level: str = 'INFO',
    log_file: Optional[str] = None,
    console_output: bool = True,
    log_format: Optional[str] = None
) -> Logger:
    logger = get_logger()
    logger.setup(level=level, log_file=log_file, console_output=console_output, log_format=log_format)
    return logger


def debug(message: str) -> None:
    get_logger().debug(message)


def info(message: str) -> None:
    get_logger().info(message)


def warning(message: str) -> None:
    get_logger().warning(message)


def error(message: str) -> None:
    get_logger().error(message)

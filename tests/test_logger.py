import pytest
import logging
from io import StringIO
from unittest.mock import patch, MagicMock

from src.logger import (
    ColoredFormatter,
    Logger,
    setup_logger,
    get_logger,
    debug,
    info,
    warning,
    error,
)


class TestColoredFormatter:
    def test_format_debug(self):
        formatter = ColoredFormatter('%(levelname)s %(message)s')
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=1,
            msg="debug message",
            args=(),
            exc_info=None
        )
        result = formatter.format(record)
        assert "debug message" in result
        assert "DEBUG" in result

    def test_format_info(self):
        formatter = ColoredFormatter('%(levelname)s %(message)s')
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="info message",
            args=(),
            exc_info=None
        )
        result = formatter.format(record)
        assert "info message" in result
        assert "INFO" in result

    def test_format_warning(self):
        formatter = ColoredFormatter('%(levelname)s %(message)s')
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="warning message",
            args=(),
            exc_info=None
        )
        result = formatter.format(record)
        assert "warning message" in result
        assert "WARNING" in result

    def test_format_error(self):
        formatter = ColoredFormatter('%(levelname)s %(message)s')
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="error message",
            args=(),
            exc_info=None
        )
        result = formatter.format(record)
        assert "error message" in result
        assert "ERROR" in result


class TestLogger:
    def test_logger_singleton(self):
        logger1 = Logger()
        logger2 = Logger()
        assert logger1 is logger2

    def test_logger_default_level(self):
        logger = Logger()
        assert logger._logger.level == logging.DEBUG

    def test_logger_setup_level(self):
        logger = Logger()
        logger.setup(level="INFO")
        assert logger._logger.level == logging.INFO

    def test_logger_setup_level_case_insensitive(self):
        logger = Logger()
        logger.setup(level="warning")
        assert logger._logger.level == logging.WARNING

    def test_logger_setup_invalid_level(self):
        logger = Logger()
        logger.setup(level="INVALID")
        assert logger._logger.level == logging.INFO

    def test_logger_debug(self, caplog):
        logger = Logger()
        logger.setup(level="DEBUG")
        with caplog.at_level(logging.DEBUG):
            logger.debug("test debug")
        assert any("test debug" in record.message for record in caplog.records)

    def test_logger_info(self, caplog):
        logger = Logger()
        logger.setup(level="INFO")
        with caplog.at_level(logging.INFO):
            logger.info("test info")
        assert any("test info" in record.message for record in caplog.records)

    def test_logger_warning(self, caplog):
        logger = Logger()
        logger.setup(level="WARNING")
        with caplog.at_level(logging.WARNING):
            logger.warning("test warning")
        assert any("test warning" in record.message for record in caplog.records)

    def test_logger_error(self, caplog):
        logger = Logger()
        logger.setup(level="ERROR")
        with caplog.at_level(logging.ERROR):
            logger.error("test error")
        assert any("test error" in record.message for record in caplog.records)


class TestSetupLogger:
    def test_setup_logger_default(self):
        logger = setup_logger()
        assert logger is not None

    def test_setup_logger_with_level(self):
        logger = setup_logger(level="DEBUG")
        assert logger._logger.level == logging.DEBUG

    def test_setup_logger_with_file(self, tmp_path):
        log_file = tmp_path / "test.log"
        logger = setup_logger(level="DEBUG", log_file=str(log_file))
        logger.info("test message")
        assert log_file.exists()


class TestModuleFunctions:
    def test_get_logger(self):
        logger = get_logger()
        assert logger is not None
        assert isinstance(logger, Logger)

    def test_get_logger_singleton(self):
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2

    def test_debug_function(self, caplog):
        setup_logger(level="DEBUG")
        with caplog.at_level(logging.DEBUG):
            debug("test debug")
        assert any("test debug" in record.message for record in caplog.records)

    def test_info_function(self, caplog):
        setup_logger(level="INFO")
        with caplog.at_level(logging.INFO):
            info("test info")
        assert any("test info" in record.message for record in caplog.records)

    def test_warning_function(self, caplog):
        setup_logger(level="WARNING")
        with caplog.at_level(logging.WARNING):
            warning("test warning")
        assert any("test warning" in record.message for record in caplog.records)

    def test_error_function(self, caplog):
        setup_logger(level="ERROR")
        with caplog.at_level(logging.ERROR):
            error("test error")
        assert any("test error" in record.message for record in caplog.records)

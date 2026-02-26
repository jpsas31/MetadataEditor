from src.logging_config import setup_logging


class TestLoggingConfig:
    def test_setup_logging_returns_logger(self):
        logger = setup_logging("test_module")
        assert logger is not None
        assert logger.name == "test_module"

    def test_setup_logging_with_custom_file(self, tmp_path):
        custom_log = tmp_path / "test.log"
        logger = setup_logging("test_module", str(custom_log))
        assert logger is not None
        assert logger.name == "test_module"

    def test_setup_logging_default_file(self):
        logger = setup_logging("test_default")
        assert logger is not None
        assert logger.name == "test_default"

    def test_setup_logging_multiple_calls(self):
        logger1 = setup_logging("module1")
        logger2 = setup_logging("module2")
        assert logger1.name == "module1"
        assert logger2.name == "module2"

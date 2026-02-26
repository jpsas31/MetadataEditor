import logging


def setup_logging(name: str, log_file: str = "/tmp/metadata_editor_debug.log") -> logging.Logger:
    """Setup logging configuration and return a logger."""
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filemode="w",
    )

    return logging.getLogger(name)

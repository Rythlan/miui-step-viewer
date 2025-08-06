# logger.py
import sys
import logging

def setup_logger():
    """Sets up a logger that prints to the console."""
    log = logging.getLogger("MIUI_Steps_Explorer")
    log.setLevel(logging.INFO)

    # Avoid adding duplicate handlers if this function is called multiple times
    if not log.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        log.addHandler(handler)

    return log

log = setup_logger()

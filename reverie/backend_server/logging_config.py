import logging
import os
from datetime import datetime

def setup_logging(log_dir="logs", log_level=logging.INFO):
    """
    Configures the logging system.
    
    Args:
        log_dir (str): Directory to save log files.
        log_level (int): Logging level (e.g., logging.INFO, logging.DEBUG).
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = os.path.join(log_dir, f"reverie_{timestamp}.log")

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )

    logging.info(f"Logging initialized. Saving logs to {log_filename}")

def get_logger(name):
    """
    Returns a logger instance with the specified name.
    """
    return logging.getLogger(name)

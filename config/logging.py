import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def setup_logger():
    current_time = datetime.now().strftime("%Y-%m-%d-%H")
    log_filename = os.path.join(LOG_DIR, f"{current_time}.log")
    debug_log_filename = os.path.join(LOG_DIR, f"{current_time}.debug.log")

    # Main logger configuration
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Handler for INFO and ERROR logs
    info_handler = TimedRotatingFileHandler(log_filename, when="H", interval=1, backupCount=24)
    info_handler.setLevel(logging.INFO)
    info_formatter = logging.Formatter(log_format, datefmt=date_format)
    info_handler.setFormatter(info_formatter)
    
    # Handler for DEBUG logs
    debug_handler = TimedRotatingFileHandler(debug_log_filename, when="H", interval=1, backupCount=24)
    debug_handler.setLevel(logging.DEBUG)
    debug_formatter = logging.Formatter(log_format, datefmt=date_format)
    debug_handler.setFormatter(debug_formatter)
    
    # Console handler for INFO and ERROR logs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(log_format, datefmt=date_format)
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(info_handler)
    logger.addHandler(debug_handler)
    logger.addHandler(console_handler)

    # Redirect logs from httpx and werkzeug to debug_handler only
    httpx_logger = logging.getLogger('httpx')
    httpx_logger.setLevel(logging.DEBUG)
    httpx_logger.addHandler(debug_handler)
    httpx_logger.propagate = False

    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.DEBUG)
    werkzeug_logger.addHandler(debug_handler)
    werkzeug_logger.propagate = False

    return logger

logger = setup_logger()

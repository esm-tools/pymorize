import warnings

import prefect
from loguru import logger
from rich.logging import RichHandler

logger.remove()

# Set up logging
showwarning_ = warnings.showwarning


def showwarning(message, *args, **kwargs):
    logger.warning(message)
    # showwarning_(message, *args, **kwargs)


warnings.showwarning = showwarning


# Function to forward loguru logs to Prefect logger if available
def loguru_to_prefect(message):
    try:
        # Try to get Prefect logger
        prefect_logger = prefect.context.get("logger")
        level = message.record["level"].name
        msg = message.record["message"]

        # Forward loguru logs to Prefect logger based on level
        if level == "DEBUG":
            prefect_logger.debug(msg)
        elif level == "INFO":
            prefect_logger.info(msg)
        elif level == "WARNING":
            prefect_logger.warning(msg)
        elif level == "ERROR":
            prefect_logger.error(msg)
        elif level == "CRITICAL":
            prefect_logger.critical(msg)
    except (KeyError, AttributeError):
        # If no Prefect logger is found, fallback to regular loguru log
        pass


# Add the Prefect logger as a sink for Loguru, with a try-except fallback
logger.add(loguru_to_prefect)

# Configure loguru with a rich handler for general logging
logger.configure(handlers=[{"sink": RichHandler(), "format": "{message}"}])

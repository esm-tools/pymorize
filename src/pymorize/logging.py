import warnings

from loguru import logger
from rich.logging import RichHandler

logger.remove()

# Set up logging
showwarning_ = warnings.showwarning


def showwarning(message, *args, **kwargs):
    logger.warning(message)
    # showwarning_(message, *args, **kwargs)


warnings.showwarning = showwarning

logger.configure(handlers=[{"sink": RichHandler(), "format": "{message}"}])

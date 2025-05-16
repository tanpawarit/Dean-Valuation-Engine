import logging

logger = logging.getLogger("alchemist")
if len(logger.handlers) > 0:
    logger.handlers = []
logger.setLevel(logging.INFO)
fomatter = logging.Formatter(
    "[%(asctime)s][%(levelname)s|%(filename)s:%(lineno)s] > %(message)s"
)
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(fomatter)
logger.addHandler(streamHandler)
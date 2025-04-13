import logging
import sys
from infrastructure.clients import db

def setup_logger(name=__name__, level=logging.INFO, toFile=False, fileName="spurly_log.log"):
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger
    
    logger.setLevel(level)
    formatter = logging.Formatter("[%(asctime)s] - %(name)s %(levelname)s %(message)s")
    if toFile:
        fileHandler = logging.FileHandler(fileName)
        fileHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)

    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)
    
    return logger

def get_logger(name=__name__):
    return logging.getLogger(name) 
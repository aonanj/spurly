import logging
from services.clients import db

def setup_logger(name=__name__, level=logging.INFO, toFile=False, fileName="spurly_log.log"):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if toFile:
        handler = logging.FileHandler(fileName)
    else:
        handler = logging.StreamHandler()

    if logger.hasHandlers():
        return logger
    
    formatter = logging.Formatter("[%(asctime)s] - %(name)s %(levelname)s %(message)s")
    if toFile:
        doc_ref = db.collection("logs").document(fileName)
        fileHandler = logging.FileHandler(doc_ref)
        fileHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)

    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)
    
    return logger

def get_logger(name=__name__):
    return logging.getLogger(name) 
import adafruit_logging as logging
import storage

__all__ = [
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
    "LogLevels",
    "LoggerDependencies",
    "newLogger",
]

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

class LoggerDependencies:
    def __init__(self,  matrix_portal):
        self.matrix_portal = matrix_portal

# xxx doc
# 
# Ideally I would also log with the RotatingFileHandler which provides very nice
# rotating log files
# https://github.com/adafruit/Adafruit_CircuitPython_Logging/blob/24c00a78a6ee6a41a87a8675e75742f990f1ee94/adafruit_logging.py#L325
# There have been some cases where I have seen issues happen on the board but
# haven't really sure why and without access to the logs it was difficult to
# debug. Unfortunately CircuitPython currently only allows file system access either from the connected USB or 
# 
# it requires reconfiguring the device so we can't
# write to it from the computer anymore.
# https://learn.adafruit.com/circuitpython-essentials/circuitpython-storage
#
# I gave this a try and got an error

class LogLevels:
    def __init__(self, aio_handler, print_handler, file_handler):
        self.aio_handler = aio_handler
        self.print_handler = print_handler
        self.file_handler= file_handler

# xxx now that I am logging to the filesystem too I should try to cut down on
# the amount of unneeded data that I log or add a log level for debug+more

def newLogger( dependencies: LoggerDependencies, log_levels: LogLevels):

    # xxx doc set the log level of the logger to be the min of all the handlers
    # so we only log what the different handlers need.
    logger_level = min(log_levels.aio_handler, log_levels.print_handler)

    logger = logging.getLogger('')
    logger.setLevel(logger_level)

    aio_handler = AIOHandler(dependencies.matrix_portal, "cmf-train-board-logging", log_levels.aio_handler)
    logger.addHandler(aio_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_levels.print_handler)
    logger.addHandler(stream_handler)

    # xxx doc only if FS isn't readonly
    fs = storage.getmount("/")
    if not fs.readonly:
        file_handler = logging.RotatingFileHandler("/log.log", maxBytes = 524288, backupCount=2)
        file_handler.setLevel(log_levels.file_handler)
        logger.addHandler(file_handler)

    logger.debug("logging initialized")
    return logger

# xxx doc
class AIOHandler(logging.Handler):
    def __init__(self, matrix_portal, feed_name, level: int):
        super().__init__(level)
        self._feed_name = feed_name
        self._matrix_portal = matrix_portal

    def emit(self, record):
        try:
            self._matrix_portal.push_to_io(self._feed_name, self.format(record))
        except Exception as e:
            print(f"Failed to push logs to adafruit.io: ${e}")

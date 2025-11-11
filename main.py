import os
import board

from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_datetime import datetime,timedelta

import logging
from train_predictor import TrainPredictor, TrainPredictorDependencies
from time_conversion import TimeConversion, TimeConversionDependencies
from display import Display, DisplayDependencies
from application import Application, ApplicationDependencies

matrix_portal = MatrixPortal(status_neopixel=board.NEOPIXEL)

log_levels = logging.LogLevels(aio_handler=logging.INFO, print_handler=logging.DEBUG)
logger = logging.newLogger(logging.LoggerDependencies(matrix_portal), log_levels)

mbta_api_key = os.getenv("MBTA_API_KEY")
if mbta_api_key is None:
    logger.error("missing MBTA API key")
    raise KeyError("missing MBTA API key")

# xxx doc where these numbers come from
train_predictor = TrainPredictor(TrainPredictorDependencies(matrix_portal.network, datetime, timedelta, datetime.now, mbta_api_key), 
    trainWarningSeconds=60,
    inboundOffsetAverageSeconds=-63, inboundOffsetStdDevSeconds=9,
    outboundOffsetAverageSeconds=93, outboundOffsetStdDevSeconds=9)

time_conversion = TimeConversion(TimeConversionDependencies(datetime.now))
display = Display(DisplayDependencies(matrix_portal, time_conversion, logger), text_scroll_delay=0.1, train_frame_duration=0.08)

app = Application(ApplicationDependencies(matrix_portal, train_predictor, time_conversion, display, datetime.now, logger))

app.run()
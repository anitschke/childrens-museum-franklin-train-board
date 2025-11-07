from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_datetime import datetime,timedelta

import logging
from train_predictor import TrainPredictor, TrainPredictorDependencies
from time_conversion import TimeConversion, TimeConversionDependencies
from display import Display, DisplayDependencies
from application import Application, ApplicationDependencies

#xxx remove unused imports


# xxx doc The esp32-s3 comes with a co-processor for handling HTTP requests. So
# ideally we would send out the HTTP request to get updated arrival times and
# have the co-processor wait for the response. While we are waiting for the
# response the main processor can continue doing other tasks like animating the
# board. The idea here is that I could use async / await along with asyncio
# python library to do cooperative multitasking (
# https://learn.adafruit.com/cooperative-multitasking-in-circuitpython-with-asyncio/overview
# ). The main processor can just keep checking in to see if the co-processor has
# finished receiving the HTTP response. 
# 
# Unfortunately the CircuitPython Requests library that we can use for sending
# HTTP requests on the esp32-s3 Matrix Portal board does not have async method
# that we can use to send HTTP requests. There is an issue about this on GitHub,
# I did some investigation into this. It would be possible to add this
# functionality but it would be a lot of work because it would requiring making
# the low level socket using for sending the HTTP request async in order to add
# a way for the processor to wait for the coprocessor to receive response at the
# correct point in time. This is just too much work for the train board that I
# am working on.
# https://github.com/adafruit/Adafruit_CircuitPython_Requests/issues/134#issuecomment-3415845378 
# 
# xxx doc As a result we need to work around this issue. So we need to be
# careful about when we send the HTTP request so that it isn't in the middle of
# an animation or something.


# xxx reduce to error or info

# xxx set the status led
matrix_portal = MatrixPortal()

log_levels = logging.LogLevels(aio_handler=logging.INFO, print_handler=logging.DEBUG)
logger = logging.newLogger(logging.LoggerDependencies(matrix_portal), log_levels)

# xxx doc where these numbers come from
train_predictor = TrainPredictor(TrainPredictorDependencies(matrix_portal.network, datetime, timedelta, datetime.now), 
    trainWarningSeconds=60,
    inboundOffsetAverageSeconds=-63, inboundOffsetStdDevSeconds=9,
    outboundOffsetAverageSeconds=93, outboundOffsetStdDevSeconds=9)

time_conversion = TimeConversion(TimeConversionDependencies(datetime.now))
display = Display(DisplayDependencies(matrix_portal, time_conversion, logger), text_scroll_delay=0.1, train_frame_duration=0.1)

app = Application(ApplicationDependencies(matrix_portal, train_predictor, time_conversion, display, datetime.now, logger))

app.run()
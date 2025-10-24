import time

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

DEBUG=True

# xxx doc
# xxx add more debugging
def print_debug(*args):
    if DEBUG:
        print(*args, sep="\n")

NUM_TRAINS_TO_FETCH=3

class ApplicationDependencies:
    def __init__(self, matrix_portal, train_predictor, time_conversion, display):
        self.matrix_portal  = matrix_portal 
        self.train_predictor  = train_predictor 
        self.time_conversion  = time_conversion 
        self.display = display

class Application:
    def __init__(self, dependencies: ApplicationDependencies ):
        self._matrix_portal  = dependencies.matrix_portal 
        self._train_predictor  = dependencies.train_predictor 
        self._time_conversion  = dependencies.time_conversion 
        self._display = dependencies.display

        self._last_train_check = None
        self._trains = [None] * NUM_TRAINS_TO_FETCH

    def run(self):
        self._startup()
        self._run_loop()

    def _startup(self):
        self._sync_clock()

    # xxx doc
    def _sync_clock(self):
        # xxx doc sync current time
        # xxx is there any time float, I should probably update the time every once in a while.
        # xxx double check that calling this multiple times will actually sync the time multiple times
        self._matrix_portal.network.get_local_time(location="America/New_York")

    def _fetch_next_trains(self):
        if self._last_train_check is None or time.monotonic() > self._last_train_check + 180: #xxx check more frequently
            try:
                self._trains = self._train_predictor.next_trains(count = NUM_TRAINS_TO_FETCH)
                self._last_train_check  = time.monotonic()
            except (ValueError, RuntimeError) as e:
                 print("Some error occured, retrying! -", e) # xxx add error logging and error handler
            
    def _run_loop(self):
        while True:
            self._fetch_next_trains()
            if self._trains[0] is not None and self._time_conversion.time_is_soon(self._trains[0].time):
                self._display.render_train(self._trains[0].direction)
            else:
                self._display.render_arrival_times(self._trains)
                self._display.scroll_text()



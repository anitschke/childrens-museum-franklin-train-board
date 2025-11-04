import time
import supervisor
import gc #xxx

#xxx remove unused imports

# xxx add a note somewhere, maybe in the README that this is a lot more
# complicated than it needs to be. If you just want simple text update without
# the animation or other logic I need for computing and caching go point back at
# an earlier commit.

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

# xxx hook something up so you can get stuff to happen by pressing the up and
# down buttons on the board. Maybe play the train animation in either direction?

#xxx add a bunch of error protection

NUM_TRAINS_TO_FETCH=3

class ApplicationDependencies:
    def __init__(self, matrix_portal, train_predictor, time_conversion, display, nowFcn, logger):
        self.matrix_portal  = matrix_portal 
        self.train_predictor  = train_predictor 
        self.time_conversion  = time_conversion 
        self.display = display
        self.nowFcn = nowFcn
        self.logger = logger

class Application:
    def __init__(self, dependencies: ApplicationDependencies ):
        self._matrix_portal  = dependencies.matrix_portal 
        self._train_predictor  = dependencies.train_predictor 
        self._time_conversion  = dependencies.time_conversion 
        self._display = dependencies.display
        self._nowFcn = dependencies.nowFcn
        self._logger = dependencies.logger

        self._last_train_check = None
        self._trains = [None] * NUM_TRAINS_TO_FETCH

        self._last_nightly_tasks_run = time.monotonic()

    def run(self):
        self._startup()
        self._run_loop()

    def _startup(self):
        self._logger.info("starting train board")
        self._try_method(self._sync_clock)

    # xxx doc
    # xxx also add _try_method to dependency creation
    def _try_method(self, method, positional_arguments = [], keyword_arguments = {}):
        attempt_count = 0
        max_attempt_count = 5
        retry_delay = 5
        restart_delay = 60

        while attempt_count < max_attempt_count:
            attempt_count += 1
            try:
                return method(*positional_arguments, **keyword_arguments)
            except Exception as e:
                self._logger.exception(e)
                # xxx show some display on the board that there was an error or whatever
            time.sleep(retry_delay)
            self._logger.debug(f"making additional attempt {attempt_count}")

        self._display.render_error()
        time.sleep(restart_delay)
        supervisor.reload()
            

    def _nightly_tasks(self):
        # xxx doc
        if time.monotonic() < self._last_nightly_tasks_run + 86400:
            return
        
        now = self._nowFcn()
        if now.hour < 3 or now.hour >3:
            return

        self._logger.debug("running nightly tasks")
        self._try_method(self._sync_clock)
        self._try_method(self._add_watchdog_log)
        self._logger.debug(f"Free memory: {gc.mem_free()} bytes")

    def _add_watchdog_log(self):
        # xxx doc have a watchdog setup on adafruit IO to allert me if we stop getting logs, This make sure we always have some logs.
        self._logger.info("I am alive")


    # xxx doc
    def _sync_clock(self):
        # xxx doc sync current time
        # xxx is there any time float, I should probably update the time every once in a while.
        # xxx double check that calling this multiple times will actually sync the time multiple times
        self._logger.debug("getting network time")
        self._matrix_portal.network.get_local_time(location="America/New_York")

    def _fetch_next_trains(self):
        if self._last_train_check is None or time.monotonic() > self._last_train_check + 180: #xxx check more frequently
            self._logger.debug("fetching trains")
            self._trains = self._try_method(self._train_predictor.next_trains, [NUM_TRAINS_TO_FETCH])
            self._last_train_check  = time.monotonic()
            self._logger.debug(f"trains: {self._trains}")
            
    def _run_loop(self):
        while True:
            self._try_method(self._fetch_next_trains)
            train_warning = self._try_method(self._train_predictor.train_passing_warning, [self._trains[0]])
            if train_warning is not None:
                while not train_warning.shouldStop():
                    self._try_method(self._display.render_train, [train_warning.direction])
                self._try_method(self._train_predictor.mark_train_arrived, [self._trains[0]])
            else:
                self._try_method(self._display.render_arrival_times, [self._trains])
                self._try_method(self._display.scroll_text)



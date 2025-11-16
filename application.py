import time
import supervisor
from train_predictor import Direction
import gc
from buttons import button_down_depressed, button_up_depressed

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

        # When we initialize we need to make sure we initialize the display
        # first. If the WiFi is down then the clock sync will fail and
        # _try_method will attempt to call display.render_error() before
        # rebooting. But since the display hasn't been initialized
        # display.render_error() will error out and won't show the error
        # message.
        self._try_method(self._display.initialize)
        self._try_method(self._sync_clock)

    # _try_method is passed a function to call along with arguments. It will
    # call that function, if the function errors out then it will log the
    # exception and then retry after a short delay. If after a few retries it
    # still fails then it will display an error message on the board saying to
    # contact me and attempt to fix the issue by doing a soft restart.
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
            time.sleep(retry_delay)
            self._logger.debug(f"making additional attempt {attempt_count}")

        try:
            self._display.render_error()
        except Exception:
            # We want to squash any errors that come out of render_error. In the
            # past we ran into issues where if the WiFi wasn't setup then the
            # display wasn't initialized and would result in render_error()
            # erroring out and preventing the board from restarting. I fixed
            # that ordering issues but we still want to make sure that even if
            # render_error() errors out we can still try to restart the board in
            # an attempt to fix the issue.
            pass
        
        time.sleep(restart_delay)
        supervisor.reload()
            

    def _nightly_tasks(self):
        # Make sure we only run the nightly tasks once a night
        if time.monotonic() < self._last_nightly_tasks_run + 7200:
            return
        
        now = self._nowFcn()
        if now.hour is not 3:
            return

        self._logger.debug("running nightly tasks")
        self._last_nightly_tasks_run = time.monotonic()
        self._try_method(self._sync_clock)
        self._train_predictor.clear_cache()
        gc.collect()

    # _sync_clock makes a call out to the adafruit ntp servers to update the time on the board.
    def _sync_clock(self):
        self._logger.debug("getting network time")
        self._matrix_portal.network.get_local_time(location="America/New_York")
        self._logger.debug(f"current time set to {self._nowFcn()}")

    def _fetch_next_trains(self):
        # We generally want to make requests to update the train arrival times
        # fairly frequently as when the train is getting close to the Children's
        # Museum of Franklin we want to make sure we have an accurate estimate
        # of arrival time to show the train animation at the correct time. We do
        # still want to make sure we aren't spamming the MBTA API too much. So
        # we will do our own rate limiting of no more than one request every
        # five seconds. When you use a free API key the MBTA API has a rate
        # limit of 1000 requests a minute. So a request every 5 seconds
        # shouldn't give us any issues.
        if self._last_train_check is None or time.monotonic() > self._last_train_check + 5:
            self._logger.debug("fetching trains")
            self._trains = self._try_method(self._train_predictor.next_trains, [NUM_TRAINS_TO_FETCH])
            self._last_train_check  = time.monotonic()
            self._logger.debug(f"trains: {self._trains}")
            
    def _run_loop(self):
        # _run_loop is the main event loop for the board.
        # 
        # My understanding is that the the esp32-s3 comes with a co-processor
        # for handling HTTP requests. So ideally we would send out the HTTP
        # request to get updated arrival times and have the co-processor wait
        # for the response. While we are waiting for the response the main
        # processor can continue doing other tasks like animating the board. The
        # idea here is that I could use async / await along with asyncio python
        # library to do cooperative multitasking (
        # https://learn.adafruit.com/cooperative-multitasking-in-circuitpython-with-asyncio/overview
        # ). The main processor can just keep checking in to see if the
        # co-processor has finished receiving the HTTP response. 
        # 
        # Unfortunately the CircuitPython Requests library that we can use for
        # sending HTTP requests on the esp32-s3 Matrix Portal board does not
        # have async method that we can use to send HTTP requests. There is an
        # issue about this on GitHub, I did some investigation into this. It
        # would be possible to add this functionality but it would be a lot of
        # work because it would requiring making the low level socket using for
        # sending the HTTP request async in order to add a way for the processor
        # to wait for the coprocessor to receive response at the correct point
        # in time. This is just too much work for the train board that I am
        # working on.
        # https://github.com/adafruit/Adafruit_CircuitPython_Requests/issues/134#issuecomment-3415845378 
        # 
        # So instead what we will do is just wait to send HTTP requests at
        # opportune times. We make sure we wait for the text to totally scroll
        # across the screen or any train animation to finish running before we
        # make a new request for train data. Once we get the response for train
        # data we can resume the normal loop.
        while True:
            # First look for user input from buttons.
            # 
            # Note ideally we would use something like hardware interrupts or
            # asyncio to monitor button presses but this adds a lot of
            # complexity to the code so instead we will just check the current
            # state of the button at this point in time. This means that you
            # must be pressing the button when we check for the button press or
            # else the press won't be registered.
            if button_up_depressed():
                self._try_method(self._display.render_train, [Direction.IN_BOUND])
                continue
            if button_down_depressed():
                self._try_method(self._display.render_train, [Direction.OUT_BOUND])
                continue              
            
            # Now move on to regular looping behavior.
            self._nightly_tasks()
            self._try_method(self._fetch_next_trains)
            train_warning = self._try_method(self._train_predictor.train_passing_warning, [self._trains[0]])
            if train_warning is not None:
                # If we know is a train is approaching and we are showing the
                # train animation warning we want to keep playing that warning
                # until the train finishes going by. No need to make a call out
                # to the MBTA to update train predictions until the train
                # finishes going by.
                while not train_warning.should_stop():
                    self._try_method(self._display.render_train, [train_warning.direction])
                self._try_method(self._train_predictor.mark_train_arrived, [self._trains[0]])
                self._logger.info(f"train arrived '{self._trains[0].schedule_id}'")
            else:
                self._try_method(self._display.render_arrival_times, [self._trains])
                self._try_method(self._display.scroll_text)



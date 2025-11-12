# xxx doc
import gc
import time
from collections_extra import LimitedSizeOrderedSet, LimitedSizeOrderedDict

# xxx doc mention https://www.mbta.com/developers/v3-api/best-practices#predictions and how we don't do that exactly

# xxx doc list of stops https://api-v3.mbta.com/stops?filter%5Broute%5D=CR-Franklin

# xxx doc mention that we could geofence The https://api-v3.mbta.com/vehicles
# API will also give us "live" (seems like it updates every 10s or so) data on
# vehicles such as lat/lon, speed, state enum (stopped, boarding, moving, ...),
# and so on. If the /predictions API doesn't give us fine grained enough data to
# determine exactly when trains will arrive we could always switch over to using
# the /vehicles API when trains are getting close in order to build our own
# prediction about when the train will pass by.
#
# The data on the vehicle for a prediction for a schedule is also available when
# we request
# https://api-v3.mbta.com/schedules?filter%5Bstop%5D=place-FB-0275&filter%5Broute%5D=CR-Franklin&sort=arrival_time&include=prediction
# by asking for it in the include query parameter:
# https://api-v3.mbta.com/schedules?filter%5Bstop%5D=place-FB-0275&filter%5Broute%5D=CR-Franklin&sort=arrival_time&include=prediction.vehicles

# DATA_SOURCE is the URL for the MBTA API that we query to get data about
# trains.
# 
# There is very good documentation for this API here
# https://www.mbta.com/developers/v3-api
# 
# In general what we are doing is querying for a schedule of when all trains are
# arriving at the Franklin MBTA station.
# 
# We also ask it to include any predictions that are associated with a given
# schedule. This allows us to use a more accurate prediction when possible but
# otherwise fallback to a the less accurate schedule time for trains that are a
# ways off and don't have a predation yet.
# 
# The "fields" query parameters is a sparce field set that we use to request
# what specific data we are interested in. It means that we get less data back
# that we need to process. See
# https://www.mbta.com/developers/v3-api/best-practices#sparse-fieldsets
# 
# One main disadvantage to this approach is the
# https://api-v3.mbta.com/schedules API will by default give us the schedule for
# ALL trains for today, even ones that have passed by. There are some "filter"
# options to filter by date and by time but it seems that this needs to be
# specified as an absolute date / time which means we would need to deal with
# updating the URL with the current date/time every time we make a request.
# There is also some tricky logic with how the consider times due to the
# "service date" of trains ( see
# https://api-v3.mbta.com/docs/swagger/index.html#/Schedule/ApiWeb_ScheduleController_index
# ). So for now we will just request ALL the trains for today and filter them
# when we get the data back. 
DATA_SOURCE="https://api-v3.mbta.com/schedules?" \
  "filter[stop]=place-FB-0275&" \
  "filter[route]=CR-Franklin&" \
  "sort=arrival_time&" \
  "include=prediction&" \
  "fields[schedule]=arrival_time,departure_time,direction_id&" \
  "fields[prediction]=arrival_time,departure_time,direction_id" 


# xxx doc
# 
# From https://api-v3.mbta.com/docs/swagger/index.html
# 
#   direction_id    integer Direction in which trip is traveling: 0 or 1.
#   
#   The meaning of direction_id varies based on the route. You can
#   programmatically get the direction names from /routes
#   /data/{index}/attributes/direction_names or /routes/{id}
#   /data/attributes/direction_names.
#
# Since we are setting this up for the Franklin line we will just hard code this for now. Looking at https://api-v3.mbta.com/routes/CR-Franklin we can see:
# 
#  "direction_names": [
#        "Outbound",
#        "Inbound"
#      ],
class Direction:
    OUT_BOUND = 0
    IN_BOUND = 1

def direction_str(direction):
    if direction == Direction.OUT_BOUND:
        return "OUT_BOUND"
    if direction == Direction.IN_BOUND:
        return "IN_BOUND"
    return "UNKNOWN"

# xxx doc
# xxx doc std_dev
class TrainArrival:
    def __init__(self, schedule_id, time, direction, std_dev):
        self.schedule_id = schedule_id
        self.time = time
        self.direction = direction
        self.std_dev = std_dev

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"TrainArrival(schedule_id={self.schedule_id}, time={self.time}, direction={direction_str(self.direction)}, std_dev={self.std_dev})"

    @staticmethod
    def sort_by_time(train):
        return train.time      

# xxx doc
class TrainWarning:
    def __init__(self, end_monotonic, direction):
        self._end_monotonic = end_monotonic
        self.direction = direction

    def shouldStop(self) -> bool:
        # xxx test
        return time.monotonic() > self._end_monotonic

class TrainPredictorDependencies:
    def __init__(self, network, datetime, timedelta, nowFcn, mbta_api_key, logger):
        self.network = network 
        self.datetime = datetime 
        self.timedelta = timedelta
        self.nowFcn = nowFcn
        self.mbta_api_key = mbta_api_key
        self.logger = logger

class TrainPredictor:
    def __init__(self, dependencies: TrainPredictorDependencies, filterResultsAfterSeconds = 30, trainWarningSeconds = 0, inboundOffsetAverageSeconds=0, inboundOffsetStdDevSeconds=0, outboundOffsetAverageSeconds=0, outboundOffsetStdDevSeconds=0):
        self._network = dependencies.network
        self._datetime = dependencies.datetime
        self._timedelta = dependencies.timedelta
        self._nowFcn = dependencies.nowFcn
        self._logger = dependencies.logger

        self._filterResultsAfterSeconds = filterResultsAfterSeconds
        self._trainWarningOffset = self._timedelta(seconds=trainWarningSeconds)

        self._inboundOffsetAverage = self._timedelta(seconds = inboundOffsetAverageSeconds)
        self._inboundOffsetStdDev = self._timedelta(seconds = inboundOffsetStdDevSeconds)
        self._outboundOffsetAverage = self._timedelta(seconds = outboundOffsetAverageSeconds)
        self._outboundOffsetStdDev = self._timedelta(seconds = outboundOffsetStdDevSeconds)
    
        self._arrived_trains = LimitedSizeOrderedSet(100)

        # xxx doc uses schedule ID as key and has train as value.
        # Needed to make sure we don't get arrival time messed up when prediction goes away
        # 
        # xxx test
        self._train_prediction_cache = LimitedSizeOrderedDict(10)

        self._mbta_api_headers = {
            "accept":  "application/vnd.api+json"
        }
        if dependencies.mbta_api_key is not None:
            self._mbta_api_headers["x-api-key"] = dependencies.mbta_api_key
        

        # The MBTA API responds with a content type header of
        # "application/vnd.api+json". When the matrix portal looks at the
        # response from this API it looks at the content type header to decide
        # if it can parse te response into JSON. But the matrix portal doesn't
        # have "application/vnd.api+json" in it's list of default JSON content
        # types so we need to add that in order for it to correctly recognize
        # the response as JSON and then parse it. see
        # https://github.com/adafruit/Adafruit_CircuitPython_PortalBase/blob/d5c51a1838c3aec4d5fbfafb9f09cf62c528d58b/adafruit_portalbase/network.py#L104
        if self._network is not None:
            self._network.add_json_content_type("application/vnd.api+json")

    # xxx doc
    def next_trains(self, count):
        schedule_json = self._fetch_schedules_and_predictions()
        results =  self._analyze_data(count, schedule_json)
        gc.collect()
        return results

    def train_passing_warning(self, train: TrainArrival):
        if train is None:
            return None

        # xxx test
        # xxx doc talk about the statistics
        now = self._nowFcn()
        warning_start_time = train.time - self._trainWarningOffset -  (2 * train.std_dev)
        if warning_start_time > now:
            return None
        warning_stop_time = train.time + (3 * train.std_dev)
        remaining_seconds = (warning_stop_time - now).total_seconds()
        now_monatomic = time.monotonic()
        end_monatomic = now_monatomic + remaining_seconds
        
        return TrainWarning(end_monatomic, train.direction)
    
    # xxx doc
    # xxx test
    def mark_train_arrived(self, train):
        self._logger.debug(f"marking '{train.schedule_id}' as arrived")
        self._arrived_trains.add(train.schedule_id)

    def _fetch_schedules_and_predictions(self):
        # When doing data analysis I ran into a few cases where the request to
        # the MBTA API appeared to stall and time out forever. So we want to
        # make sure we have a timeout here to make sure the request doesn't
        # totally stall.
        timeout = 10
        response = self._network.fetch(DATA_SOURCE, headers=self._mbta_api_headers, timeout=timeout)
        if response.status_code is not 200:
            raise RuntimeError(f"Failed to fetch data from MBTA API. status_code: {response.status_code} response: {response.text}")
        return response.json()
    
    # xxx test
    def _compute_train(self, schedule_id, schedule, prediction):
        self._logger.debug(f"computing train arrival time for '{schedule_id}' schedule={schedule}, prediction={prediction}")

        # If we know the train has already arrived then ignore it
        if schedule_id in self._arrived_trains:
            self._logger.debug(f"Filtering '{schedule_id}' since it is marked as having arrived already")
            return None

        direction = schedule.get("direction_id")
        cmf_arrival_time, time_is_from_prediction = self._get_estimated_cmf_arrival_time(schedule, prediction, direction)
        if cmf_arrival_time is None:
            self._logger.debug(f"Filtering '{schedule_id}' since no predicted arrival time could be computed")
            return None
        
        # Remove any times more than self._filterResultsAfterSeconds (by default
        # 5 minutes ago). For the most part trains that have already passed by
        # should be removed with the _arrived_trains check because we call
        # mark_train_arrived to mark the train as already arrived, so we really
        # just need to deal with filtering out old trains from before the board
        # first starts up.
        now = self._nowFcn()
        if (cmf_arrival_time - now).total_seconds() < (-1 * self._filterResultsAfterSeconds):
            self._logger.debug(f"Filtering '{schedule_id}' since predicted arrival time ({cmf_arrival_time}) is in the past (now = {now})")
            return None

        std_dev = self._inboundOffsetStdDev if direction == Direction.IN_BOUND else self._outboundOffsetStdDev

        train = TrainArrival(schedule_id, cmf_arrival_time, direction, std_dev)

        # Outbound trains have a prediction time to arrive at the Children's
        # Museum of Franklin after it leaves the Franklin station. Unfortunately
        # as we noticed when analyzing data (see
        # https://github.com/anitschke/childrens-museum-franklin-train-board-data-analysis
        # ) as soon as a train leaves from a station MBTA removes the
        # prediction. This could cause issues for us because we still need that
        # prediction to predict when it will pass by the Children's Museum of
        # Franklin. If the time offsets are such that we don't start playing the
        # train warning animation before the train leaves the station the
        # prediction will go away and we won't have an accurate measure of when
        # the train is leaving.
        # 
        # I think that the Children's Museum of Franklin is close enough that
        # the time offsets won't ever have this happen. But just to be on the
        # safe side we will do some caching to prevent it. For a given schedule
        # we will cache the train arrival object if the train arrival object was
        # crated using prediction data.
        # 
        # Then later if we see that the train arrival data is no logger from a
        # prediction we will used the cached copy from the prediction if we have
        # it.
        # 
        # xxx test
        if time_is_from_prediction:
            self._logger.debug(f"Inserting prediction for '{schedule_id}' into cache")
            self._train_prediction_cache[schedule_id] = train
        elif schedule_id in self._train_prediction_cache:
            cached_train = self._train_prediction_cache[schedule_id]
            self._logger.debug(f"Using existing cached prediction for '{schedule_id}' {cached_train}")
            return cached_train

        self._logger.debug(f"Computed train for '{schedule_id}' {train}")
        return train

    # xxx test
    # xxx doc
    def _get_estimated_cmf_arrival_time(self, schedule, prediction, direction):
        # Prefer using prediction data if possible
        if prediction is not None:
            result = self._compute_cmf_arrival_time(direction, prediction.get("arrival_time"), prediction.get("departure_time"))
            if result is not None:
                return result, True
        
        # Fall back to using schedule data
        return self._compute_cmf_arrival_time(schedule.get("direction_id"), schedule.get("arrival_time"), schedule.get("departure_time")), False

    def _compute_cmf_arrival_time(self, direction, arrival_time, departure_time):
        # We are using the Franklin station for our predictions since it is
        # closest to the Children's Museum of Franklin. The Children's Museum of
        # Franklin is on the outbound side of the Franklin station. So for
        # inbound trains we will watch for the arrival time at the Franklin
        # station since the train will pass by Children's Museum of Franklin
        # before it gets to the station. For outbound trains we will watch the
        # departure time from the Franklin station since the train will pass by
        # the Children's Museum of Franklin after the train departs from the
        # station.
        #
        # If the preferred time is not available we will fall back to using the
        # other time. This is since we still want to use prediction data over
        # using schedule or not coming up with an answer at all.
        #
        # xxx doc also mention offset
        #
        # xxx doc point to analysis page

        station_time_str = (arrival_time or departure_time) if direction == Direction.IN_BOUND else (departure_time or arrival_time)
        station_time = self._datetime.fromisoformat(station_time_str).replace(tzinfo=None)

        # Since the Children's Museum of Franklin isn't exactly at the Franklin
        # station we need to apply an offset to station time to give a better
        # estimate of when the train will pass by Children's Museum of Franklin.
        offset = self._inboundOffsetAverage if direction == Direction.IN_BOUND else self._outboundOffsetAverage
        cmf_time = station_time + offset
        return cmf_time

    def _analyze_data(self, count, schedule_json):
        gc.collect()
        trains = []
        included = {item["id"]: item for item in schedule_json.get("included", [])}

        # xxx doc some old notes that need to be cleaned up:
        # 
        # this logic could probably be improved some depending on how accurate
        # we want to try to get the board:
        # 
        # 1. We want to predict the time that the train passes the children's
        #    museum, not when it arrives at the station. So instead of just looking
        #    at the station arrival_time or departure_time we should probably look
        #    at the "direction" of the train and add some offset to either the
        #    arrival_time or departure_time based on what direction it is going.
        #
        # 2. with regards to null arrival times and departure times
        #    https://www.mbta.com/developers/v3-api/best-practices says:
        # 
        #       The departure time is present if, and only if, it's possible for
        #       riders to board the associated vehicle at the associated stop. A
        #       null departure time is typically seen at the last stop on a trip.
        #  
        #       The arrival time is present if, and only if, it's possible for
        #       riders to alight from the associated vehicle at the associated stop.
        #       A null arrival time is typically seen at the first stop on a trip.
        #  
        #       In general, we recommend not displaying predictions with null
        #       departure times, since riders will not be able to board the vehicle.
        #       If both arrival and departure time are present, the arrival time is
        #       likely to be more useful to riders.
        #
        #    We don't really care about the "can a customer board or not" but I do
        #    sometimes see some null values in the schedule. I think we need to
        #    consider the above logic in how we calculate when the train will pass
        #    by.
    
        # Build trains list
        for item in schedule_json.get("data", []):

            # Get prediction if available
            perdition = None 
            prediction_ref = item.get("relationships", {}).get("prediction", {}).get("data")
            if prediction_ref and prediction_ref.get("id") in included:
                perdition = included[prediction_ref["id"]]["attributes"]

            # Compute the train object
            schedule_attrs = item.get("attributes", {})
            train = self._compute_train(item.get("id"), schedule_attrs, perdition)
            if train is not None:
                trains.append(train)

        # Sort the list
        trains.sort(key=TrainArrival.sort_by_time)

        # We only need "count" times as we only display that many on the board. So we
        # will trim or pad the array so we always have "count" values:
        while len(trains) < count:
            trains.append(None)
        trains = trains[:count]

        return trains
    
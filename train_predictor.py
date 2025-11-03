# xxx doc
import gc
import time

#xxx read through https://www.mbta.com/developers/v3-api/best-practices#predictions to see if you are getting it right

# xxx see if you can use sparce fieldsets to request less data: https://www.mbta.com/developers/v3-api/best-practices#sparse-fieldsets
#
# working example: https://api-v3.mbta.com/schedules?filter%5Bstop%5D=place-FB-0275&filter%5Broute%5D=CR-Franklin&sort=arrival_time&include=prediction.vehicle&fields[schedule]=arrival_time,departure_time,direction_id&fields[prediction]=arrival_time,arrival_uncertainty,departure_time,departure_uncertainty,direction_id,revenue,status&fields[vehicle]=bearing,current_status,direction_id,latitude,longitude,revenue,speed,updated_at

# xxx doc list of stops https://api-v3.mbta.com/stops?filter%5Broute%5D=CR-Franklin

# xxx also look at
# https://github.com/mbta/gtfs-documentation/blob/master/reference/gtfs-realtime.md#json-feeds
# as an alternative If I look at
# https://cdn.mbta.com/realtime/VehiclePositions_enhanced.json and
# https://cdn.mbta.com/realtime/VehiclePositions.json I can see that It shows me
# actual lat / lon of vehicles. https://cdn.mbta.com/realtime/TripUpdates.json
# also seems to show live updates. So this might give more accurate estimate
# depending on how often it is updated. Looking at the ETag of the request and
# the last-modified it seems to show that it really is 100% live. If I diff it
# in meld I can even see changes in lat / lon live. So the question is will
# api-v3.mbta.com be just as accurate or should I use cdn.mbta.com/realtime
# instead? And if I should use cdn.mbta.com/realtime instead is there an easy
# way to get the data I want. Doing some digging through the General Transit
# Feed Specification Realtime (GTFS-RT) spec I do not see any way to filter the
# data. The data that we get from these json files is MASSIVE, I think it will
# be way too much for us to parse into json and dig through all that data to
# find what we were looking for.

# xxx The https://api-v3.mbta.com/vehicles API will also give us "live" (seems
# like it updates every 10s or so) data on vehicles such as lat/lon, speed,
# state enum (stopped, boarding, moving, ...), and so on. If the /predictions
# API doesn't give us fine grained enough data to determine exactly when trains
# will arrive we could always switch over to using the /vehicles API when trains
# are getting close in order to build our own prediction about when the train
# will pass by.
#
# The data on the vehicle for a prediction for a schedule is also available when
# we request
# https://api-v3.mbta.com/schedules?filter%5Bstop%5D=place-FB-0275&filter%5Broute%5D=CR-Franklin&sort=arrival_time&include=prediction
# by asking for it in the include query parameter:
# https://api-v3.mbta.com/schedules?filter%5Bstop%5D=place-FB-0275&filter%5Broute%5D=CR-Franklin&sort=arrival_time&include=prediction.vehicles

# xxx get an API key get to control versioning: https://www.mbta.com/developers/v3-api/versioning

# xxx this api is pretty good but it has some issues:
# 
# * It returns the whole scedule for the entire day including trips that has
#   already happened, this means we need to parse a lot more data. There is an
#   filter for min_time but the rules as per the API documentation seem a little
#   tricky to implement as sometimes you need to use times greater than 24 hours
#
# * It seems like it will return all the trips with a service data of the
#   current day. this means towards the end of the day we might not have a full
#   list of all trains coming the next data. There is a `date` filter but it
#   seems to not allow multiple values.
# 
# If needed the fetch() API does have the ability to pass in a udpate_url that
# we could use to inject in the current date/time.
# https://github.com/adafruit/Adafruit_CircuitPython_PortalBase/blob/d5c51a1838c3aec4d5fbfafb9f09cf62c528d58b/adafruit_portalbase/__init__.py#L438

DATA_SOURCE='https://api-v3.mbta.com/schedules?filter%5Bstop%5D=place-FB-0275&filter%5Broute%5D=CR-Franklin&sort=arrival_time&include=prediction'


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
    def __init__(self, time, direction, std_dev):
        self.time = time
        self.direction = direction
        self.std_dev = std_dev

    def str(self):
        return f"time: {self.time}, direction: {direction_str(self.direction)}"

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
    def __init__(self, network, datetime, timedelta, nowFcn):
        self.network = network 
        self.datetime = datetime 
        self.timedelta = timedelta
        self.nowFcn = nowFcn 

class TrainPredictor:
    def __init__(self, dependencies: TrainPredictorDependencies, filterResultsAfterSeconds = 120, trainWarningSeconds = 0, inboundOffsetAverageSeconds=0, inboundOffsetStdDevSeconds=0, outboundOffsetAverageSeconds=0, outboundOffsetStdDevSeconds=0):
        self._network = dependencies.network
        self._datetime = dependencies.datetime
        self._timedelta = dependencies.timedelta
        self._nowFcn = dependencies.nowFcn

        self._filterResultsAfterSeconds = filterResultsAfterSeconds
        self._trainWarningOffset = self._timedelta(seconds=trainWarningSeconds)

        self._inboundOffsetAverage = self._timedelta(seconds = inboundOffsetAverageSeconds)
        self._inboundOffsetStdDev = self._timedelta(seconds = inboundOffsetStdDevSeconds)
        self._outboundOffsetAverage = self._timedelta(seconds = outboundOffsetAverageSeconds)
        self._outboundOffsetStdDev = self._timedelta(seconds = outboundOffsetStdDevSeconds)
    
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

    def _fetch_schedules_and_predictions(self):
        # xxx move DATA_SOURCE into TrainPredictor?
        # xxx what do I want for a timeout here?
        response = self._network.fetch(DATA_SOURCE, timeout=10)
        return response.json()
    
    # xxx test
    def _compute_train(self, schedule, prediction):
        
        direction = schedule.get("direction_id")

        cmf_arrival_time = self._get_estimated_cmf_arrival_time(schedule, prediction, direction)
        if cmf_arrival_time is None:
            return None
        
        std_dev = self._inboundOffsetStdDev if direction == Direction.IN_BOUND else self._outboundOffsetStdDev

        # xxx it would be a lot more efficient to do the check to see if we need
        # to keep the train around here and just return None if the train has
        # passed by rather than add it to an array that will get even bigger and
        # take up more memory that we need to eventually filter down.

        # xxx we could also do some things to make it more efficient like if the
        # train is more than 4 or 8 or 12 hours away then don't bother returning
        # it too

        
        train = TrainArrival(cmf_arrival_time, direction, std_dev)
        return train

    # xxx test
    # xxx doc
    def _get_estimated_cmf_arrival_time(self, schedule, prediction, direction):
        # Prefer using prediction data if possible
        if prediction is not None:
            result = self._compute_cmf_arrival_time(direction, prediction.get("arrival_time"), prediction.get("departure_time"))
            if result is not None:
                return result
        
        # Fall back to using schedule data
        return self._compute_cmf_arrival_time(schedule.get("direction_id"), schedule.get("arrival_time"), schedule.get("departure_time"))

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

        # xxx this logic could probably be improved some depending on how accurate
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
            train = self._compute_train(schedule_attrs, perdition)
            if train is not None:
                trains.append(train)

        # Sort the list
        trains.sort(key=TrainArrival.sort_by_time)

        # xxxxxxxxxxx figure out how to turn print_debug back on in tests
        # print_debug("times:", times) 

        # Remove any times more than self._filterResultsAfterSeconds (by default
        # 2 minutes ago). When we do this we need to make sure we remove any
        # time zone information or else we get "CircuitPython does not currently
        # implement time.gmtime" errors.
        now = self._nowFcn()
        # print_debug("now:", now)
        trains = [t for t in trains if (t.time - now).total_seconds() >= (-1 * self._filterResultsAfterSeconds)]
        # print_debug("filtered trains:", trains)

        # We only need "count" times as we only display that many on the board. So we
        # will trim or pad the array so we always have "count" values:
        while len(trains) < count:
            trains.append(None)
        trains = trains[:count]
        # print_debug("filtered times:", trains)


        #xxx move this into the display code

        # # Now transform them into nice user readable times
        # readable_times = [get_arrival_in_minutes_from_now(now, t) for t in times]
        # print_debug("readable_times:", times)

        return trains
    
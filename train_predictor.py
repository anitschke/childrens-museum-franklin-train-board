# xxx doc
import gc

class TrainArrival:
    def __init__(self, time, direction):
        self.time = time
        self.direction = direction

    @staticmethod
    def sort_by_time(train):
        return train.time      

class TrainPredictor:
    def __init__(self, network, datetime, nowFcn):
        self._network = network
        self._datetime = datetime
        self._nowFcn = nowFcn
    
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

    

    def _fetch_schedules_and_predictions(self):
        # xxx move DATA_SOURCE into TrainPredictor?
        # xxx what do I want for a timeout here?
        return self._network.fetch(DATA_SOURCE, timeout=10)
    
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
            prediction_ref = item.get("relationships", {}).get("prediction", {}).get("data")
            prediction_time = None

            # Prefer prediction if available
            if prediction_ref and prediction_ref.get("id") in included:
                pred = included[prediction_ref["id"]]["attributes"]
                prediction_time = pred.get("arrival_time") or pred.get("departure_time")

            # Fallback to schedule times if prediction missing
            schedule_attrs = item.get("attributes", {})
            schedule_time = (
                schedule_attrs.get("arrival_time")
                or schedule_attrs.get("departure_time")
            )

            time_str = prediction_time or schedule_time
            if time_str:
                direction = schedule_attrs.get("direction_id")
                train = TrainArrival(time_str, direction)
                trains.append(train)

        # Sort the list
        trains.sort(key=TrainArrival.sort_by_time)

        # xxxxxxxxxxx figure out how to turn print_debug back on in tests
        # print_debug("times:", times) 

        # Remove any times more than 2 minutes ago When we do this we need to make
        # sure we remove any time zone information or else we get "CircuitPython
        # does not currently implement time.gmtime" errors.
        now = self._nowFcn()
        # print_debug("now:", now)
        trains = [t for t in trains if (self._datetime.fromisoformat(t.time).replace(tzinfo=None) - now).total_seconds() >= -120.0]
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
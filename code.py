import time
import microcontroller
from board import NEOPIXEL
import displayio
import adafruit_display_text.label
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_datetime import datetime, timedelta
import adafruit_ntp
import json
import gc

#xxx remove unused imports

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
DEBUG=True

ARRIVAL_TIMES_FONT='fonts/6x10.bdf'

#xxx doc
DATA_LOCATION = [
     ["times", 0],
     ["times", 1],
     ["times", 2]
]

#xxx doc
def print_debug(*args):
    if DEBUG:
        print(*args, sep="\n")

# xxx doc 
def get_arrival_in_minutes_from_now(now, date_str):
    
    # xxx if we weren't able to get any data then we get a none type. To avoid issues with parsing we will check and just return empty
    if date_str is None:
         return ""

    # When we look at times we need to make sure we remove any time zone
    # information or else we get "CircuitPython does not currently implement
    # time.gmtime" errors.
    train_date = datetime.fromisoformat(date_str).replace(tzinfo=None) # Remove tzinfo to be able to diff dates # xxx is this really needed?
    time_in_minutes = round((train_date-now).total_seconds()/60.0)

    if time_in_minutes <= 1:
        return "Arriving"
    if time_in_minutes < 60:
        return  f"{time_in_minutes}min"
    
    time_in_hours = round(time_in_minutes/60.0)
    extra_minutes = time_in_minutes % 60
    if extra_minutes == 0:
        return f"{time_in_hours}h"
    else:
        return f"{time_in_hours}h {extra_minutes}min"

# xxx doc
def transform_json(schedule_json):
    gc.collect()
    times = []
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
 
    # Build times list
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
            times.append(time_str)

    # Sort the list
    times.sort()
    print_debug("times:", times)

    # Remove any times more than 2 minutes ago When we do this we need to make
    # sure we remove any time zone information or else we get "CircuitPython
    # does not currently implement time.gmtime" errors.
    now = datetime.now()
    print_debug("now:", now)
    times = [t for t in times if (datetime.fromisoformat(t).replace(tzinfo=None) - now).total_seconds() >= -120.0]
    print_debug("filtered times:", times)

    # We only need three times as we only display that many on the board. So we
    # will trim or pad the array so we always have three values:
    while len(times) < 3:
        times.append(None)
    times = times[:3]
    print_debug("filtered times:", times)

    # Now transform them into nice user readable times
    readable_times = [get_arrival_in_minutes_from_now(now, t) for t in times]
    print_debug("readable_times:", times)


    # matrix portal expects that we transform the json by modifying the dict
    # that we are passed. So instead of returning something we will clear the
    # dict and then populate with the times. We only need to populate in three
    # of these times since we only show at most three times on the board.
    schedule_json.clear()
    schedule_json["times"] = readable_times

    print_debug("transformed json:", schedule_json)

    # Cleanup
    del times
    del included
    gc.collect()

# xxx set the status led
matrixPortal = MatrixPortal(url=DATA_SOURCE, debug=DEBUG, json_path=DATA_LOCATION)

# xxx doc sync current time
# xxx is there any time float, I should probably update the time every once in a while.
matrixPortal.network.get_local_time(location="America/New_York")

# The MBTA API responds with a content type header of
# "application/vnd.api+json". When the matrix portal looks at the response from
# this API it looks at the content type header to decide if it can use the
# json_path provided to parse the response. But the matrix portal doesn't have
# "application/vnd.api+json" in it's list of default json content types so we
# need to add that in order for it to correctly recognize the response as json
# and then parse it. see
# https://github.com/adafruit/Adafruit_CircuitPython_PortalBase/blob/d5c51a1838c3aec4d5fbfafb9f09cf62c528d58b/adafruit_portalbase/network.py#L104
matrixPortal.network.add_json_content_type("application/vnd.api+json")

# xxx doc
matrixPortal.network.add_json_transform(transform_json)

matrixPortal.set_background('/background.bmp')
matrixPortal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(15, 3), text="Children's Museum of Franklin", is_data=False, scrolling=True)

#xxx documentation seems to say that I can give a list of text_position but can't seem to get that to work, look into this some more
matrixPortal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(16, 11), text="?min", is_data=True)
matrixPortal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(16, 19), text="?min", is_data=True)
matrixPortal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(16, 27), text="?min", is_data=True)


last_check = None

while True:
    if last_check is None or time.monotonic() > last_check + 180: #xxx check more frequently
        try:
            value = matrixPortal.fetch()
            print_debug("Response is:", value)
            last_check = time.monotonic()
        except (ValueError, RuntimeError) as e:
            print("Some error occured, retrying! -", e)
    matrixPortal.scroll()
    time.sleep(0.03)

class DisplayMode:
    ARRIVAL_TIMES = 1

# xxx doc
# xxx test
class Display:
    def __init__(self, matrix_portal, text_scroll_delay):
        self._matrix_portal = matrix_portal
        self._mode = None
        self._text_scroll_delay = text_scroll_delay
        
        self._arrival_time_indices = None
    
    def render_arrival_times(self, times):
        if self.mode != DisplayMode.ARRIVAL_TIMES:
            self._initialize_arrival_times()
        self._matrix_portal.set_text(times[0], self._arrival_time_indices[0])
        self._matrix_portal.set_text(times[1], self._arrival_time_indices[1])
        self._matrix_portal.set_text(times[2], self._arrival_time_indices[2])


    def _initialize_arrival_times(self):
        self._matrix_portal.remove_all_text()
        self._matrix_portal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(15, 3), text="Children's Museum of Franklin", is_data=False, scrolling=True)
        
        self._arrival_time_indices = [
            self._matrix_portal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(16, 11), text="?min", is_data=False),
            self._matrix_portal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(16, 19), text="?min", is_data=False),
            self._matrix_portal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(16, 27), text="?min", is_data=False),
        ]
        self._mode = DisplayMode.ARRIVAL_TIMES

    def scroll_text(self):
        self._matrix_portal.scroll_text(self._text_scroll_delay)
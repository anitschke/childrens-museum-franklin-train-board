import time
import microcontroller
from board import NEOPIXEL
import displayio
import adafruit_display_text.label
from adafruit_datetime import datetime
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_datetime import datetime
import adafruit_ntp
import json

#xxx remove unused imports

#xxx I feel like I am getting too many results saying that trains are ariving way more frequently then they probably are

#xxx read through https://www.mbta.com/developers/v3-api/best-practices#predictions to see if you are getting it right

# xxx see if you can use sparce fieldsets to request less data: https://www.mbta.com/developers/v3-api/best-practices#sparse-fieldsets

# xxx the other MBTA board uses a different API, not sure why:
# https://github.com/jegamboafuentes/Train_schedule_board/blob/ae2938fc52b9993b929b04ba700fe58fa47946cb/display_code/8-23-23/new/code.py#L28
DATA_SOURCE='https://api-v3.mbta.com/predictions?filter%5Bstop%5D=Franklin&filter%5Broute%5D=CR-Franklin&page%5Blimit%5D=3&sort=arrival_time'
DEBUG=True

ARRIVAL_TIMES_FONT='fonts/6x10.bdf'

DATA_LOCATION = [
     ["data", 0, "attributes", "departure_time"],
     ["data", 1, "attributes", "departure_time"],
     ["data", 2, "attributes", "departure_time"]
]

def print_debug(str):
    if DEBUG:
        print(str)

def get_arrival_in_minutes_from_now(date_str):
    
    # xxx if we weren't able to get any data then we get a none type. To avoid issues with parsing we will check and just return empty
    if date_str is None:
         return ""

    now = datetime.now()
    train_date = datetime.fromisoformat(date_str).replace(tzinfo=None) # Remove tzinfo to be able to diff dates # xxx is this really needed?
    time_in_minutes = round((train_date-now).total_seconds()/60.0)

    #xxx
    print_debug(f"now: {now}")
    print_debug(f"time_in_minutes: {time_in_minutes}")

    if time_in_minutes <= 0:
        return "Now Arriving"
    else:
        return f"{time_in_minutes} min"
    #xxx handle times that are longer than an hour

# xxx set the status led
matrixPortal = MatrixPortal(url=DATA_SOURCE, debug=DEBUG, json_path=DATA_LOCATION)

# xxx doc sync current time
# xxx add debugging output 
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

matrixPortal.set_background('/background.bmp')
matrixPortal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(15, 3), text="Children's Museum of Franklin", is_data=False, scrolling=True)

#xxx documentation seems to say that I can give a list of text_position but can't seem to get that to work, look into this some more
matrixPortal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(26, 11), text="? min", is_data=True, text_transform=get_arrival_in_minutes_from_now)
matrixPortal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(26, 19), text="? min", is_data=True, text_transform=get_arrival_in_minutes_from_now)
matrixPortal.add_text( text_font=ARRIVAL_TIMES_FONT, text_position=(26, 27), text="? min", is_data=True, text_transform=get_arrival_in_minutes_from_now)


last_check = None

while True:
    if last_check is None or time.monotonic() > last_check + 180:
        try:
            print(matrixPortal.json_path)
            value = matrixPortal.fetch()
            print("Response is", value)
            last_check = time.monotonic()
        except (ValueError, RuntimeError) as e:
            print("Some error occured, retrying! -", e)
    matrixPortal.scroll()
    time.sleep(0.03)
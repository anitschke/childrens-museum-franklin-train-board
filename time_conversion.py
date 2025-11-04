import math

# xxx doc
class TimeConversionDependencies:
    def __init__(self, nowFcn):
        self.nowFcn = nowFcn


# xxx doc

class TimeConversion:
    def __init__(self, dependencies: TimeConversionDependencies):
        self._nowFcn = dependencies.nowFcn

    # xxx doc
    def relative_time_from_now(self, train_time):

        # When we look at times we need to make sure we remove any time zone
        # information or else we get "CircuitPython does not currently implement
        # time.gmtime" errors.
        now = self._nowFcn()
        time_in_seconds = (train_time-now).total_seconds()

        if time_in_seconds <= 60:
            return "Arriving"

        # I debated if I should use round, floor or ceil here. The MBTA best
        # practices page https://www.mbta.com/developers/v3-api/best-practices
        # says that for countdown display guide lines:
        #
        #    Round the seconds value to the nearest whole number of minutes,
        #    rounding up if exactly in-between; call this value "minutes."
        #
        # So we will use round here.
        time_in_minutes = round(time_in_seconds/60)
        if time_in_minutes < 60:
            return  f"{time_in_minutes}min"

        time_in_hours, extra_minutes = divmod(time_in_minutes, 60.0)
        if extra_minutes == 0:
            return f"{int(time_in_hours)}h"
        else:
            return f"{int(time_in_hours)}h {int(extra_minutes)}min"
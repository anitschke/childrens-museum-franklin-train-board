from time_conversion import TimeConversion, TimeConversionDependencies
from datetime import datetime
import unittest


def mock_now_func(timeOfNow):
    return lambda : datetime.fromisoformat(timeOfNow).replace(tzinfo=None)
    
class Test_relative_time_from_now(unittest.TestCase):
    def run_test(self, now, time_str, exp_result):
        now_func = mock_now_func(now)
        deps = TimeConversionDependencies(datetime=datetime, nowFcn=now_func)
        time_conv = TimeConversion(deps)
        act_result = time_conv.relative_time_from_now(time_str)
        self.assertEqual(act_result, exp_result)

    def test_time_already_gone_past(self):
        self.run_test(now="2025-10-22T05:07:00", time_str="2025-10-22T05:06:00", exp_result="Arriving")

    def test_less_than_1min(self):
        self.run_test(now="2025-10-22T05:06:00", time_str="2025-10-22T05:06:30", exp_result="Arriving")

    def test_1min_0s(self):
        self.run_test(now="2025-10-22T05:06:00", time_str="2025-10-22T05:07:00", exp_result="Arriving")

    def test_1min_10s(self):
        self.run_test(now="2025-10-22T05:06:00", time_str="2025-10-22T05:07:10", exp_result="1min")

    def test_1min_50s(self):
        self.run_test(now="2025-10-22T05:06:00", time_str="2025-10-22T05:07:50", exp_result="2min")

    def test_2min_10s(self):
        self.run_test(now="2025-10-22T05:06:00", time_str="2025-10-22T05:08:10", exp_result="2min")

    def test_1h_0min_10s(self):
        self.run_test(now="2025-10-22T05:06:00", time_str="2025-10-22T06:06:10", exp_result="1h")

    def test_1h_1min_10s(self):
        self.run_test(now="2025-10-22T05:06:00", time_str="2025-10-22T06:07:10", exp_result="1h 1min")




if __name__ == '__main__':
    unittest.main()
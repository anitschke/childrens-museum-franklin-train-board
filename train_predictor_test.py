from train_predictor import TrainPredictor, TrainPredictorDependencies, Direction
from datetime import datetime
import json
import os
import unittest
import urllib.request


def mock_now_func(timeOfNow):
    return lambda : datetime.fromisoformat(timeOfNow).replace(tzinfo=None)

def load_test_schedule_json(file):
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_file_directory, 'testdata', 'schedules', file)
    with open(file_path, 'r') as file:
        return json.load(file)

class MockResponse:
    def __init__(self, jsonResponse):
        self._jsonResponse = jsonResponse
    
    def json(self):
        return self._jsonResponse

class MockNetwork:
    def add_json_content_type(self, type):
        return
    def fetch(self, url, timeout=30):
        with urllib.request.urlopen(url) as response:
            data = response.read()
            jsonData = json.loads(data.decode('utf-8'))
            return MockResponse(jsonData)
    
class Test_next_trains(unittest.TestCase):
    def test_next_trains(self):
        # The goal of this test is to be a system level test that actually calls
        # next_trains to connect together _fetch_schedules_and_predictions and
        # _analyze_data to actually make an HTTP request to MBTA API to make
        # sure we can really analyze that real data.

        # When we provide the timestamp for "now" we will give the timestamp of
        # 1am on the current morning. We will do this because if the test is
        # running late at night there is a chance that there are no more trains
        # tonight and the test expects that we will get some results back for
        # the train. So setting the current time to 1am should ensure that we
        # don't filter out trains that have already happened.
        now = datetime.now()
        mock_now = lambda : now.replace(tzinfo=None, hour=1)

        deps = TrainPredictorDependencies(MockNetwork(), datetime, mock_now)
        train_predictor = TrainPredictor(deps)
        results = train_predictor.next_trains(count=1)

        self.assertEqual(len(results), 1)
        self.assertNotEqual(results[0], None)
        
        # Since we said that we will test as if it is 1am we should be getting
        # the first train of the day. This is ALMOST always an inbound train
        # that happens a 5am. So lets verify it is inbound and happens before 8
        # am.
        self.assertEqual(results[0].direction, Direction.IN_BOUND)

        expected_time = now.replace(hour=8)
        self.assertLess(results[0].time, expected_time.isoformat())



class Test_fetch_schedules_and_predictions(unittest.TestCase):
    def test_fetch(self):
        # This is a basic test that the train predictor can make a request to
        # the MBTA APIs and get something back. For this test we won't bother
        # doing anything more than having the MockNetwork make the request and
        # do the json decode. If that worked that is good enough for this test.
        # We will use Test_next_trains to connect together testing for
        # _fetch_schedules_and_predictions and _analyze_data to make sure we can
        # actually analyze data that is currently coming out of the API.
        deps = TrainPredictorDependencies(MockNetwork(), datetime=None, nowFcn=None)
        train_predictor = TrainPredictor(deps)
        train_predictor._fetch_schedules_and_predictions()    

class Test_analyze_data(unittest.TestCase):
    # xxx doc
    def test_simple(self):
        # Simple test with best case where we have both the schedule data and
        # prediction data for a train.
        mock_now = mock_now_func('2025-10-22T23:04:00-04:00')
        deps = TrainPredictorDependencies(network=None, datetime=datetime, nowFcn=mock_now)
        train_predictor = TrainPredictor(deps)

        data = load_test_schedule_json('simple.json')
        
        count = 1
        result = train_predictor._analyze_data(count, data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].direction, 0)
        self.assertEqual(result[0].time, "2025-10-22T23:04:53-04:00")

    def test_simple_sparse(self):
        # This is the same as test_simple but uses a sparse dataset. The MBTA
        # allows requesting a more minimal dataset. So this is the smallest
        # amount of data that I think we can get away with requesting at the
        # moment.
        mock_now = mock_now_func('2025-10-22T23:04:00-04:00')
        deps = TrainPredictorDependencies(network=None, datetime=datetime, nowFcn=mock_now)
        train_predictor = TrainPredictor(deps)

        data = load_test_schedule_json('simple_sparse.json')
        
        count = 1
        result = train_predictor._analyze_data(count, data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].direction, 0)
        self.assertEqual(result[0].time, "2025-10-22T23:04:53-04:00")
    
    def test_no_prediction_data(self):
        # When there is no prediction data in the JSON from the MBTA we should
        # fallback to using the schedule time
        mock_now = mock_now_func('2025-10-22T23:04:00-04:00')
        deps = TrainPredictorDependencies(network=None, datetime=datetime, nowFcn=mock_now)
        train_predictor = TrainPredictor(deps)

        data = load_test_schedule_json('simple_no_prediction.json')
        
        count = 1
        result = train_predictor._analyze_data(count, data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].direction, 0)
        self.assertEqual(result[0].time, "2025-10-22T23:06:00-04:00")

    def test_multiple_data_request_one_result(self):
        # There are multiple possible results that could be returned but only
        # one is requested
        mock_now = mock_now_func('2025-10-22T04:06:00-04:00')
        deps = TrainPredictorDependencies(network=None, datetime=datetime, nowFcn=mock_now)
        train_predictor = TrainPredictor(deps)

        data = load_test_schedule_json('multiple_results.json')
        
        count = 1
        result = train_predictor._analyze_data(count, data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].direction, 1)
        self.assertEqual(result[0].time, "2025-10-22T05:06:00-04:00")

    def test_multiple_data_request_more_results(self):
        # There are two possible results that could be returned but three are
        # requested
        mock_now = mock_now_func('2025-10-22T04:06:00-04:00')
        deps = TrainPredictorDependencies(network=None, datetime=datetime, nowFcn=mock_now)
        train_predictor = TrainPredictor(deps)

        data = load_test_schedule_json('multiple_results.json')
        
        count = 3
        result = train_predictor._analyze_data(count, data)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].direction, 1)
        self.assertEqual(result[0].time, "2025-10-22T05:06:00-04:00")
        self.assertEqual(result[1].direction, 0)
        self.assertEqual(result[1].time, "2025-10-22T06:06:00-04:00")
        self.assertEqual(result[2], None)

    def old_results_filtered(self):
        # There are multiple possible results that could be returned but only
        # one is requested
        mock_now = mock_now_func('2025-10-22T05:06:20-04:00')
        deps = TrainPredictorDependencies(network=None, datetime=datetime, nowFcn=mock_now)
        train_predictor = TrainPredictor(None, datetime, mock_now, filterResultsAfterSeconds=10)

        data = load_test_schedule_json('multiple_results.json')
        
        count = 3
        result = train_predictor._analyze_data(count, data)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].direction, 0)
        self.assertEqual(result[0].time, "2025-10-22T06:06:00-04:00")
        self.assertEqual(result[1], None)
        self.assertEqual(result[2], None)


    def test_data_array_empty(self):
        mock_now = mock_now_func('2025-10-22T23:04:00-04:00')
        deps = TrainPredictorDependencies(network=None, datetime=datetime, nowFcn=mock_now)
        train_predictor = TrainPredictor(deps)

        data = load_test_schedule_json('data_array_empty.json')
        
        count = 1
        result = train_predictor._analyze_data(count, data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], None)

    def test_no_data_property(self):
        mock_now = mock_now_func('2025-10-22T23:04:00-04:00')
        deps = TrainPredictorDependencies(network=None, datetime=datetime, nowFcn=mock_now)
        train_predictor = TrainPredictor(deps)

        data = load_test_schedule_json('no_data_property.json')
        
        count = 1
        result = train_predictor._analyze_data(count, data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], None)



if __name__ == '__main__':
    unittest.main()
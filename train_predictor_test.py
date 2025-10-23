from train_predictor import TrainPredictor
from datetime import datetime
import json
import os
import unittest


def mock_now_func(timeOfNow):
    return lambda : datetime.fromisoformat(timeOfNow).replace(tzinfo=None)

def load_test_schedule_json(file):
    current_file_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_file_directory, 'testdata', 'schedules', file)
    with open(file_path, 'r') as file:
        return json.load(file)

class Test_analyze_data(unittest.TestCase):
    def test_simple(self):
        mock_now = mock_now_func('2025-10-22T23:04:00-04:00')
        train_predictor = TrainPredictor(None, datetime, mock_now)

        data = load_test_schedule_json('simple.json')
        
        count = 1
        result = train_predictor._analyze_data(count, data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].direction, 0)

if __name__ == '__main__':
    unittest.main()
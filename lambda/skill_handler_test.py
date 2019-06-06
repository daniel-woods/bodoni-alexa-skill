import unittest
from json import dumps, loads
import skill_handler

with open('tests.json') as f:
    tests = loads(f.read())


class LaunchRequest(unittest.TestCase):
    def test_response(self):
        class_name = self.__class__.__name__
        print("START: {}".format(class_name))
        for test_case in tests[class_name]:
            event = test_case["input"]
            context = None
            result = skill_handler.handler(event, context)
            print("Response:\n{}".format(dumps(result, indent=4)))
            expected_response = test_case["output"]
            self.assertEqual(expected_response, result["response"])
        print("END: {}".format(class_name))


class HelpIntent(unittest.TestCase):
    def test_response(self):
        class_name = self.__class__.__name__
        print("START: {}".format(class_name))
        for test_case in tests[class_name]:
            event = test_case["input"]
            context = None
            result = skill_handler.handler(event, context)
            print("Response:\n{}".format(dumps(result, indent=4)))
            expected_response = test_case["output"]
            self.assertEqual(expected_response, result["response"])
        print("END: {}".format(class_name))


class MeetingIntent(unittest.TestCase):
    def test_response(self):
        class_name = self.__class__.__name__
        print("START: {}".format(class_name))
        for test_case in tests[class_name]:
            event = test_case['input']
            context = None
            result = skill_handler.handler(event, context)
            print("Response:\n{}".format(dumps(result, indent=4)))
            expected_response = test_case['output']
            self.assertEqual(expected_response, result["response"])
        print("END: {}".format(self.__class__.__name__))


if __name__ == '__main__':
    unittest.main()

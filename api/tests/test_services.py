import unittest
from unittest.mock import patch

# Import the actual classes we need to test and use
from api.services import OneShotAuthService, RedisAuthService


class MockState:
    def __init__(self, next_instance=None):
        self.next = next_instance

    def validator(self, x):
        return True  # simple validation

    def is_finish(self):
        return False

    def handle(self, value):
        if self.validator(value):
            return self.next or self  # go to next state
        return self

    def get_data(self, value):
        return value


class MockStateInput1(MockState):
    name = "mock input"


class MockStateInput2(MockState):
    name = "mock input 2"


class MockStateInput2Invalid(MockStateInput2):
    name = "mock input 2 invalid"

    def validator(self, x):
        raise ValueError("invalid validation!")


class MockStateComplete(MockState):
    name = "mock complete"

    def is_finish(self):
        return True


class MockStateCompleteInvalid(MockStateComplete):
    name = "mock complete invalid"

    def validator(self, x):
        raise ValueError("invalid validation!")


class MockBuilder:
    def build(self, data):
        return "build"


class MockRedisConn:
    def __init__(self):
        self.expiration = {}
        self.connection = {}

    def setex(self, ids, exp_time, data):
        print("saving in the connection")
        self.ids = ids
        self.connection[ids] = data
        self.expiration[ids] = exp_time

    def get(self, ids):
        return self.connection.get(ids)

    def delete(self, ids):
        if ids in self.connection:
            del self.connection[ids]
            del self.expiration[ids]


"""
The services take in a state flow that validates the data and the builder that perfroms the desired actoin on the data
"""

"""
Data:
There are two services. One shot and Redis MultiStep
One Shot --> give two input data
"""


@patch("api.services.get_redis_connection")
class RedisAuthServiceTests(unittest.TestCase):

    def setUp(self):
        self.builder = MockBuilder()
        self.data = {}

    def setUpRedis(self, MockRedisConnection):
        redis_conn = MockRedisConn()
        MockRedisConnection.return_value = redis_conn
        self.service = RedisAuthService()

    def test_successfull_flow(self, MockRedisConnection):
        redis_conn = MockRedisConn()
        MockRedisConnection.return_value = redis_conn
        self.service = RedisAuthService()

        state_flow = MockStateInput1(MockStateInput2(MockStateComplete(None)))

        self.data["data1"] = "data1"

        result = self.service.execute(self.data, self.builder, state_flow)
        print(result)

        self.assertTrue("message" in result)

        self.assertTrue("data1" in redis_conn.connection[redis_conn.ids])

        self.data["jwt"] = result["jwt"]
        self.data["data2"] = "data2"

        result = self.service.execute(self.data, self.builder, state_flow)

        self.assertTrue("create" in result)
        self.assertEqual(result, {"create": "build"})

        self.assertTrue(len(redis_conn.connection) == 0)

    def test_invalid_jwt(self, MockRedisConnection):
        redis_conn = MockRedisConn()
        MockRedisConnection.return_value = redis_conn
        self.service = RedisAuthService()

        state_flow = MockStateInput1(MockStateInput2(MockStateComplete(None)))

        self.data["jwt"] = "invalid jwt"

        result = self.service.execute(self.data, self.builder, state_flow)
        print(result, "result")
        self.assertTrue("errors" in result)


class OneShotAuthServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = OneShotAuthService()
        self.data = {"mock data 1": "momo", "mock data 2": "abucar"}
        self.builder = MockBuilder()

    def test_successfull_flow(self):
        state_flow = MockStateInput1(MockStateInput2(MockStateComplete(None)))

        result = self.service.execute(self.data, self.builder, state_flow)
        print("result", result)

        self.assertEqual(result, {"create": "build"})

        self.assertEqual(self.data, self.service.info)

    def test_invalid_process_step(self):
        state_flow = MockStateInput1(MockStateInput2(MockStateCompleteInvalid(None)))

        result = self.service.execute(self.data, self.builder, state_flow)

        self.assertTrue("errors" in result)
        self.assertEqual(self.data, self.service.info)

    def test_missing_data_step(self):
        state_flow = MockStateInput1(MockStateInput2(MockStateComplete(None)))

        del self.data["mock data 2"]

        result = self.service.execute(self.data, self.builder, state_flow)

        self.assertTrue("errors" in result)

        self.assertEqual(self.data, self.service.info)

    def test_invalid_data_input(self):
        state_flow = MockStateInput1(MockStateInput2Invalid(MockStateComplete(None)))

        result = self.service.execute(self.data, self.builder, state_flow)

        self.assertTrue("errors" in result)

        self.assertEqual(self.data == self.service.info, False)

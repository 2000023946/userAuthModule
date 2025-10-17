import json
from abc import ABC, abstractmethod
from django_redis import get_redis_connection
from .utils import get_transaction_id, create_jwt, decode_jwt
from .tracers import trace


# ------------------------------------------------------------------
# SERVICE INTERFACE
# ------------------------------------------------------------------


class Servicable(ABC):
    """Unified interface for all service classes."""

    @abstractmethod
    def execute(self, data, builder, initial_state):
        """Process data using builder and state machine."""
        pass


# ------------------------------------------------------------------
# BASE AUTH SERVICE
# ------------------------------------------------------------------


class AuthService(Servicable):
    """
    Template method for processing a state machine workflow.
    """

    @trace(lambda self: f"{self.__class__.__name__}_post")
    def execute(self, data, builder, initial_state):
        print("executing")
        try:
            self._initialize(data, builder, initial_state)
        except Exception as e:
            self.errors["initialization"] = str(e)
            return self._get_result()

        state_inputs = {k: v for k, v in data.items() if k != "jwt"}

        if self.errors:
            return self._get_result()
        print(state_inputs, self.state.next)
        for key, value in state_inputs.items():
            print("k", key, "val", value, "state", self.state.name)
            step_result = self._process_step(key, value)
            if not step_result["success"]:
                break
            print("res", step_result)
            self._save(key, step_result["output"])
            self._advance(step_result["next_state"])

        if self.state.is_finish():
            print("fnished", "info", self.info)
            final_result = self._process_step("final", self.info)

            if final_result["success"]:
                print("scuess")
                self._on_successful_finish()
                try:
                    print("now buildign..", final_result["output"])
                    self.result = {"create": self.builder.build(final_result["output"])}
                    print(self.result, "good finsih")
                except Exception as e:
                    self.errors["builder_exception"] = str(e)

        self._on_finish_execution()
        return self._get_result()

    # ---------------------
    # Hooks / helpers
    # ---------------------

    def _initialize(self, data, builder, initial_state):
        if not data:
            raise ValueError("Data cannot be null")
        self.builder = builder
        self.state = initial_state
        self.errors = {}
        self.result = {}
        self.info = {}

    def _process_step(self, key, value):
        """Process a single step in the state machine."""
        try:
            next_state = self.state.handle(value)
            print("next state", next_state)
            output = getattr(self.state, "get_data", lambda v: v)(value)
            print(self.state.get_data(value), "outp98put")
            return {"success": True, "output": output, "next_state": next_state}
        except Exception as e:
            self.errors[self.state.name] = str(e)
            return {"success": False, "output": None, "next_state": None}

    def _save(self, key, value):
        self.info[key] = value

    def _advance(self, next_state):
        if next_state:
            self.state = next_state

    def _on_finish_execution(self):
        pass

    def _on_successful_finish(self):
        pass

    def _get_extra_msg(self):
        return None

    def _get_result(self):
        if self.errors:
            return {"errors": self.errors}
        if self.result:
            return self.result
        return self._get_extra_msg()


# ------------------------------------------------------------------
# REDIS-STATEFUL SERVICE
# ------------------------------------------------------------------


class RedisAuthService(AuthService):
    def __init__(self, redis_conn=None):
        self.redis_conn = redis_conn or get_redis_connection("default")

    def _initialize(self, data, builder, initial_state):
        super()._initialize(data, builder, initial_state)
        starting_state_name = self._load(data)
        print("init service", starting_state_name)
        if starting_state_name:
            current = initial_state
            while current and not current.__eq__(starting_state_name):
                current = current.next
            if not current:
                raise ValueError("Invalid state!")
            self.state = current
            print("starting at ", self.state.name)

    def _on_finish_execution(self):
        if not self.state.is_finish():
            self.redis_conn.setex(self.id, 600, json.dumps(self.info))

    def _on_successful_finish(self):
        if hasattr(self, "id"):
            self.redis_conn.delete(self.id)

    def _get_extra_msg(self):
        if not self.state.is_finish() and not self.errors:
            jwt_token = create_jwt({"id": self.id, "state": self.state.name})
            return {"message": f"Continue at state {self.state.name}", "jwt": jwt_token}
        return self.errors

    def _load(self, data):
        print("data", data)
        if "jwt" in data:
            try:
                token = decode_jwt(data["jwt"])
                self.id = token["id"]
                cached = self.redis_conn.get(self.id)
                if cached:
                    self.info = json.loads(cached)
                return token.get("state")
            except Exception as e:
                self.errors["jwt_error"] = str(e)
        else:
            self.id = get_transaction_id()
            return None


# ------------------------------------------------------------------
# ONE-SHOT SERVICE
# ------------------------------------------------------------------


class OneShotAuthService(AuthService):
    """Handles workflows completed in a single execution."""

    def _on_finish_execution(self):
        if not self.state.is_finish():
            self.errors["input_data"] = "Missing required data!"

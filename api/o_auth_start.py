import requests
from abc import ABC, abstractmethod


class ThirdPartyStrategy(ABC):
    @abstractmethod
    def get_user_info(self, token):
        pass


class GoogleStrategy(ThirdPartyStrategy):
    def get_user_info(self, token):
        google_verify_url = "https://oauth2.googleapis.com/tokeninfo"
        resp = self.get_response(google_verify_url, token)
        if resp.status_code != 200:
            raise ValueError("Invalid Google token")

        payload = resp.json()
        return {
            "email": payload["email"],
            "username": payload.get("name", ""),
        }

    def get_response(self, url, token):
        return requests.get(url, params={"id_token": token})


class ThirdPartyStrategySingleton:
    strategies = {"google": GoogleStrategy}

    @classmethod
    def get_user_info(cls, provider, token):
        return cls.strategies[provider]().get_user_info(token)

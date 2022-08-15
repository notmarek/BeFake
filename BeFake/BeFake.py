from base64 import b64decode
import json
import httpx
import pendulum
import hashlib
from models.user import User


class BeFake:
    def __init__(
        self,
        refresh_token=None,
        api_url="https://mobile.bereal.com/api",
        google_api_key="AIzaSyDwjfEeparokD7sXPVQli9NsTuhT6fJ6iA",
    ) -> None:
        self.client = httpx.Client(
            headers={
                "user-agent": "AlexisBarreyat.BeReal/0.23.2 iPhone/16.0 hw/iPhone13_2",
                "x-ios-bundle-identifier": "AlexisBarreyat.BeReal",
            },
        )
        self.gapi_key = google_api_key
        self.api_url = api_url

        if refresh_token is not None:
            self.refresh_token = refresh_token
            self.refresh_tokens()

    def __repr__(self):
        return f"BeFake(user_id={self.user_id})"

    def save(self, file_path: str) -> None:
        with open(file_path, "w") as f:
            f.write(self.refresh_token)

    def load(self, file_path: str) -> None:
        with open(file_path, "r") as f:
            self.refresh_token = f.read()
            self.refresh_tokens()

    def send_otp(self, phone: str) -> None:
        self.phone = phone
        res = self.client.post(
            "https://www.googleapis.com/identitytoolkit/v3/relyingparty/sendVerificationCode",
            params={"key": self.gapi_key},
            data={
                "phoneNumber": phone,
                "iosReceipt": "AEFDNu9QZBdycrEZ8bM_2-Ei5kn6XNrxHplCLx2HYOoJAWx-uSYzMldf66-gI1vOzqxfuT4uJeMXdreGJP5V1pNen_IKJVED3EdKl0ldUyYJflW5rDVjaQiXpN0Zu2BNc1c",
            },
        ).json()
        self.otp_session = res["sessionInfo"]

    def verify_otp(self, otp: str) -> None:
        if self.otp_session is None:
            raise Exception("No open otp session.")
        res = self.client.post(
            "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPhoneNumber",
            params={"key": self.gapi_key},
            data={
                "sessionInfo": self.otp_session,
                "code": otp,
                "operation": "SIGN_UP_OR_IN",
            },
        ).json()

        self.token = res["idToken"]
        self.token_info = json.loads(b64decode(res["idToken"].split(".", 3)[1]))
        self.refresh_token = res["refreshToken"]
        self.expiration = pendulum.now().add(seconds=int(res["expiresIn"]))
        self.user_id = res["localId"]
        self.phone = res["phoneNumber"]

    def refresh_tokens(self) -> None:
        if self.refresh_token is None:
            raise Exception("No refresh token.")
        res = self.client.post(
            "https://securetoken.googleapis.com/v1/token",
            params={"key": self.gapi_key},
            data={"refresh_token": self.refresh_token, "grant_type": "refresh_token"},
        ).json()
        self.token = res["id_token"]
        self.token_info = json.loads(b64decode(res["id_token"].split(".", 3)[1]))
        self.refresh_token = res["refresh_token"]
        self.expiration = pendulum.now().add(seconds=int(res["expires_in"]))
        self.user_id = res["user_id"]

    def get_user_info(self):
        res = self.client.get(
            f"{self.api_url}/person/me",
            headers={
                "authorization": self.token,
            },
        ).json()
        return User(res, self)

    def get_friends_feed(self):
        res = self.client.get(
            f"{self.api_url}/feeds/friends",
            headers={
                "authorization": self.token,
            },
        ).json()
        return res

    def get_discovery_feed(self):
        res = self.client.get(
            f"{self.api_url}/feeds/discovery",
            headers={
                "authorization": self.token,
            },
        ).json()
        return res

    def get_memories_feed(self):
        res = self.client.get(
            f"{self.api_url}/feeds/memories",
            headers={
                "authorization": self.token,
            },
        ).json()
        return res

    def delete_memory(self, memory_id: str):
        res = self.client.delete(
            f"{self.api_url}/memories/{memory_id}",
            headers={
                "authorization": self.token,
            },
        ).json()
        return res

    def get_memories_video(self):
        res = self.client.get(
            f"{self.api_url}/memories/video",
            headers={
                "authorization": self.token,
            },
        ).json()
        return res

    def delete_video_memory(self, memory_id: str):
        res = self.client.delete(
            f"{self.api_url}/memories/video/{memory_id}",
            headers={
                "authorization": self.token,
            },
        ).json()
        return res

    def add_friend(self, user_id: str):
        res = self.client.post(
            f"{self.api_url}/relationships/friend-requests",
            headers={
                "authorization": self.token,
            },
            data={
                "userId": user_id,
                "source": "contact",
            },
        ).json()
        return res

    def get_friends(self):
        res = self.client.get(
            f"{self.api_url}/relationships/friends",
            headers={
                "authorization": self.token,
            },
        ).json()
        return [User(friend, self) for friend in res["data"]]

    def get_friend_suggestions(self):
        res = self.client.get(
            f"{self.api_url}/relationships/suggestions",
            headers={
                "authorization": self.token,
            },
        ).json()
        return [User(suggestion, self) for suggestion in res["data"]]

    def get_friend_requests(self, req_type: str):
        res = self.client.get(
            f"{self.api_url}/relationships/friend-requests/{req_type}",
            headers={
                "authorization": self.token,
            },
        ).json()
        return [User(user, self) for user in res["data"]]

    def get_sent_friend_requests(self):
        return self.get_friend_requests("sent")

    def get_received_friend_requests(self):
        return self.get_friend_requests("received")

    def get_users_by_phone_number(self, phone_numbers):
        hashed_phone_numbers = [
            hashlib.sha256(phone_number.encode("utf-8")).hexdigest()
            for phone_number in phone_numbers
        ]
        res = self.client.post(
            f"{self.api_url}/relationships/contacts",
            headers={
                "authorization": self.token,
            },
            data={
                "phoneNumbers": hashed_phone_numbers,
            },
        ).json()
        return [User(user, self) for user in res]

    def get_user_by_phone_number(self, phone_number: str):
        return self.get_users_by_phone_number([phone_number])[0]

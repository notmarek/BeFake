from base64 import b64decode
import json
import httpx
import pendulum


class BeFake:
    def __init__(self, refresh_token=None) -> None:
        self.client = httpx.Client(
            headers={
                "user-agent": "AlexisBarreyat.BeReal/0.23.2 iPhone/16.0 hw/iPhone13_2",
                "x-ios-bundle-identifier": "AlexisBarreyat.BeReal",
            },
        )
        if refresh_token is not None:
            self.refreshToken = refresh_token
            self.refresh_token()

    def save(self, file_path: str) -> None:
        with open(file_path, "w") as f:
            f.write(self.refreshToken)

    def load(self, file_path: str) -> None:
        with open(file_path, "r") as f:
            self.refreshToken = f.read()
            self.refresh_token()

    def send_otp(self, phone: str) -> None:
        self.phone = phone
        res = self.client.post(
            "https://www.googleapis.com/identitytoolkit/v3/relyingparty/sendVerificationCode",
            params={"key": "AIzaSyDwjfEeparokD7sXPVQli9NsTuhT6fJ6iA"},
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
            params={"key": "AIzaSyDwjfEeparokD7sXPVQli9NsTuhT6fJ6iA"},
            data={
                "sessionInfo": self.otp_session,
                "code": otp,
                "operation": "SIGN_UP_OR_IN",
            },
        ).json()

        self.token = res["idToken"]
        self.tokenInfo = json.loads(b64decode(res["idToken"].split(".", 3)[1]))
        self.refreshToken = res["refreshToken"]
        self.expiration = pendulum.now().add(seconds=int(res["expiresIn"]))
        self.localId = res["localId"]
        self.phone = res["phoneNumber"]

    def refresh_token(self) -> None:
        if self.refreshToken is None:
            raise Exception("No refresh token.")
        res = self.client.post(
            "https://securetoken.googleapis.com/v1/token",
            params={"key": "AIzaSyDwjfEeparokD7sXPVQli9NsTuhT6fJ6iA"},
            data={"refresh_token": self.refreshToken, "grant_type": "refresh_token"},
        ).json()
        self.token = res["id_token"]
        self.tokenInfo = json.loads(b64decode(res["id_token"].split(".", 3)[1]))
        self.refreshToken = res["refresh_token"]
        self.expiration = pendulum.now().add(seconds=int(res["expires_in"]))

    def get_friends_feed(self):
        res = self.client.get(
            "https://mobile.bereal.com/api/feeds/friends",
            headers={
                "authorization": self.token,
            },
        ).json()
        return res

    def get_memories_feed(self):
        res = self.client.get(
            "https://mobile.bereal.com/api/feeds/memories",
            headers={
                "authorization": self.token,
            },
        ).json()
        return res

    def get_friends(self):
        res = self.client.get(
            "https://mobile.bereal.com/api/relationships/friends",
            headers={
                "authorization": self.token,
            },
        ).json()
        return res

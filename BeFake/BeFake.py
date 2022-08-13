from base64 import b64decode
import json
import httpx


class BeFake:
    def __init__(self) -> None:
        self.client = httpx.Client(
            headers={
                "user-agent": "AlexisBarreyat.BeReal/0.23.2 iPhone/16.0 hw/iPhone13_2",
                "x-ios-bundle-identifier": "AlexisBarreyat.BeReal",
            },
        )

    def send_otp(self, phone: str) -> None:
        self.phone = phone
        self.otp_session = self.client.post(
            "https://www.googleapis.com/identitytoolkit/v3/relyingparty/sendVerificationCode",
            params={"key": "AIzaSyDwjfEeparokD7sXPVQli9NsTuhT6fJ6iA"},
            data={
                "phoneNumber": phone,
                "iosReceipt": "AEFDNu9QZBdycrEZ8bM_2-Ei5kn6XNrxHplCLx2HYOoJAWx-uSYzMldf66-gI1vOzqxfuT4uJeMXdreGJP5V1pNen_IKJVED3EdKl0ldUyYJflW5rDVjaQiXpN0Zu2BNc1c",
            },
        ).json()["sessionInfo"]

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
        self.expiresIn = res["expiresIn"]
        self.localId = res["localId"]
        self.phone = res["phoneNumber"]

    def refresh_token(self) -> None:
        if self.refreshToken is None:
            raise Exception("No refresh token.")
        res = self.client.post(
            "https://securetoken.googleapis.com/v1/token",
            params={"key": "AIzaSyDwjfEeparokD7sXPVQli9NsTuhT6fJ6iA"},
        ).json()
        self.token = res["idToken"]
        self.tokenInfo = json.loads(b64decode(res["idToken"].split(".", 3)[1]))
        self.refreshToken = res["refreshToken"]
        self.expiresIn = res["expiresIn"]
        self.localId = res["localId"]

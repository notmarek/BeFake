import urllib.parse
from base64 import b64decode
import json
from typing import Optional

import httpx
import pendulum
import hashlib
import platform
import os
from pathlib import Path
from .models.realmoji_picture import RealmojiPicture

from .models.post import Post, FOFPost
from .models.memory import Memory
from .models.user import User


def _get_config_dir() -> Path:
    """Modified from source: Instaloader (MIT License)
    https://github.com/instaloader/instaloader/blob/3cc29a4/instaloader/instaloader.py#L30-L39"""
    if platform.system() == "Windows":
        # on Windows, use %LOCALAPPDATA%\BeFake
        localappdata = os.getenv("LOCALAPPDATA")
        if localappdata is not None:
            return Path(localappdata) / "BeFake"
    # on Unix, use ~/.config/befake
    return Path.home() / ".config" / "befake"


def get_default_session_filename() -> Path:
    """Returns default token filename for given phone number.
    Modified from source: Instaloader (MIT License)
    https://github.com/instaloader/instaloader/blob/3cc29a4/instaloader/instaloader.py#L42-L46"""

    if os.environ.get('IS_DOCKER', False):
        return Path('/data/token.txt')

    config_dir = _get_config_dir()
    token_filename = f"token.txt"
    return config_dir / token_filename


class BeFake:
    def __init__(
            self,
            refresh_token: Optional[str] = None,
            proxies=None,
            disable_ssl=False,
            deviceId=None,
            api_url="https://mobile.bereal.com/api",
            google_api_key="AIzaSyDwjfEeparokD7sXPVQli9NsTuhT6fJ6iA",
    ) -> None:
        self.client = httpx.Client(
            proxies=proxies,
            verify=not disable_ssl,
            headers={
                # "user-agent": "AlexisBarreyat.BeReal/0.24.0 iPhone/16.0.2 hw/iPhone12_8 (GTMSUF/1)",
                "user-agent": "BeReal/0.35.0 (iPhone; iOS 16.0.2; Scale/2.00)",
                "x-ios-bundle-identifier": "AlexisBarreyat.BeReal",
            },
        )
        self.gapi_key = google_api_key
        self.api_url = api_url
        self.deviceId = deviceId
        if refresh_token is not None:
            self.refresh_token = refresh_token
            self.refresh_tokens()

    def __repr__(self):
        return f"BeFake(user_id={self.user_id})"

    def save(self, file_path: Optional[Path] = None) -> None:
        if file_path is None:
            file_path = get_default_session_filename()
        if not file_path.parent.exists():
            file_path.parent.mkdir(mode=700, parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            file_path.chmod(0o600)
            f.write(self.refresh_token)

    def load(self, file_path: Optional[Path] = None) -> None:
        if file_path is None:
            file_path = get_default_session_filename()
        with open(file_path, "r") as f:
            self.refresh_token = str(f.read()).strip()
            self.refresh_tokens()

    def api_request(self, method: str, endpoint: str, **kwargs) -> dict:
        assert not endpoint.startswith("/")
        res = self.client.request(
            method,
            f"{self.api_url}/{endpoint}",
            headers={"authorization": self.token},
            **kwargs,
        )
        res.raise_for_status()
        # TODO: Include error message in exception
        return res.json()

    def send_otp_firebase(self, phone: str) -> None:  # iOS Firebase OTP
        res = self.client.post(
            "https://www.googleapis.com/identitytoolkit/v3/relyingparty/sendVerificationCode",
            params={"key": self.gapi_key},
            data={
                "phoneNumber": phone,
                "iosReceipt": "AEFDNu9QZBdycrEZ8bM_2-Ei5kn6XNrxHplCLx2HYOoJAWx-uSYzMldf66-gI1vOzqxfuT4uJeMXdreGJP5V1pNen_IKJVED3EdKl0ldUyYJflW5rDVjaQiXpN0Zu2BNc1c",
            },
        ).json()
        self.otp_session = res["sessionInfo"]

    def get_recaptcha_url(self):
        validUrlRes = self.client.get("https://www.googleapis.com/identitytoolkit/v3/relyingparty/getProjectConfig",
                                      params={"key": self.gapi_key}).json()
        recaptcha_instances = validUrlRes["authorizedDomains"]
        payload = {'apiKey': self.gapi_key, 'authType': 'verifyApp',
                   'apn': 'com.bereal.ft', 'v': 'XX21001000', 'eid': 'p',
                   'appName': '[DEFAULT]', 'sha1Cert': '1d14ab0c48b1b2ad252c79d65f48bae37aefe8bb',
                   'publicKey': 'CKHQydkDEtsBCs4BCj10eXBlLmdvb2dsZWFwaXMuY29tL2dvb2dsZS5jcnlwdG8udGluay5FY2ll\nc0FlYWRIa2RmUHVibGljS2V5EooBEkQKBAgCEAMSOhI4CjB0eXBlLmdvb2dsZWFwaXMuY29tL2dv\nb2dsZS5jcnlwdG8udGluay5BZXNHY21LZXkSAhAQGAEYARogDBxbrkTTsYg1gvrVOX-qAi4i64nb\n_d_VC_WLuZuJ98oiIAVLfq0TkXxNNDATcMIb2OjBdxyJtqAkUMdU6kNGqjn1GAMQARih0MnZAyAB'}

        return "https://" + recaptcha_instances[1] + "/__/auth/handler?" + urllib.parse.urlencode(payload)

    def send_otp_recaptcha(self, recaptchaToken: str, phone: str):  #
        payload = {
            "phoneNumber": phone,
            "recaptchaToken": recaptchaToken,
        }

        res = self.client.post(
            "https://www.googleapis.com/identitytoolkit/v3/relyingparty/sendVerificationCode",
            params={"key": self.gapi_key},
            data=payload).json()
        self.otp_session = res["sessionInfo"]

    def send_otp_vonage(self, phone: str) -> None:
        self.phone = phone
        data = {
            "phoneNumber": phone,
            "deviceId": self.deviceId
        }
        vonageRes = self.client.post(
            "https://auth.bereal.team/api/vonage/request-code",
            headers={
                "user-agent": "BeReal/8586 CFNetwork/1240.0.4 Darwin/20.6.0",
            },
            data=data)
        if vonageRes.json()["status"] != '0':
            print("WARNING: " + vonageRes.json()["errorText"])
            print("If you already received a code before, ignore the warning and enter it.")
        if vonageRes.status_code == 200:
            self.otp_session = vonageRes.json()["vonageRequestId"]

    def verify_otp_firebase(self, otp: str) -> None:
        if self.otp_session is None:
            raise Exception("No open otp session (firebase).")

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
        self.token_info = json.loads(b64decode(res["idToken"].split(".")[1] + '=='))
        self.refresh_token = res["refreshToken"]
        self.expiration = pendulum.now().add(seconds=int(res["expiresIn"]))
        self.user_id = res["localId"]
        self.phone = res["phoneNumber"]

    def verify_otp_vonage(self, otp: str) -> None:
        if self.otp_session is None:
            raise Exception("No open otp session (vonage).")
        vonageRes = self.client.post("https://auth.bereal.team/api/vonage/check-code", data={
            "code": otp,
            "vonageRequestId": self.otp_session
        })
        # TODO: better error handling and retries
        if vonageRes.status_code not in [200, 201]:
            print("Error: " + vonageRes.json()["statusCode"] + vonageRes.json()["message"])
            print("Make sure you entered the right code")
        vonageRes = vonageRes.json()
        res = self.client.post("https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyCustomToken",
                               params={"key": self.gapi_key}, data={
                "token": vonageRes["token"],
                "returnSecureToken": True
            }).json()
        self.token = res["idToken"]
        self.token_info = json.loads(b64decode(res["idToken"].split(".")[1] + '=='))
        self.refresh_token = res["refreshToken"]
        self.expiration = pendulum.now().add(seconds=int(res["expiresIn"]))

    def refresh_tokens(self) -> None:
        if self.refresh_token is None:
            raise Exception("No refresh token.")
        res = self.client.post(
            "https://securetoken.googleapis.com/v1/token",
            params={"key": self.gapi_key},
            data={"refresh_token": self.refresh_token, "grant_type": "refresh_token"},
        ).json()
        self.token = res["id_token"]
        self.token_info = json.loads(b64decode(res["id_token"].split(".")[1] + '=='))
        self.refresh_token = res["refresh_token"]
        self.expiration = pendulum.now().add(seconds=int(res["expires_in"]))
        self.user_id = res["user_id"]

    def get_user_info(self):
        res = self.api_request("get", "person/me")
        return User(res, self)

    def get_user_profile(self, user_id):
        # here for example we have a firebase-instance-id-token header with the value from the next line, that we can just ignore (but maybe we need it later, there seem to be some changes to the API especially endpoints moving tho the cloudfunctions.net server)
        # cTn8odwxQo6DR0WFVnM9TJ:APA91bGV86nmQUkqnLfFv18IhpOak1x02sYMmKvpUAqhdfkT9Ofg29BXKXS2mbt9oE-LoHiiKViXw75xKFLeOxhb68wwvPCJF79z7V5GbCsIQi7XH1RSD8ItcznqM_qldSDjghf5N8Uo
        res = self.client.get(f"{self.api_url}/person/profiles/{user_id}",
                              headers={"authorization": f"Bearer {self.token}"}).json()
        return User(res, self)

    def get_friends_feed(self):
        res = self.api_request("get", "feeds/friends")
        return [Post(p, self) for p in res]

    def get_fof_feed(self):  # friends of friends feed
        res = self.api_request("get", "feeds/friends-of-friends")
        return [FOFPost(p, self) for p in res["data"]]

    def get_discovery_feed(self):
        res = self.api_request("get", "feeds/discovery")
        return [Post(p, self) for p in res["posts"]]

    def get_memories_feed(self):
        res = self.api_request("get", "feeds/memories")
        return [Memory(mem, self) for mem in res["data"]]

    def delete_memory(self, memory_id: str):
        res = self.api_request("delete", f"memories/{memory_id}")
        return res

    def delete_post(self):
        res = self.api_request("delete", "content/posts")
        return res

    def get_memories_video(self):
        res = self.api_request("get", f"memories/video")
        return res

    def delete_video_memory(self, memory_id: str):
        res = self.api_request("delete", f"memories/video/{memory_id}")
        return res

    def add_friend(self, user_id: str, source: str):
        res = self.api_request("post",
                               "relationships/friend-requests",
                               data={
                                   "userId": user_id,
                                   "source": source,
                               },
                               )
        return User(res, self)

    def get_friends(self):
        res = self.api_request("get", f"relationships/friends")
        return [User(friend, self) for friend in res["data"]]

    def get_friend_suggestions(self):
        res = self.api_request("get", f"relationships/suggestions")
        return [User(suggestion, self) for suggestion in res["data"]]

    def get_friend_requests(self, req_type: str):
        res = self.api_request("get", f"relationships/friend-requests/{req_type}")
        return [User(user, self) for user in res["data"]]

    def get_sent_friend_requests(self):
        return self.get_friend_requests("sent")

    def get_received_friend_requests(self):
        return self.get_friend_requests("received")

    def remove_friend_request(self, userId):
        res = self.api_request("patch", f"relationships/friend-requests/{userId}", data={"status": "cancelled"})
        return User(res, self)

    def get_users_by_phone_numbers(self, phone_numbers):
        hashed_phone_numbers = [
            hashlib.sha256(phone_number.encode("utf-8")).hexdigest()
            for phone_number in phone_numbers
        ]
        res = self.api_request("post",
                               "relationships/contacts",
                               data={
                                   "phoneNumbers": hashed_phone_numbers,
                               },
                               )
        return [User(user, self) for user in res]

    def get_user_by_phone_number(self, phone_number: str):
        return self.get_users_by_phone_numbers([phone_number])[0]

    def send_capture_in_progress_push(self, topic=None, username=None):
        topic = topic if topic else self.user_id
        username = username if username else self.get_user_info().username
        res = self.client.post(
            "https://us-central1-alexisbarreyat-bereal.cloudfunctions.net/sendCaptureInProgressPush",
            headers={
                "authorization": f"Bearer {self.token}",
            },
            json={"data": {
                "photoURL": "",
                "topic": topic,
                "username": username
            }}
        ).json()
        return res

    def change_caption(self, caption: str):
        res = self.api_request("patch", f"content/posts/caption", data={"caption": caption})
        return res

    def upload(self, data: bytes):  # Broken?
        file = RealmojiPicture({})
        file.upload(self, data)
        print(file.url)
        return file

    def take_screenshot(self, post_id):
        payload = {
            "postId": post_id,
        }
        res = self.client.post(f"{self.api_url}/content/screenshots", params=payload,
                               headers={"authorization": self.token})
        return res.content

    def add_comment(self, post_id, comment):
        payload = {
            "postId": post_id,
        }
        data = {
            "content": comment,
        }
        res = self.api_request("post", "content/comments", params=payload, data=data)
        return res

    def delete_comment(self, post_id, comment_id):
        payload = {
            "postId": post_id,
        }
        data = {
            "commentIds": comment_id,
        }
        res = self.api_request("delete", "content/comments", params=payload, data=data)
        return res

    def upload_realmoji(self, image_file: bytes, emoji_type: str):
        picture = RealmojiPicture({})
        path = picture.upload(self, image_file)
        emojis = {
            "up": "👍",
            "happy": "😃",
            "surprised": "😲",
            "laughing": "😍",
            "heartEyes": "😂"
        }
        if emoji_type not in emojis:
            raise ValueError("Not a valid emoji type")

        data = {
            "media": {
                "bucket": "storage.bere.al",
                "path": path,
                "width": picture.width,
                "height": picture.height
            },
            "emoji": emojis[emoji_type]
        }

        res = self.api_request("put", "person/me/realmojis", data=data, headers={"authorization": self.token})
        return res

    # IT WORKS!!!!

    def post_realmoji(
            self,
            post_id: str,
            user_id: str,
            emoji_type: str,
    ):
        emojis = {
            "up": "👍",
            "happy": "😃",
            "surprised": "😲",
            "laughing": "😍",
            "heartEyes": "😂"
        }
        if emoji_type not in emojis:
            raise ValueError("Not a valid emoji type")

        payload = {
            "postId": post_id,
            "postUserId": user_id
        }

        json_data = {
            "emoji": emojis[emoji_type]
        }
        res = self.api_request("put", f"/content/realmojis", params=payload,
                               json=json_data)
        return res

    def post_instant_realmoji(self, post_id: str, owner_id: str, image_file: bytes):
        picture = RealmojiPicture({})
        path = picture.upload(self, image_file)
        json_data = {
            "media": {
                "bucket": "storage.bere.al",
                "path": path,
                "width": 500,
                "height": 500
            }
        }
        payload = {
            "postId": post_id,
            "postUserId": owner_id
        }

        res = self.client.put("https://mobile.bereal.com/api/content/realmojis/instant", params=payload,
                              content=json.dumps(json_data), headers={"authorization": f"Bearer {self.token}",
                                                                      "content-type": "application/json;charset=utf-8"})
        return res.json()

    # works also for not friends and unpublic post with given post_id
    def get_reactions(self, post_id):
        payload = {
            "postId": post_id,
        }
        res = self.api_request("get", f"content/realmojis",
                               params=payload,
                               )
        return res

    def search_username(self, username):
        res = self.api_request("get", f"search/profile", params={"query": username})
        return [User(user, self) for user in res["data"]]

    def get_settings(self):
        res = self.api_request("get", f"settings")
        return res

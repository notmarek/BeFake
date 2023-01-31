from base64 import b64decode
import json
from typing import Optional

import httpx
import pendulum
import hashlib
import platform
import os
from .models.picture import Picture
from .models.realmoji_picture import RealmojiPicture

from .models.post import Post
from .models.memory import Memory
from .models.user import User


def _get_config_dir() -> str:
    """Source: Instaloader (MIT License)
    https://github.com/instaloader/instaloader/blob/3cc29a4/instaloader/instaloader.py#L30-L39"""
    if platform.system() == "Windows":
        # on Windows, use %LOCALAPPDATA%\BeFake
        localappdata = os.getenv("LOCALAPPDATA")
        if localappdata is not None:
            return os.path.join(localappdata, "BeFake")
    # on Unix, use ~/.config/befake
    return os.path.join(os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "befake")


def get_default_session_filename() -> str:
    """Returns default token filename for given phone number.
    Source: Instaloader (MIT License)
    https://github.com/instaloader/instaloader/blob/3cc29a4/instaloader/instaloader.py#L42-L46"""

    if os.environ.get('IS_DOCKER', False):
        return '/data/token.txt'

    config_dir = _get_config_dir()
    token_filename = f"token.txt"
    return os.path.join(config_dir, token_filename)


class BeFake:
    def __init__(
            self,
            refresh_token=None,
            proxies=None,
            disable_ssl=False,
            api_url="https://mobile.bereal.com/api",
            google_api_key="AIzaSyDwjfEeparokD7sXPVQli9NsTuhT6fJ6iA",
    ) -> None:
        self.client = httpx.Client(
            proxies=proxies,
            verify=not disable_ssl,
            headers={
                # "user-agent": "AlexisBarreyat.BeReal/0.24.0 iPhone/16.0.2 hw/iPhone12_8 (GTMSUF/1)",
                "user-agent": "BeReal/0.25.1 (iPhone; iOS 16.0.2; Scale/2.00)",
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

    def save(self, file_path: Optional[str] = None) -> None:
        if file_path is None:
            file_path = get_default_session_filename()
        dirname = os.path.dirname(file_path)
        if dirname != '' and not os.path.exists(dirname):
            os.makedirs(dirname)
            os.chmod(dirname, 0o700)
        with open(file_path, "w") as f:
            os.chmod(file_path, 0o600)
            f.write(self.refresh_token)

    def load(self, file_path: Optional[str] = None) -> None:
        if file_path is None:
            file_path = get_default_session_filename()
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
        self.token_info = json.loads(b64decode(res["idToken"].split(".")[1] + '=='))
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
        self.token_info = json.loads(b64decode(res["id_token"].split(".")[1] + '=='))
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

    def get_user_profile(self, user_id):
        payload = {
            "data": {
                "uid": user_id
            }
        }
        # here for example we have a firebase-instance-id-token header with the value from the next line, that we can just ignore (but maybe we need it later, there seem to be some changes to the API especially endpoints moving tho the cloudfunctions.net server)
        # cTn8odwxQo6DR0WFVnM9TJ:APA91bGV86nmQUkqnLfFv18IhpOak1x02sYMmKvpUAqhdfkT9Ofg29BXKXS2mbt9oE-LoHiiKViXw75xKFLeOxhb68wwvPCJF79z7V5GbCsIQi7XH1RSD8ItcznqM_qldSDjghf5N8Uo
        res = self.client.post("https://us-central1-alexisbarreyat-bereal.cloudfunctions.net/getUserProfile",
                               json=payload,
                               headers={"authorization": f"Bearer {self.token}"}
                               )
        return res.json()

    def get_friends_feed(self):
        res = self.client.get(
            f"{self.api_url}/feeds/friends",
            headers={
                "authorization": self.token,
            },
        ).json()
        return [Post(p, self) for p in res]

    def get_discovery_feed(self):
        res = self.client.get(
            f"{self.api_url}/feeds/discovery",
            headers={
                "authorization": self.token,
            },
        ).json()
        return [Post(p, self) for p in res["posts"]]

    def get_memories_feed(self):
        res = self.client.get(
            f"{self.api_url}/feeds/memories",
            headers={
                "authorization": self.token,
            },
        ).json()
        return [Memory(mem, self) for mem in res["data"]]

    def delete_memory(self, memory_id: str):
        res = self.client.delete(
            f"{self.api_url}/memories/{memory_id}",
            headers={
                "authorization": self.token,
            },
        ).json()
        return res

    def delete_post(self):
        res = self.client.post(
            "https://us-central1-alexisbarreyat-bereal.cloudfunctions.net/deleteBeReal",
            headers={
                "authorization": f"Bearer {self.token}",
            },
            json={"data": {"uid": None}}
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
        res = self.client.post(
            "https://us-central1-alexisbarreyat-bereal.cloudfunctions.net/setCaptionPost",
            headers={
                "authorization": f"Bearer {self.token}",
            },
            json={"data": {"caption": caption}}
        ).json()
        return res

    def upload(self, data: bytes):
        file = Picture({})
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
        res = self.client.post(f"{self.api_url}/content/comments", params=payload, data=data,
                               headers={"authorization": self.token})
        return res.json()

    def upload_realmoji(self, image_file: bytes, emoji_type: str):
        picture = RealmojiPicture({})
        name = picture.upload(self, image_file, emoji_type)
        return name

    # currently gives server errors
    def post_realmoji(
            self,
            post_id: str,
            emoji_type: str,
            name: str
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
        emoji = emojis.get(emoji_type, "👍")
        json_data = {
            "data": {
                "action": "add",
                "emoji": emoji,
                "ownerId": self.user_id,
                "photoId": post_id,
                "type": emoji_type,
                "uri": name
            }
        }
        res = self.client.post("https://us-central1-alexisbarreyat-bereal.cloudfunctions.net/sendRealMoji",
                               json=json_data, headers={"authorization": f"Bearer {self.token}"})
        return res.content

    def post_instant_realmoji(self, post_id: str, image_file: bytes):
        name = self.upload_realmoji(image_file, "instant")
        json_data = {
            "data": {
                "action": "add",
                "emoji": "⚡",
                "ownerId": self.user_id,
                "photoId": post_id,
                "type": "instant",
                "uri": name
            }
        }
        res = self.client.post("https://us-central1-alexisbarreyat-bereal.cloudfunctions.net/sendRealMoji",
                               json=json_data, headers={"authorization": f"Bearer {self.token}"})
        return res.json()

    # works also for not friends and unpublic post with given post_id
    def get_reactions(self, post_id):
        payload = {
            "postId": post_id,
        }
        res = self.client.get(f"{self.api_url}/content/realmojis",
                              params=payload,
                              headers={"authorization": self.token}
                              )
        return res

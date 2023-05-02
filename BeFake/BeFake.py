import urllib.parse
from base64 import b64decode
import json
from typing import Optional

import httpx
import pendulum
import hashlib
import platform
import os
from .models.realmoji_picture import RealmojiPicture

from .models.post import Post, FOFPost
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
        return '/data/session.json'

    config_dir = _get_config_dir()
    token_filename = f"session.json"
    return os.path.join(config_dir, token_filename)


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
                "user-agent": "BeReal/1.0.1 (AlexisBarreyat.BeReal; build:9513; iOS 16.0.2) 1.0.0/BRApriKit",
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

    def save(self, file_path: Optional[str] = None) -> None:
        session = {"access": {"refresh_token": self.refresh_token,
                              "token": self.token,
                              "expires": self.expiration.timestamp()},
                   "firebase": {"refresh_token": self.firebase_refresh_token,
                                "token": self.firebase_token,
                                "expires": self.firebase_expiration.timestamp()},
                    "user_id": self.user_id}

        if file_path is None:
            file_path = get_default_session_filename()
        dirname = os.path.dirname(file_path)
        if dirname != '' and not os.path.exists(dirname):
            os.makedirs(dirname)
            os.chmod(dirname, 0o700)
        with open(file_path, "w") as f:
            os.chmod(file_path, 0o600)
            f.write(json.dumps(session))

    def load(self, file_path: Optional[str] = None) -> None:
        if file_path is None:
            file_path = get_default_session_filename()
        with open(file_path, "r") as f:
            session = json.load(f)
            self.user_id = session["user_id"]
            self.refresh_token = session["access"]["refresh_token"]
            self.token = session["access"]["token"]
            self.expiration = pendulum.from_timestamp(session["access"]["expires"])
            if pendulum.now() >= self.expiration:
                self.refresh_tokens()
            self.firebase_refresh_token = session["firebase"]["refresh_token"]
            self.firebase_token = session["firebase"]["token"]
            self.firebase_expiration = pendulum.from_timestamp(session["firebase"]["expires"])
            if pendulum.now().add(minutes=3) >= self.firebase_expiration:
                self.firebase_refresh_tokens()

    def legacy_load(self): # DEPRECATED, use this once to convert to new token
        if os.environ.get('IS_DOCKER', False):
            file_path = '/data/token.txt'

        config_dir = _get_config_dir()
        token_filename = f"token.txt"
        file_path = os.path.join(config_dir, token_filename)
        with open(file_path, "r") as f:
            self.firebase_refresh_token = str(f.read()).strip()
            self.firebase_refresh_tokens()
            self.grant_access_token()

    def api_request(self, method: str, endpoint: str, **kwargs) -> dict:
        assert not endpoint.startswith("/")
        res = self.client.request(
            method,
            f"{self.api_url}/{endpoint}",
            headers={"authorization": "Bearer " + self.token},
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
        )
        if not res.is_success:
            raise Exception(res.content)
        res = res.json()
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
            data=payload)
        if not res.is_success:
            raise Exception(res.content)
        res = res.json()
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
        if not vonageRes.is_success:
            raise Exception(vonageRes.content)
        if vonageRes.json()["status"] != '0':
            print("WARNING: " + vonageRes.json()["errorText"])
            print("If you already received a code before, ignore the warning and enter it.")    
        self.otp_session = vonageRes.json()["vonageRequestId"]

    def verify_otp_firebase(self, otp: str) -> None:
        if self.otp_session is None:
            raise Exception("No open otp session (firebase).")

        tokenRes = self.client.post(
            "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPhoneNumber",
            params={"key": self.gapi_key},
            data={
                "sessionInfo": self.otp_session,
                "code": otp,
            },
        )
        if not tokenRes.is_success:
            raise Exception(tokenRes.content)
        tokenRes = tokenRes.json()
        self.firebase_refresh_token = tokenRes["refreshToken"]
        self.phone = tokenRes["phoneNumber"]
        self.firebase_refresh_tokens()
        self.grant_access_token()


    def verify_otp_vonage(self, otp: str) -> None:
        if self.otp_session is None:
            raise Exception("No open otp session (vonage).")
        vonageRes = self.client.post("https://auth.bereal.team/api/vonage/check-code", data={
            "code": otp,
            "vonageRequestId": self.otp_session
        })
        if not vonageRes.is_success:
            print("Error: " + str(vonageRes.json()["statusCode"]) + vonageRes.json()["message"])
            print("Make sure you entered the right code")
        vonageRes = vonageRes.json()
        idTokenRes = self.client.post("https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyCustomToken",
                                      params={"key": self.gapi_key}, data={
                "token": vonageRes["token"],
                "returnSecureToken": True
            })
        if not idTokenRes.is_success:
            raise Exception(idTokenRes.content)

        idTokenRes = idTokenRes.json()

        self.firebase_refresh_token = idTokenRes["refreshToken"]
        self.firebase_refresh_tokens()
        self.grant_access_token()

    def refresh_tokens(self) -> None:
        if self.refresh_token is None:
            raise Exception("No refresh token.")

        res = self.client.post(
            "https://auth.bereal.team/token",
            params={"grant_type": "refresh_token"},
            data={"grant_type": "refresh_token",
                  "client_id": "ios",
                  "client_secret": "962D357B-B134-4AB6-8F53-BEA2B7255420",
                  "refresh_token": self.refresh_token
                  })
        if not res.is_success:
            raise Exception(res.content)

        res = res.json()
        self.token = res["access_token"]
        self.token_info = json.loads(b64decode(res["access_token"].split(".")[1] + '=='))
        self.refresh_token = res["refresh_token"]
        self.expiration = pendulum.now().add(seconds=int(res["expires_in"]))
        self.save()

    def grant_access_token(self) -> None:
        res = self.client.post("https://auth.bereal.team/token", params={"grant_type": "firebase"}, data={
            "grant_type": "firebase",
            "client_id": "ios",
            "client_secret": "962D357B-B134-4AB6-8F53-BEA2B7255420",
            "token": self.firebase_token
        })
        if not res.is_success:
            raise Exception(res.content)

        res = res.json()

        self.token = res["access_token"]
        self.token_info = json.loads(b64decode(res["access_token"].split(".")[1] + '=='))
        self.refresh_token = res["refresh_token"]
        self.expiration = pendulum.now().add(seconds=int(res["expires_in"]))

    def firebase_refresh_tokens(self) -> None:
        res = self.client.post("https://securetoken.googleapis.com/v1/token", params={"key": self.gapi_key},
                                    data={"grantType": "refresh_token",
                                          "refreshToken": self.firebase_refresh_token
                                          })
        if not res.is_success:
            raise Exception(res.content)
        res = res.json()
        self.firebase_refresh_token = res["refresh_token"]
        self.firebase_token = res["id_token"]
        self.firebase_expiration = pendulum.now().add(seconds=int(res["expires_in"]))
        self.user_id = res["user_id"]

    def get_account_info(self):
        res = self.client.post("https://www.googleapis.com/identitytoolkit/v3/relyingparty/getAccountInfo",
                               params={"key": self.gapi_key}, data={"idToken": self.firebase_token})
        if not res.is_success:
            raise Exception(res.content)

        self.user_id = res["users"][0]["localId"]

    def get_user_info(self):
        res = self.api_request("get", "person/me")
        return User(res, self)

    def get_user_profile(self, user_id):
        # here for example we have a firebase-instance-id-token header with the value from the next line, that we can just ignore (but maybe we need it later, there seem to be some changes to the API especially endpoints moving tho the cloudfunctions.net server)
        # cTn8odwxQo6DR0WFVnM9TJ:APA91bGV86nmQUkqnLfFv18IhpOak1x02sYMmKvpUAqhdfkT9Ofg29BXKXS2mbt9oE-LoHiiKViXw75xKFLeOxhb68wwvPCJF79z7V5GbCsIQi7XH1RSD8ItcznqM_qldSDjghf5N8Uo
        res = self.api_request("get", f"person/profiles/{user_id}")
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

    def get_friend_suggestions(self, next=None):
        if next:
            res = self.api_request("get", f"relationships/suggestions", params={"page": next})
        else:
            res = self.api_request("get", f"relationships/suggestions")

        return [User(suggestion, self) for suggestion in res["data"]], res["next"]

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

    def send_capture_in_progress_push(self, topic=None, username=None):  # Outdated?
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
            "laughing": "😂",
            "heartEyes": "😍"
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

        res = self.api_request("put", "person/me/realmojis", data=data)
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
    def get_reactions(self, post_id: str):
        payload = {
            "postId": post_id,
        }
        res = self.api_request("get", f"content/realmojis",
                               params=payload,
                               )
        return res

    def search_username(self, username: str):
        res = self.api_request("get", f"search/profile", params={"query": username})
        return [User(user, self) for user in res["data"]]

    def get_settings(self):
        res = self.api_request("get", f"settings")
        return res

    def get_terms(self):
        res = self.api_request("get", f"terms")
        return res

    def set_terms(self, code: str, choice: bool):
        if choice:
            res = self.api_request("put", f"terms/{code}", data={"status": "ACCEPTED"})
        else:
            res = self.api_request("put", f"terms/{code}", data={"status": "DECLINED"})
        return res

    def set_profile_picture(self, picture: bytes):
        payload = {'upload-file': ('profile-picture.webp', picture, 'image/webp')}
        res = self.api_request("put", f"person/me/profile-picture", files=payload)
        return res

    def remove_profile_picture(self):
        res = self.api_request("delete", f"person/me/profile-picture")
        return res

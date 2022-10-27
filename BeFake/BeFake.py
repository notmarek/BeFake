from base64 import b64decode
import json
import httpx
import pendulum
import hashlib
from models.picture import Picture
from models.realmoji_picture import RealmojiPicture

from models.post import Post
from models.memory import Memory
from models.user import User


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
                #"user-agent": "AlexisBarreyat.BeReal/0.24.0 iPhone/16.0.2 hw/iPhone12_8 (GTMSUF/1)",
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

    def create_post(
        self,
        primary: bytes,
        secondary: bytes,
        is_late: bool,
        is_public: bool,
        caption: str,
        location,
        retakes=0,
        taken_at=None,
    ):
        if taken_at is None:
            now = pendulum.now()
            taken_at = f"{now.to_date_string()}T{now.to_time_string()}Z"

        primary_picture = Picture({})
        primary_picture.upload(self, primary)
        secondary_picture = Picture({})
        secondary_picture.upload(self, secondary, True)

        json_data = {
            "isPublic": is_public,
            "isLate": is_late,
            "retakeCounter": retakes,
            "takenAt": taken_at,
            "location": location,
            "caption": caption,
            "backCamera": {
                "bucket": "storage.bere.al",
                "height": primary_picture.height,
                "width": primary_picture.width,
                "path": primary_picture.url.replace("https://storage.bere.al/", ""),
            },
            "frontCamera": {
                "bucket": "storage.bere.al",
                "height": secondary_picture.height,
                "width": secondary_picture.width,
                "path": secondary_picture.url.replace("https://storage.bere.al/", ""),
            },
        }
        res = self.client.post(f"{self.api_url}/content/post", json=json_data, headers={"authorization": self.token})
        return res.content
    
    def upload(self, data: bytes):
        file = Picture({})
        file.upload(self, data)
        print(file.url)
        return file
    
    def take_screenshot(self, post_id):
        payload = {
            "postId": post_id,
        }
        res = self.client.post(f"{self.api_url}/content/screenshots", params=payload, headers={"authorization": self.token})
        return res.content
    
    def add_comment(self, post_id, comment):
        payload = {
            "postId": post_id,
        }
        data = {
            "content": comment,
        }
        res = self.client.post(f"{self.api_url}/content/comments", params=payload, data=data, headers={"authorization": self.token})
        return res.json()

    def upload_realmoji(self, image_file: bytes, type: str):
        picture = RealmojiPicture({})
        name = picture.upload(self, image_file, type)
        return name
    
    def post_realmoji(
        self,
        post_id: str,
        type: str,
        emoji: str,
        name: str
    ):
        json_data = {
            "data": {
                "action": "add",
                "emoji": emoji,
                "ownerId": self.user_id,
                "photoId": post_id,
                "type": type,
                "uri": name
            }
        }
        
        res = self.client.post("https://us-central1-alexisbarreyat-bereal.cloudfunctions.net/sendRealMoji", json=json_data, headers={"authorization": f"Bearer {self.token}"})
        return res.content

    def post_instant_realmoji(self, image_file: bytes, post_id: str):
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
        res = self.client.post("https://us-central1-alexisbarreyat-bereal.cloudfunctions.net/sendRealMoji", json=json_data, headers={"authorization": f"Bearer {self.token}"})
        return res.content
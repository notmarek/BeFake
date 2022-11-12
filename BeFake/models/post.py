# from ..BeFake import BeFake
from .user import User
from .picture import Picture
from .realmoji import RealMoji
from .screenshot_v2 import ScreenshotV2
from .comment import Comment
import pendulum


class Post(object):
    def __init__(self, data_dict, befake) -> None:
        self.bf = befake
        self.id = data_dict.get("id", None)
        self.notification_id = data_dict.get("notificationID", None)
        self.owner_id = data_dict.get("ownerID", None)
        self.username = data_dict.get("userName", None)
        self.user = User(data_dict.get("user", {}), befake)
        self.media_type = data_dict.get("mediaType", None)
        self.region = data_dict.get("region")
        self.bucket = data_dict.get("bucket")
        self.primary_photo = Picture(
            {},
            data_dict.get("photoURL", None),
            data_dict.get("imageWidth", None),
            data_dict.get("imageHeight", None),
        )
        self.secondary_photo = Picture(
            {},
            data_dict.get("secondaryPhotoURL", None),
            data_dict.get("secondaryImageHeight", None),
            data_dict.get("secondaryImageWidth", None),
        )
        self.late_in_seconds = data_dict.get("lateInSeconds", None)
        self.caption = data_dict.get("caption", None)
        self.public = data_dict.get("isPublic", None)
        self.location = data_dict.get("location", None)  # TODO: location object?
        self.retakes = data_dict.get("retakeCounter", None)
        self.creation_date = data_dict.get("creationDate", None)
        if self.creation_date is not None:
            self.creation_date = pendulum.from_timestamp(self.creation_date["_seconds"])
        self.updated_at = data_dict.get("updatedAt", None)
        if self.updated_at is not None:
            self.updated_at = pendulum.from_timestamp(self.updated_at / 1000)
        self.taken_at = data_dict.get("takenAt", None)
        if self.taken_at is not None:
            self.taken_at = pendulum.from_timestamp(self.taken_at["_seconds"])
        self.comment = [Comment(comment, befake) for comment in data_dict.get("comment", None)]
        self.realmojis = [RealMoji(rm, befake) for rm in data_dict.get("realMojis", [])]
        self.screenshots = data_dict.get("screenshots", None)  # list containing ids of users that screenshotted
        self.screenshots_v2 = [ScreenshotV2(s, befake) for s in data_dict.get("screenshotsV2", None)]
        self.data_dict = data_dict

    def __repr__(self) -> str:
        return f"<Post {self.id}>"

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

        self.primary_photo = Picture(res["primary"])
        self.secondary_photo = Picture(res["secondary"])
        self.id = res.get("id", None)
        self.late_in_seconds = res.get("lateInSeconds", None)
        self.caption = res.get("caption", None)
        self.creation_date = res.get("createdAt", None)
        if self.creation_date is not None:
            self.creation_date = pendulum.parse(self.creation_date)
        self.taken_at = res.get("takenAt", None)
        if self.taken_at is not None:
            self.taken_at = pendulum.parse(self.taken_at)
        self.location = res.get("location", None)
        self.user = User(res.get("user", {}), self.bf)

        return res.content

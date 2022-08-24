#from ..BeFake import BeFake
from .user import User
from .picture import Picture
from .realmoji import RealMoji
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
        self.comment = data_dict.get("comment", None)  # TODO: figure out what this is
        self.realmojis = [RealMoji(rm, befake) for rm in data_dict.get("realMojis", [])]
        self.screenshots = data_dict.get(
            "screenshots", None
        )  # TODO: figure out what this does
        self.screenshots_v2 = data_dict.get(
            "screenshotsV2", None
        )  # TODO: figure out what this does

    def __repr__(self) -> str:
        return f"<Post {self.id}>"

    def create(
        self,
        primary: bytes,
        secondary: bytes,
        caption="",
        retakes=0,
        taken_at=None,
        location={"latitude": "37.2297175", "longitude": "-115.7911082"},
        is_public=False,
        is_late=False,
    ):
        res = self.bf.create_post(
            primary, secondary, is_late, is_public, caption, location, retakes, taken_at
        )
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

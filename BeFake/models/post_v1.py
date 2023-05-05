import pendulum

from .comment import CommentV1
from .picture import Picture
from .post import Location
from .realmoji import RealMojiV1
from .user import User


class PostsV1(object):
    def __init__(self, data_dict, befake) -> None:
        self.bf = befake
        self.user = User(data_dict.get("user", {}), befake)
        self.posts = [PostV1(post, befake) for post in data_dict.get("posts", {})]
        self.region = data_dict.get("region", None)
        self.notification_id = data_dict.get("momentId", None)
        self.data_dict = data_dict


    def __repr__(self):
        return f"<PostsV1 {self.notification_id}>"


class PostV1(object):
    def __init__(self, data_dict, befake) -> None:
        self.bf = befake
        self.id = data_dict.get("id", None)
        self.primary_photo = Picture(data_dict.get("primary", {}))
        self.secondary_photo = Picture(data_dict.get("secondary", {}))
        self.caption = data_dict.get("caption", None)
        self.is_late = data_dict.get("isLate", None)
        self.is_main = data_dict.get("isMain", None)
        self.late_in_seconds = data_dict.get("lateInSeconds", None)
        self.comment = [CommentV1(comment, befake) for comment in data_dict.get("comments", [])]
        self.screenshots = data_dict.get("screenshots", None)
        self.realmojis = [RealMojiV1(rm, befake) for rm in data_dict.get("realMojis", [])]
        self.location = data_dict.get("location", None)
        if self.location is not None:
            self.location = Location(self.location["latitude"], self.location["longitude"])
        self.retakes = data_dict.get("retakeCounter", None)
        self.creation_date = data_dict.get("creationDate", None)
        if self.creation_date is not None:
            self.creation_date = pendulum.parse(self.creation_date)
        self.updated_at = data_dict.get("updatedAt", None)
        if self.updated_at is not None:
            self.updated_at = pendulum.parse(self.updated_at)
        self.taken_at = data_dict.get("takenAt", None)
        if self.taken_at is not None:
            self.taken_at = pendulum.parse(self.taken_at)
        self.data_dict = data_dict

    def __repr__(self):
        return f"<PostV1 {self.id}>"

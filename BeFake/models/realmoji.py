from .picture import Picture
from .user import User
import pendulum


class RealMoji(object):
    def __init__(self, data_dict, befake) -> None:
        self.bf = befake
        self.id = data_dict.get("id", None)
        self.uid = data_dict.get("uid", None)
        self.username = data_dict.get("userName", None)
        self.user = User(data_dict.get("user", {}), befake)
        self.emoji = data_dict.get("emoji", None)
        self.type = data_dict.get("type", None)
        self.photo = Picture({}, data_dict.get("uri"), None, None)

        # date when the realmoji was added to the post
        self.date = data_dict.get("date", None)
        if self.date is not None:
            self.date = pendulum.from_timestamp(self.date["_seconds"])

        # date when the realmoji was created
        if self.type == 'instant':
            self.creation_date = self.date

    def __repr__(self) -> str:
        return f"<RealMoji {self.id}>"

    def get_creation_date(self):
        if not hasattr(self, 'creation_date'):
            self.creation_date = self.photo.get_date()
        return self.creation_date


class RealMojiV1(RealMoji):
    def __init__(self, data_dict, befake):
        self.bf = befake
        self.id = data_dict.get("id", None)
        self.user = User(data_dict.get("user", {}), befake)
        self.uid = self.user.id
        self.username = self.user.username
        self.emoji = data_dict.get("emoji", None)
        self.type = data_dict.get("type", None)
        self.photo = Picture(data_dict.get("media"))
        self.date = pendulum.parse(data_dict.get("postedAt", None))

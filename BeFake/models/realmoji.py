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
        self.date = data_dict.get("date", None)
        if self.date is not None:
            self.date = pendulum.from_timestamp(self.date["_seconds"])

    def __repr__(self) -> str:
        return f"<RealMoji {self.id}>"

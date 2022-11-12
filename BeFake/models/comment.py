import pendulum

from .user import User

class Comment(object):
    def __init__(self, data_dict, befake) -> None:
        self.bf = befake
        self.creation_date = self.creation_date_to_pendulum(data_dict.get("creationDate", None))
        self.id = data_dict.get("id", None)
        self.text = data_dict.get("text", None)
        self.user = User(data_dict.get("user", None), befake)
        self.uid = data_dict.get("uid", None)  # user id, redundant to what's stored in self.user
        self.user_name = data_dict.get("userName", None)  # username, redundant to what's stored in self.user

    def __repr__(self) -> str:
        return f"<Comment {self.id}>"

    @staticmethod
    def creation_date_to_pendulum(data_dict):
        nanoseconds = data_dict.get("_nanoseconds", None)
        seconds = data_dict.get("_seconds", None)
        nanoseconds = int(nanoseconds)
        seconds = int(seconds)
        timestamp = seconds + nanoseconds * 0.000000001
        return pendulum.from_timestamp(timestamp)

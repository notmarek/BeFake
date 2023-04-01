from .user import User
import pendulum


class ScreenshotV2(object):
    def __init__(self, data_dict, befake) -> None:
        self.bf = befake
        self.id = data_dict.get("id", None)
        self.snapped_at = pendulum.parse(data_dict.get("snappedAt", None))  # string in format YYYY-MM-DDTHH:mm:ss.sssZ
        self.user = User(data_dict.get("user", None), befake)

    def __repr__(self) -> str:
        return f"<Screenshot_v2 {self.id}>"

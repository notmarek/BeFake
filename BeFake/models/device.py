from zoneinfo import ZoneInfo


class Device:
    def __init__(self, data_dict: dict, clientVersion=None, device=None,
                 deviceId=None, platform=None, language=None, timezone=None):
        self.clientVersion = data_dict["clientVersion"]
        self.device = data_dict["device"]
        self.deviceId = data_dict["deviceId"]
        self.platform = data_dict["platform"]
        self.language = data_dict["language"]
        self.timezone = ZoneInfo(data_dict["timezone"])
        print(self.timezone)
        if data_dict is None:
            self.clientVersion = clientVersion
            self.device = device
            self.deviceId = deviceId
            self.platform = platform
            self.language = language
            self.timezone = ZoneInfo(timezone)

    def __repr__(self) -> str:
        return f"<Device {self.deviceId}>"

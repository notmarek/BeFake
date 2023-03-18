class Device:
    def __init__(self, clientVersion, device, deviceId, platform, language, timezone):
        self.clientVersion = clientVersion
        self.device = device
        self.deviceId = deviceId
        self.platform = platform
        self.language = language
        self.timezone = timezone

    def __repr__(self) -> str:
        return f"<Device {self.deviceId}>"
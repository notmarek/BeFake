from .picture import Picture


class Track(object):
    def __init__(self, data_dict):
        self.isrc = data_dict.get("isrc", None)
        self.track = data_dict.get("track", None)
        self.artist = data_dict.get("artist", None)
        self.artwork = Picture({}, data_dict.get("url", None), None, None)
        self.provider = data_dict.get("provider", None)
        self.visibility = data_dict.get("visibility", None)
        self.provider_id = data_dict.get("providerId", None)
        self.open_url = data_dict.get("openUrl", None)
        self.type = data_dict.get("audioType", None)

    def __repr__(self):
        return f"<Track {self.track} {self.artist}>"

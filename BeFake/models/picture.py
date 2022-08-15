import httpx


class Picture(object):
    def __init__(self, data_dict, url=None, width=None, height=None) -> None:
        self.url = data_dict.get("url", url)
        self.width = data_dict.get("width", width)
        self.height = data_dict.get("height", height)

    def __repr__(self) -> str:
        return f"<Image {self.url} {self.width}x{self.height}>"

    def download(self):
        return httpx.get(self.url).content

import datetime
import os.path
from typing import Optional

import httpx
import pendulum
import io
from PIL import Image


class Picture(object):
    def __init__(self, data_dict, url=None, width=None, height=None) -> None:
        self.url = data_dict.get("url", url)
        if self.exists():
            self.ext = self.url.split('.')[-1]
        self.width = data_dict.get("width", width)
        self.height = data_dict.get("height", height)
        self.date = None
        self.data = None

    def __repr__(self) -> str:
        return f"<Image {self.url} {self.width}x{self.height}>"

    def exists(self):
        return self.url is not None

    def download(self, path: Optional[str], ext=None):
        if ext:
            # with jpg/jpeg, the file extension is conventionally jpg, but the PIL format name is jpeg
            if ext in ['jpg', 'jpeg']:
                file_ext = 'jpg'
                ext_type = 'jpeg'
            else:
                file_ext = ext
                ext_type = ext
        else:
            file_ext = self.ext
            ext_type = self.ext

        # don't re-download already saved pictures
        if path and os.path.exists(f"{path}.{file_ext}"):
            return

        r = httpx.get(self.url, headers={
            "user-agent": "BeReal/1.0.1 (AlexisBarreyat.BeReal; build:9513; iOS 16.0.2) 1.0.0/BRApriKit",
            "x-ios-bundle-identifier": "AlexisBarreyat.BeReal"})

        self.data = r.content

        if path:
            if ext:
                # borrowed from https://stackoverflow.com/questions/32908639/open-pil-image-from-byte-file
                img = Image.open(io.BytesIO(r.content))
                img = img.convert('RGB')
                img.save(f"{path}.{file_ext}", ext_type)
                self.ext = file_ext
            else:
                with open(f"{path}.{self.ext}", "wb") as f:
                    f.write(self.data)

        return r.content

    def get_date(self):
        if self.date:
            return self.date
        r = httpx.head(self.url)

        # https://stackoverflow.com/a/71637523
        if r.status_code != 200:
            raise Exception(f"Error requesting image: {r.status_code}")

        url_time = r.headers.get('Last-Modified')
        last_updated_pattern = "%a, %d %b %Y %H:%M:%S %Z"
        timestamp = int(datetime.datetime.strptime(url_time, last_updated_pattern).timestamp())
        self.date = pendulum.from_timestamp(timestamp)
        return self.date

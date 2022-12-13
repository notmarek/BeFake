import datetime
import json
import os.path
from typing import Optional

import httpx
import uuid
import pendulum
import io
from PIL import Image
from urllib.parse import quote_plus


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

        r = httpx.get(self.url)
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

    def upload(
        self, befake, img_file: bytes, secondary: bool = False, name: str = None
    ):
        img = Image.open(io.BytesIO(img_file))
        mime_type = Image.MIME[img.format]
        if mime_type != "image/jpeg":
            if not img.mode == "RGB":
                img = img.convert("RGB")
        img_data = io.BytesIO()
        img.save(img_data, format="JPEG", quality=90)
        img_data = img_data.getvalue()
        if name is None:
            name = f"Photos/{befake.user_id}/bereal/{uuid.uuid4()}-{int(pendulum.now().timestamp())}{'-secondary' if secondary else ''}.webp"
        json_data = {
            "cacheControl": "public,max-age=172800",
            "contentType": "image/webp",
            "metadata": {"type": "bereal"},
            "name": name,
        }
        headers = {
            "x-goog-upload-protocol": "resumable",
            "x-goog-upload-command": "start",
            "x-firebase-storage-version": "ios/9.4.0",
            "x-goog-upload-content-type": "image/webp",
            "Authorization": f"Firebase {befake.token}",
            "x-goog-upload-content-length": str(len(img_data)),
            "content-type": "application/json",
            "x-firebase-gmpid": "1:405768487586:ios:28c4df089ca92b89",
        }
        params = {
            "uploadType": "resumable",
            "name": name,
        }
        uri = f"https://firebasestorage.googleapis.com/v0/b/storage.bere.al/o/{quote_plus(name)}"
        # initate the upload
        init_res = befake.client.post(
            uri, headers=headers, params=params, data=json.dumps(json_data)
        )
        if init_res.status_code != 200:
            raise Exception(f"Error initiating upload: {init_res.status_code}")
        upload_url = init_res.headers["x-goog-upload-url"]
        headers = {
            "x-goog-upload-command": "upload, finalize",
            "x-goog-upload-protocol": "resumable",
            "x-goog-upload-offset": "0",
            "content-type": "image/jpeg",
        }
        # upload the image
        upload_res = befake.client.put(upload_url, headers=headers, content=img_data)
        if upload_res.status_code != 200:
            raise Exception(f"Error uploading image: {upload_res.status_code}")
        res_data = upload_res.json()
        # populate self
        self.url = f'https://{res_data["bucket"]}/{res_data["name"]}'
        self.width = 1500
        self.height = 2000

        # Photos/2lzXSG00xMNWR4cKFuGAzdUbOXM2/bereal/3a0fa270-bd7b-4dfd-8af0-d5a23a291999-1660586403.jpg
        # https://storage.bere.al/Photos/2lzXSG00xMNWR4cKFuGAzdUbOXM2/bereal/3a0fa270-bd7b-4dfd-8af0-d5a23a291999-1660586403.jpg
        # Photos%2F2lzXSG00xMNWR4cKFuGAzdUbOXM2%2Fbereal%2F3a0fa270-bd7b-4dfd-8af0-d5a23a291999-1660586403.jpg
        # https://firebasestorage.googleapis.com/v0/b/storage.bere.al/o/Photos%2F2lzXSG00xMNWR4cKFuGAzdUbOXM2%2Fbereal%2F3a0fa270-bd7b-4dfd-8af0-d5a23a291999-1660586403.jpg?uploadType=resumable&name=Photos%2F2lzXSG00xMNWR4cKFuGAzdUbOXM2%2Fbereal%2F3a0fa270-bd7b-4dfd-8af0-d5a23a291999-1660586403.jpg

    def get_date(self):
        if self.date:
            return self.date
        r = httpx.head(self.url)

        # https://stackoverflow.com/a/71637523
        url_time = r.headers.get('Last-Modified')
        last_updated_pattern = "%a, %d %b %Y %H:%M:%S %Z"
        timestamp = int(datetime.datetime.strptime(url_time, last_updated_pattern).timestamp())
        self.date = pendulum.from_timestamp(timestamp)
        return self.date

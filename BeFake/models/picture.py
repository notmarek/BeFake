import json
import httpx
import uuid
import pendulum
import io
from PIL import Image
from urllib.parse import quote_plus


class Picture(object):
    def __init__(self, data_dict, url=None, width=None, height=None) -> None:
        self.url = data_dict.get("url", url)
        self.width = data_dict.get("width", width)
        self.height = data_dict.get("height", height)

    def __repr__(self) -> str:
        return f"<Image {self.url} {self.width}x{self.height}>"

    def download(self):
        return httpx.get(self.url).content

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
            name = f"Photos/{befake.user_id}/{uuid.uuid4}-{int(pendulum.now().timestamp())}{'-secondary' if secondary else ''}.jpg"

        json_data = {
            "cacheControl": "public,max-age=172800",
            "contentType": "image/jpeg",
            "metadata": {"type": "bereal"},
            "name": name,
        }
        headers = {
            "x-goog-upload-protocol": "resumable",
            "x-goog-upload-command": "start",
            "x-firebase-storage-version": "ios/9.3.0",
            "x-goog-upload-content-type": "image/jpeg",
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
        # Photos%2F2lzXSG00xMNWR4cKFuGAzdUbOXM2%2Fbereal%2F3a0fa270-bd7b-4dfd-8af0-d5a23a291999-1660586403.jpg
        # https://firebasestorage.googleapis.com/v0/b/storage.bere.al/o/Photos%2F2lzXSG00xMNWR4cKFuGAzdUbOXM2%2Fbereal%2F3a0fa270-bd7b-4dfd-8af0-d5a23a291999-1660586403.jpg?uploadType=resumable&name=Photos%2F2lzXSG00xMNWR4cKFuGAzdUbOXM2%2Fbereal%2F3a0fa270-bd7b-4dfd-8af0-d5a23a291999-1660586403.jpg

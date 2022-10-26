import json
import httpx
import uuid
import pendulum
import io
from PIL import Image
from urllib import parse


class RealmojiPicture(object):
    def __init__(self, data_dict, url=None, width=None, height=None) -> None:
        self.url = data_dict.get("url", url)
        self.width = data_dict.get("width", width)
        self.height = data_dict.get("height", height)

    def __repr__(self) -> str:
        return f"<RealmojiImage {self.url} {self.width}x{self.height}>"

    def exists(self):
        return self.url is not None
    
    def download(self):
        r = httpx.get(self.url)
        self.data = r.content
        return r.content

    def upload(
        self, befake, img_file: bytes, type: str, name: str = None
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
            name = f"Photos/{befake.user_id}/realmoji/{uuid.uuid4()}-{type}-{int(pendulum.now().timestamp())}.webp"
        uri = befake.get_realmoji_upload_url()
        print(uri)
        parameters = parse.parse_qs(parse.urlsplit(uri).query)
        json_data = {
            "cacheControl": "public,max-age=2592000",
            "contentType": "image/webp",
            "metadata": {"type": "realmoji"},
            "name": name,
        }
        headers = {
            "cache-control": "public,max-age=2592000",
            "content-type": "application/json",
            "x-goog-content-length-range": "0,25000",
            "x-goog-signature": parameters["X-Goog-Signature"][0], # With these lines 400 (malformed) without 403 (forbidden -> unsigned-payload error)
            "x-goog-credential": parameters["X-Goog-Credential"][0],

            "x-goog-upload-content-type": "image/webp",
            "x-goog-upload-protocol": "resumable",
            "x-goog-upload-command": "start",
            "x-goog-upload-content-length": str(len(img_data)),
            "x-firebase-storage-version": "ios/9.4.0",
            "Authorization": f"Firebase {befake.token}",
            "x-firebase-gmpid": "1:405768487586:ios:28c4df089ca92b89",
        }
        params = {
            "uploadType": "resumable",
            "name": name,
        }
        #uri = f"https://firebasestorage.googleapis.com/v0/b/storage.bere.al/o/{quote_plus(name)}"
        
        # initate the upload
        init_res = befake.client.post(
            uri, headers=headers, params=params, data=json.dumps(json_data)
        )
        if init_res.status_code != 200:
            print(init_res.content)
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

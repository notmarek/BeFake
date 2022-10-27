import json
import httpx
import uuid
import pendulum
import io
from PIL import Image
import random, string


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

    # TODO: Figure out why non-instant realmojis can't be added after being uploaded ({"error":{"message":"Something went Wrong","status":"INTERNAL"}})
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
            name = f"Photos/{befake.user_id}/realmoji/{uuid.uuid4()}-{''.join(random.choices(string.ascii_letters + string.digits, k=16))}-{type}-{int(pendulum.now().timestamp()) if type != 'instant' else ''}.jpg"
        
        dt = pendulum.now(tz="GMT")
        json_data = {
            "cacheControl": "public,max-age=2592000",
            "contentType": "image/jpeg",
            "metadata": {
                "creationDate": dt.format('ddd MMM D Y HH:mm:ss [GMT+0000]'),
                "type": "instantRealmoji" if type == "instant" else "realmoji",
                "uid": befake.user_id
            }
        }
        headers = {
            "Authorization": f"Firebase {befake.token}",
            "x-firebase-storage-version": "ios/9.4.0",
            "x-firebase-gmpid": "1:405768487586:ios:28c4df089ca92b89",
            "x-goog-upload-command": "start",
            "x-goog-upload-protocol": "resumable",
            "x-goog-upload-content-type": "image/jpeg",
            "content-type": "application/json",
        }
        params = {
            "uploadType": "resumable",
            "name": name,
        }
        uri = "https://firebasestorage.googleapis.com/v0/b/storage.bere.al/o"
        
        # initate the upload
        init_res = befake.client.post(
            uri, headers=headers, params=params, data=json.dumps(json_data)
        )
        if init_res.status_code != 200:
            raise Exception(f"Error initiating upload: {init_res.status_code}")
        
        upload_url = init_res.headers["x-goog-upload-url"]
        headers = {
            "Authorization": f"Firebase {befake.token}",
            "x-firebase-storage-version": "ios/9.4.0",
            "x-firebase-gmpid": "1:405768487586:ios:28c4df089ca92b89",
            "x-goog-upload-command": "upload, finalize",
            "x-goog-upload-protocol": "resumable",
            "x-goog-upload-offset": "0",
            "content-type": "application/x-www-form-urlencoded",
        }
        # upload the image
        upload_res = befake.client.post(upload_url, headers=headers, content=img_data)
        if upload_res.status_code != 200:
            print(upload_res.content)
            raise Exception(f"Error uploading image: {upload_res.status_code}")
        res_data = upload_res.json()
        # populate self
        self.url = f'https://{res_data["bucket"]}/{res_data["name"]}'
        self.width = 500
        self.height = 500
        
        return name
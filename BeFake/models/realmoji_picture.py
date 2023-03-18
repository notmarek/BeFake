import httpx


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
    def upload(self, befake):
        initHeaders = {
            "authorization": f"Bearer {befake.token}"
        }

        # signed url request
        initRes = befake.client.get(
            "https://mobile.bereal.com/api/content/realmojis/upload-url?mimeType=image/webp",
            headers=initHeaders)
        if initRes.status_code != 200:
            raise Exception(f"Error initiating upload: {initRes.status_code}")

        init_data = initRes.json()
        headers = init_data["data"]["headers"]
        headers["Authorization"] = f"Bearer {befake.token}"
        url = init_data["data"]["url"]

        # Upload request
        upload_res = befake.client.put(url, headers=headers, data=self.imageData)
        if upload_res.status_code != 200:
            raise Exception(f"Error uploading primary image: {upload_res.status_code}")

        # populate self
        self.width = 500
        self.height = 500
        self.url = url
        # return path
        return init_data["data"]["path"]
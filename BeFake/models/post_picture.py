import io
from PIL import Image


class PostUpload:
    """
    BeReal post upload endpoint
    """
    def __init__(self, primary: bytes, secondary: bytes):
        self.primary = Image.open(io.BytesIO(primary))
        self.secondary = Image.open(io.BytesIO(secondary))
        mime_type1 = Image.MIME[self.primary.format]
        mime_type2 = Image.MIME[self.secondary.format]
        if mime_type1 != "image/webp":
            if not self.primary.mode == "RGB":
                self.primary = self.primary.convert("RGB")

        if mime_type2 != "image/webp":
            if not self.secondary.mode == "RGB":
                self.secondary = self.secondary.convert("RGB")

        self.primaryData = io.BytesIO()
        self.primary.save(self.primaryData, format="WEBP")
        self.primaryData = self.primaryData.getvalue()

        self.secondaryData = io.BytesIO()
        self.secondary.save(self.secondaryData, format="WEBP")
        self.secondaryData = self.secondaryData.getvalue()

        self.primaryPath = None
        self.secondaryPath = None


    def upload(self, befake):
        # Upload initialization:
        initRes = befake.api_request("get",f"content/posts/upload-url", params={"mimeType": "image/webp"})
        if initRes.status_code != 200:
            raise Exception(f"Error initiating upload: {initRes.status_code}")

        init_data = initRes.json()
        headers1 = init_data["data"][0]["headers"]
        headers1["Authorization"] = f"Bearer {befake.token}"
        headers2 = init_data["data"][1]["headers"]
        headers2["Authorization"] = f"Bearer {befake.token}"

        url1 = init_data["data"][0]["url"]
        url2 = init_data["data"][1]["url"]

        primary_res = befake.client.put(url1, headers=headers1, data=self.primaryData)

        if primary_res.status_code != 200:
            raise Exception(f"Error uploading primary image: {primary_res.status_code}")

        secondary_res = befake.client.put(url2, headers=headers2, data=self.secondaryData)
        if secondary_res.status_code != 200:
            raise Exception(f"Error uploading secondary image: {secondary_res.status_code}")


        # populate self
        self.primaryPath = init_data["data"][0]["path"]
        self.secondaryPath = init_data["data"][1]["path"]

        self.primarySize = (1500, 2000) # (width, height)
        self.secondarySize = (1500, 2000) # (width, height)
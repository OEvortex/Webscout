import os
import tempfile
import time
import uuid
from io import BytesIO
from typing import Union, cast, Optional

import requests

from webscout.litagent import LitAgent
from webscout.AIbase import SimpleModelList
from webscout.Provider.TTI.base import BaseImages, TTICompatibleProvider
from webscout.Provider.TTI.utils import ImageData, ImageResponse

try:
    from PIL import Image
except ImportError:
    Image = None


class Images(BaseImages):
    def __init__(self, client):
        self._client = client

    def create(
        self,
        model: str = "magicstudio",
        prompt: Optional[str] = None,
        n: int = 1,
        size: Optional[str] = None,
        response_format: str = "url",
        user: Optional[str] = None,
        style: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        timeout: int = 60,
        image_format: str = "jpg",
        **kwargs,
    ) -> ImageResponse:
        if not prompt:
            raise ValueError("Prompt is required!")
        agent = LitAgent()
        images = []
        urls = []
        api_url = "https://ai-api.magicstudio.com/api/ai-art-generator"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": agent.random(),
            "Origin": "https://magicstudio.com",
            "Referer": "https://magicstudio.com/ai-art-generator/",
            "DNT": "1",
            "Sec-GPC": "1",
        }
        session = requests.Session()
        session.headers.update(headers)
        for _ in range(n):
            form_data = {
                "prompt": prompt,
                "output_format": "bytes",
                "user_profile_id": "null",
                "anonymous_user_id": str(uuid.uuid4()),
                "request_timestamp": time.time(),
                "user_is_subscribed": "false",
                "client_id": uuid.uuid4().hex,
            }
            resp = session.post(
                api_url,
                data=form_data,
                timeout=timeout,
            )
            resp.raise_for_status()
            img_bytes = resp.content
            # Convert to png or jpeg in memory if needed
            if Image is not None:
                with BytesIO(img_bytes) as input_io:
                    with Image.open(input_io) as im:
                        out_io = BytesIO()
                        if (
                            image_format.lower() == "jpeg"
                            or image_format.lower() == "jpg"
                        ):
                            im = im.convert("RGB")
                            im.save(out_io, format="JPEG")
                        else:
                            im.save(out_io, format="PNG")
                        img_bytes = out_io.getvalue()
            images.append(img_bytes)
            if response_format == "url":

                def upload_file_with_retry(img_bytes, image_format, max_retries=3):
                    ext = "jpg" if image_format.lower() in ("jpeg", "jpg") else "png"
                    for attempt in range(max_retries):
                        tmp_path = None
                        try:
                            with tempfile.NamedTemporaryFile(
                                suffix=f".{ext}", delete=False
                            ) as tmp:
                                tmp.write(img_bytes)
                                tmp.flush()
                                tmp_path = tmp.name
                            with open(tmp_path, "rb") as f:
                                files = {
                                    "fileToUpload": (f"image.{ext}", f, f"image/{ext}")
                                }
                                data = {"reqtype": "fileupload", "json": "true"}
                                headers = {"User-Agent": agent.random()}
                                if attempt > 0:
                                    headers["Connection"] = "close"
                                resp = requests.post(
                                    "https://catbox.moe/user/api.php",
                                    files=files,
                                    data=data,
                                    headers=headers,
                                    timeout=timeout,
                                )
                                if resp.status_code == 200 and resp.text.strip():
                                    text = resp.text.strip()
                                    if text.startswith("http"):
                                        return text
                                    try:
                                        result = resp.json()
                                        if "url" in result:
                                            return result["url"]
                                    except Exception:
                                        if "http" in text:
                                            return text
                        except Exception:
                            if attempt < max_retries - 1:
                                time.sleep(1 * (attempt + 1))
                        finally:
                            if tmp_path and os.path.isfile(tmp_path):
                                try:
                                    os.remove(tmp_path)
                                except Exception:
                                    pass
                    return None

                def upload_file_alternative(img_bytes, image_format):
                    try:
                        ext = (
                            "jpg" if image_format.lower() in ("jpeg", "jpg") else "png"
                        )
                        with tempfile.NamedTemporaryFile(
                            suffix=f".{ext}", delete=False
                        ) as tmp:
                            tmp.write(img_bytes)
                            tmp.flush()
                            tmp_path = tmp.name
                        try:
                            if not os.path.isfile(tmp_path):
                                return None
                            with open(tmp_path, "rb") as img_file:
                                files = {"file": img_file}
                                alt_resp = requests.post("https://0x0.st", files=files)
                                alt_resp.raise_for_status()
                                image_url = alt_resp.text.strip()
                                if not image_url.startswith("http"):
                                    return None
                                return image_url
                        except Exception:
                            return None
                        finally:
                            try:
                                os.remove(tmp_path)
                            except Exception:
                                pass
                    except Exception:
                        return None

                uploaded_url = upload_file_with_retry(img_bytes, image_format)
                if not uploaded_url:
                    uploaded_url = upload_file_alternative(img_bytes, image_format)
                if uploaded_url:
                    urls.append(uploaded_url)
                else:
                    raise RuntimeError(
                        "Failed to upload image to catbox.moe using all available methods"
                    )
        result_data = []
        if response_format == "url":
            for url in urls:
                result_data.append(ImageData(url=url))
        elif response_format == "b64_json":
            import base64

            for img in images:
                b64 = base64.b64encode(img).decode("utf-8")
                result_data.append(ImageData(b64_json=b64))
        else:
            raise ValueError("response_format must be 'url' or 'b64_json'")
        from time import time as _time

        return ImageResponse(created=int(_time()), data=result_data)


class MagicStudioAI(TTICompatibleProvider):
    """MagicStudio AI TTI Provider - Generates images through MagicStudio's public endpoint."""

    # Provider status
    required_auth: bool = False  # No authentication required
    working: bool = True  # Currently working

    AVAILABLE_MODELS = ["magicstudio"]

    def __init__(self):
        self.api_endpoint = "https://ai-api.magicstudio.com/api/ai-art-generator"
        self.session = requests.Session()
        self.user_agent = LitAgent().random()
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://magicstudio.com",
            "referer": "https://magicstudio.com/ai-art-generator/",
            "user-agent": self.user_agent,
        }
        self.session.headers.update(self.headers)
        self.images = Images(self)

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    from rich import print

    client = MagicStudioAI()
    response = client.images.create(
        prompt="A cool cyberpunk city at night",
        response_format="url",
        n=2,
        timeout=30,
    )
    print(response)

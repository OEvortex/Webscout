import json
import os
import random
import tempfile
import time
from io import BytesIO
from typing import Union, cast, Optional

import requests
from requests.exceptions import RequestException

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
        *,
        model: str,
        prompt: str,
        n: int = 1,
        size: str = "1024x1024",
        response_format: str = "url",
        user: Optional[str] = None,
        style: str = "none",
        aspect_ratio: str = "1:1",
        timeout: int = 60,
        image_format: str = "png",
        seed: Optional[int] = None,
        **kwargs,
    ) -> ImageResponse:
        """
        image_format: "png" or "jpeg"
        seed: Optional random seed for reproducibility. If not provided, a random seed is used.
        """
        if Image is None:
            raise ImportError("Pillow (PIL) is required for image format conversion.")

        images = []
        urls = []

        def upload_file_with_retry(img_bytes, image_format, max_retries=3):
            ext = "jpg" if image_format.lower() == "jpeg" else "png"
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
                        files = {"fileToUpload": (f"image.{ext}", f, f"image/{ext}")}
                        data = {"reqtype": "fileupload", "json": "true"}
                        headers = {"User-Agent": LitAgent().random()}
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
                            except json.JSONDecodeError:
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
                ext = "jpg" if image_format.lower() == "jpeg" else "png"
                with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
                    tmp.write(img_bytes)
                    tmp.flush()
                    tmp_path = tmp.name
                try:
                    if not os.path.isfile(tmp_path):
                        return None
                    with open(tmp_path, "rb") as img_file:
                        files = {"file": img_file}
                        response = requests.post("https://0x0.st", files=files)
                        response.raise_for_status()
                        image_url = response.text.strip()
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

        for i in range(n):
            # Prepare parameters for Pollinations API
            params = {
                "model": model,
                "width": int(size.split("x")[0]) if "x" in size else 1024,
                "height": int(size.split("x")[1]) if "x" in size else 1024,
                "seed": seed if seed is not None else random.randint(0, 2**32 - 1),
            }
            # Build the API URL
            base_url = f"https://image.pollinations.ai/prompt/{prompt}"
            # Compose query string
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{base_url}?{query}"
            try:
                resp = self._client.session.get(
                    url,
                    timeout=timeout,
                )
                resp.raise_for_status()
                img_bytes = resp.content
            except RequestException as e:
                raise RuntimeError(f"Failed to fetch image from Pollinations API: {e}")

            # Convert to png or jpeg in memory
            with BytesIO(img_bytes) as input_io:
                with Image.open(input_io) as im:
                    out_io = BytesIO()
                    if image_format.lower() == "jpeg":
                        im = im.convert("RGB")
                        im.save(out_io, format="JPEG")
                    else:
                        im.save(out_io, format="PNG")
                    img_bytes = out_io.getvalue()

            images.append(img_bytes)

            if response_format == "url":
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


class PollinationsAI(TTICompatibleProvider):
    """PollinationsAI TTI Provider - Allows setting a custom seed for reproducible results."""

    # Provider status
    required_auth: bool = False  # No authentication required
    working: bool = True  # Currently working

    AVAILABLE_MODELS = [
        "flux",
        "flux-pro",
        "flux-realism",
        "flux-anime",
        "flux-3d",
        "any-dark",
        "turbo",
        "gptimage"
    ]

    def __init__(self):
        self.api_endpoint = "https://image.pollinations.ai/prompt"
        self.session = requests.Session()
        self.user_agent = LitAgent().random()
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://image.pollinations.ai",
            "referer": "https://image.pollinations.ai/",
            "user-agent": self.user_agent,
        }
        self.session.headers.update(self.headers)
        self.images = Images(self)

    @property
    def models(self) -> SimpleModelList:
        return SimpleModelList(type(self).AVAILABLE_MODELS)


if __name__ == "__main__":
    from rich import print

    client = PollinationsAI()
    response = client.images.create(
        model="flux",
        prompt="a japanese waifu in short kimono clothes",
        response_format="url",
        n=4,
        timeout=30,
        seed=None,  # You can set a specific seed for reproducibility
    )
    print(response)

import base64
import os
import tempfile
import time
import uuid
from io import BytesIO
from typing import TYPE_CHECKING, Any, Optional

import requests

from webscout.AIbase import SimpleModelList
from webscout.litagent import LitAgent
from webscout.Provider.TTI.base import BaseImages, TTICompatibleProvider
from webscout.Provider.TTI.utils import ImageData, ImageResponse

# Optional Pillow import for image format conversion
Image: Any = None
PILLOW_AVAILABLE = False
try:
    from PIL import Image  # type: ignore

    PILLOW_AVAILABLE = True
except ImportError:
    pass

if TYPE_CHECKING:
    from PIL import Image as PILImage  # type: ignore


def _convert_image_format(img_bytes: bytes, image_format: str) -> bytes:
    """
    Convert image bytes to the specified format using Pillow.

    Args:
        img_bytes: Raw image bytes
        image_format: Target format ("png", "jpg", or "jpeg")

    Returns:
        Converted image bytes

    Raises:
        ImportError: If Pillow is not installed
    """
    if not PILLOW_AVAILABLE or Image is None:
        raise ImportError(
            "Pillow (PIL) is required for image format conversion. "
            "Install it with: pip install pillow"
        )

    with BytesIO(img_bytes) as input_io:
        with Image.open(input_io) as im:
            out_io = BytesIO()
            if image_format.lower() in ("jpeg", "jpg"):
                im = im.convert("RGB")
                im.save(out_io, format="JPEG")
            else:
                im.save(out_io, format="PNG")
            return out_io.getvalue()


class Images(BaseImages):
    def __init__(self, client: "MagicStudioAI"):
        self._client = client

    def create(
        self,
        *,
        model: str = "magicstudio",
        prompt: str,
        n: int = 1,
        size: str = "1024x1024",
        response_format: str = "url",
        user: Optional[str] = None,
        style: str = "none",
        aspect_ratio: str = "1:1",
        timeout: Optional[int] = None,
        image_format: str = "jpg",
        seed: Optional[int] = None,
        convert_format: bool = False,
        **kwargs,
    ) -> ImageResponse:
        """
        Generate images using MagicStudio's AI art generator.

        Args:
            model: Model to use (default: "magicstudio")
            prompt: The image generation prompt (required)
            n: Number of images to generate
            size: Image size (not used by this provider)
            response_format: "url" or "b64_json"
            user: Optional user identifier
            style: Optional style parameter
            aspect_ratio: Optional aspect ratio
            timeout: Request timeout in seconds (default: 60)
            image_format: Output format "png" or "jpg" (used for upload and conversion)
            seed: Optional random seed for reproducibility
            convert_format: If True, convert image to specified format (requires Pillow)
            **kwargs: Additional parameters

        Returns:
            ImageResponse with generated image data

        Raises:
            ValueError: If prompt is not provided or response_format is invalid
            ImportError: If convert_format is True but Pillow is not installed
        """
        if not prompt:
            raise ValueError("Prompt is required!")

        # Use default timeout if not provided
        effective_timeout = timeout if timeout is not None else 60

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
                timeout=effective_timeout,
            )
            resp.raise_for_status()
            img_bytes = resp.content

            # Convert image format if requested (requires Pillow)
            if convert_format:
                img_bytes = _convert_image_format(img_bytes, image_format)

            images.append(img_bytes)
            if response_format == "url":

                def upload_file_with_retry(
                    img_bytes: bytes, image_format: str, max_retries: int = 3
                ) -> Optional[str]:
                    ext = "jpg" if image_format.lower() in ("jpeg", "jpg") else "png"
                    for attempt in range(max_retries):
                        tmp_path = None
                        try:
                            with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
                                tmp.write(img_bytes)
                                tmp.flush()
                                tmp_path = tmp.name
                            with open(tmp_path, "rb") as f:
                                files = {"fileToUpload": (f"image.{ext}", f, f"image/{ext}")}
                                data = {"reqtype": "fileupload", "json": "true"}
                                upload_headers = {"User-Agent": agent.random()}
                                if attempt > 0:
                                    upload_headers["Connection"] = "close"
                                upload_resp = requests.post(
                                    "https://catbox.moe/user/api.php",
                                    files=files,
                                    data=data,
                                    headers=upload_headers,
                                    timeout=effective_timeout,
                                )
                                if upload_resp.status_code == 200 and upload_resp.text.strip():
                                    text = upload_resp.text.strip()
                                    if text.startswith("http"):
                                        return text
                                    try:
                                        result = upload_resp.json()
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

                def upload_file_alternative(img_bytes: bytes, image_format: str) -> Optional[str]:
                    try:
                        ext = "jpg" if image_format.lower() in ("jpeg", "jpg") else "png"
                        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
                            tmp.write(img_bytes)
                            tmp.flush()
                            tmp_path = tmp.name
                        try:
                            if not os.path.isfile(tmp_path):
                                return None
                            with open(tmp_path, "rb") as img_file:
                                files = {"file": img_file}
                                alt_resp = requests.post(
                                    "https://0x0.st", files=files, timeout=effective_timeout
                                )
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
        model="magicstudio",
        prompt="A cool cyberpunk city at night",
        response_format="url",
        n=2,
        timeout=30,
    )
    print(response)

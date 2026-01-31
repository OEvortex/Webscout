import base64
import json
import os
import random
import tempfile
import time
from io import BytesIO
from typing import TYPE_CHECKING, Any, Optional

import requests
from requests.exceptions import RequestException

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


def _convert_image_format(img_bytes: bytes, target_format: str) -> bytes:
    """
    Convert image bytes to the specified format using Pillow.

    Args:
        img_bytes: Raw image bytes
        target_format: Target format ('png' or 'jpeg')

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
            if target_format.lower() == "jpeg":
                im = im.convert("RGB")
                im.save(out_io, format="JPEG")
            else:
                im.save(out_io, format="PNG")
            return out_io.getvalue()


def _detect_image_format(img_bytes: bytes) -> Optional[str]:
    """
    Detect image format from magic bytes.

    Args:
        img_bytes: Raw image bytes

    Returns:
        Format string ('png', 'jpeg', 'gif', 'webp') or None if unknown
    """
    if len(img_bytes) < 12:
        return None

    # PNG: 89 50 4E 47 0D 0A 1A 0A
    if img_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"

    # JPEG: FF D8 FF
    if img_bytes[:3] == b"\xff\xd8\xff":
        return "jpeg"

    # GIF: GIF87a or GIF89a
    if img_bytes[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"

    # WebP: RIFF....WEBP
    if img_bytes[:4] == b"RIFF" and img_bytes[8:12] == b"WEBP":
        return "webp"

    return None


class Images(BaseImages):
    def __init__(self, client: "PollinationsAI"):
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
        timeout: Optional[int] = None,
        image_format: str = "png",
        seed: Optional[int] = None,
        convert_format: bool = False,
        **kwargs,
    ) -> ImageResponse:
        """
        Generate images using Pollinations API.

        Args:
            model: Model to use for generation
            prompt: The image generation prompt
            n: Number of images to generate
            size: Image size (e.g., "1024x1024")
            response_format: "url" or "b64_json"
            user: Optional user identifier
            style: Style parameter
            aspect_ratio: Aspect ratio
            timeout: Request timeout in seconds (default: 60)
            image_format: Output format "png" or "jpeg" (used for upload filename)
            seed: Optional random seed for reproducibility
            convert_format: If True, convert image to specified format (requires Pillow)

        Returns:
            ImageResponse with generated image data
        """
        # Use default timeout if not provided
        effective_timeout = timeout if timeout is not None else 60

        images = []
        urls = []

        def upload_file_with_retry(img_bytes: bytes, image_format: str, max_retries: int = 3):
            ext = "jpg" if image_format.lower() == "jpeg" else image_format.lower()
            if ext not in ("jpg", "png", "gif", "webp"):
                ext = "png"
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
                        headers = {"User-Agent": LitAgent().random()}
                        if attempt > 0:
                            headers["Connection"] = "close"
                        resp = requests.post(
                            "https://catbox.moe/user/api.php",
                            files=files,
                            data=data,
                            headers=headers,
                            timeout=effective_timeout,
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

        def upload_file_alternative(img_bytes: bytes, image_format: str):
            try:
                ext = "jpg" if image_format.lower() == "jpeg" else image_format.lower()
                if ext not in ("jpg", "png", "gif", "webp"):
                    ext = "png"
                with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
                    tmp.write(img_bytes)
                    tmp.flush()
                    tmp_path = tmp.name
                try:
                    if not os.path.isfile(tmp_path):
                        return None
                    with open(tmp_path, "rb") as img_file:
                        files = {"file": img_file}
                        response = requests.post(
                            "https://0x0.st", files=files, timeout=effective_timeout
                        )
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
                    timeout=effective_timeout,
                )
                resp.raise_for_status()
                img_bytes = resp.content
            except RequestException as e:
                raise RuntimeError(f"Failed to fetch image from Pollinations API: {e}")

            # Convert image format if requested
            if convert_format:
                img_bytes = _convert_image_format(img_bytes, image_format)
                actual_format = image_format
            else:
                # Detect actual image format from bytes
                actual_format = _detect_image_format(img_bytes) or image_format

            images.append(img_bytes)

            if response_format == "url":
                uploaded_url = upload_file_with_retry(img_bytes, actual_format)
                if not uploaded_url:
                    uploaded_url = upload_file_alternative(img_bytes, actual_format)
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
        "gptimage",
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
        convert_format=False,  # Set to True to convert format (requires Pillow)
    )
    print(response)

import time
from typing import List, Optional, Union, cast

from pydantic import BaseModel, Field


class ImageData(BaseModel):
    url: Optional[str] = None
    b64_json: Optional[str] = None


class ImageResponse(BaseModel):
    created: int = Field(default_factory=lambda: int(time.time()))
    data: List[ImageData]

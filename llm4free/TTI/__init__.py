# This file marks the directory as a Python package.
# Static imports for all TTI (Text-to-Image) provider modules

# Base classes
from llm4free.TTI.base import (
    BaseImages,
    TTICompatibleProvider,
)

# Provider implementations
from llm4free.TTI.bingimage import BingImageAI
from llm4free.TTI.magichour import MagicHourAI
from llm4free.TTI.magicstudio import MagicStudioAI
from llm4free.TTI.miragic import MiragicAI
from llm4free.TTI.nologintool import NoLoginTool
from llm4free.TTI.onefreeai import OneFreeAI
from llm4free.TTI.perchance import PerchanceAI
from llm4free.TTI.pollinations import PollinationsAI
from llm4free.TTI.raphael import RaphaelAI
from llm4free.TTI.together import TogetherImage
from llm4free.TTI.visualgpt import VisualGPT

# Utility classes
from llm4free.TTI.utils import (
    ImageData,
    ImageResponse,
)

# List of all exported names
__all__ = [
    # Base classes
    "TTICompatibleProvider",
    "BaseImages",
    # Utilities
    "ImageData",
    "ImageResponse",
    # Providers
    "BingImageAI",
    "MagicHourAI",
    "MagicStudioAI",
    "NoLoginTool",
    "OneFreeAI",
    "PollinationsAI",
    "RaphaelAI",
    "TogetherImage",
    "MiragicAI",
    "PerchanceAI",
    "VisualGPT",
]

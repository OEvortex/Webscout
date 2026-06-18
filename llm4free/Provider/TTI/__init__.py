# This file marks the directory as a Python package.
# Static imports for all TTI (Text-to-Image) provider modules

# Base classes
from llm4free.Provider.TTI.base import (
    BaseImages,
    TTICompatibleProvider,
)

# Provider implementations
from llm4free.Provider.TTI.bingimage import BingImageAI
from llm4free.Provider.TTI.magichour import MagicHourAI
from llm4free.Provider.TTI.magicstudio import MagicStudioAI
from llm4free.Provider.TTI.miragic import MiragicAI
from llm4free.Provider.TTI.pollinations import PollinationsAI
from llm4free.Provider.TTI.together import TogetherImage
from llm4free.Provider.TTI.visualgpt import VisualGPT

# Utility classes
from llm4free.Provider.TTI.utils import (
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
    "PollinationsAI",
    "TogetherImage",
    "MiragicAI",
    "VisualGPT",
]

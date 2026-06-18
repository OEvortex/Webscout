# llm4free/__init__.py

from .AIauto import *  # noqa: F403
from .AIutel import *  # noqa: F403
from .client import Client
from .Extra import *  # noqa: F403
from llm4free.litagent import LitAgent
from .models import model
from .optimizers import *
from .Provider import *
from .AISEARCH import *
from .STT import *  # noqa: F403
from .TTI import *
from .TTS import *
from .scout import *
from .search import *
from .swiftcli import *
from .update_checker import check_for_updates
from .version import __version__

# x0gpt.py and X0GPT removed; no import here
from .zeroart import *

useragent = LitAgent()

# Check for updates on import to notify users of new versions
try:
    update_message = check_for_updates(force=True)
    if update_message:
        print(update_message)
except Exception:
    pass


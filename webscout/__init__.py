# webscout/__init__.py

from .AIauto import *  # noqa: F403
from .AIutel import *  # noqa: F403
from .client import Client
from .Extra import *  # noqa: F403
from .litagent import LitAgent
from .models import model
from .optimizers import *
from .Provider import *
from .Provider.AISEARCH import *
from .Provider.STT import *  # noqa: F403
from .Provider.TTI import *
from .Provider.TTS import *
from .scout import *
from .search import *
from .swiftcli import *
from .update_checker import check_for_updates
from .version import __version__
from .zeroart import *

useragent = LitAgent()
try:
    update_message = check_for_updates(force=False)
    if update_message:
        print(update_message)
except Exception:
    pass


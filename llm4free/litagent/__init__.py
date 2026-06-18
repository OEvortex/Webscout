"""
LitAgent - A lit user agent generator with infinite possibilities! 🔥

Examples:
>>> from llm4free import LitAgent
>>> agent = LitAgent()
>>>
>>> # Get random user agents
>>> agent.random()  # Random agent from any browser
>>> agent.mobile()  # Random mobile device agent
>>> agent.desktop()  # Random desktop agent
>>>
>>> # Browser specific agents
>>> agent.chrome()  # Latest Chrome browser
>>> agent.firefox()  # Latest Firefox browser
>>> agent.safari()  # Latest Safari browser
>>> agent.edge()  # Latest Edge browser
>>> agent.opera()  # Latest Opera browser
>>>
>>> # Refresh your agents
>>> agent.refresh()  # Get fresh new agents
"""

from .agent import LitAgent
from .constants import BROWSERS, DEVICES, FINGERPRINTS, OS_VERSIONS

agent = LitAgent()

__all__ = ['LitAgent', 'agent', 'BROWSERS', 'OS_VERSIONS', 'DEVICES', 'FINGERPRINTS']

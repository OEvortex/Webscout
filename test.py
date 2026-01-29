# from webscout.Extra.proxy_manager import ProxyManager
# pm = ProxyManager(auto_fetch=True, debug=True)
# pm.patch()
from webscout import DeepInfra
ai = DeepInfra()
resp = ai.chat("Hello, how are you?")
print(resp)
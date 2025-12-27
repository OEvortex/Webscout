# from webscout.AIauto import AUTO

# client = AUTO(print_provider_info=True)
# ai = client.chat("Hello, how can I assist you today?", stream=True)
# for message in ai:
#     print(message, end="", flush=True)

from webscout import GEMINI

client = GEMINI(cookie_file=r"C:\Users\koula\Desktop\Webscout\cookies.json", model="latest")
ai = client.chat("Hello, how can I assist you today?", stream=True)
for message in ai:
    print(message, end="", flush=True)

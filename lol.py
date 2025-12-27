from webscout.AIauto import AUTO

client = AUTO(print_provider_info=True)
ai = client.chat("Hello, how can I assist you today?", stream=True)
while True:
    for message in ai:
        print(message, end="", flush=True)

from webscout.Provider.OPENAI import FreeAIChat

# Initialize the client
client = FreeAIChat()

# Create a streaming completion
stream = client.chat.completions.create(
    model="GPT 4o Search Preview",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a short poem about programming."}
    ],
    stream=True
)

# Process the streaming response
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()  # Add a newline at the end
from openai import OpenAI
client = OpenAI(base_url="https://api.algion.dev/v1", api_key="123123")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "Hello!"},
    ],
)
print(response.choices[0].message.content)
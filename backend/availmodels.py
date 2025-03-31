import openai

client = openai.OpenAI(
    api_key="xx",
    base_url="xx"
)

try:
    models = client.models.list()
    print("Available Models:", [model.id for model in models.data])
except Exception as e:
    print("Error:", e)

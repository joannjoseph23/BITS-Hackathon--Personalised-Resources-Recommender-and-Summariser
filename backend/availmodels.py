import openai

client = openai.OpenAI(
    api_key="eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIyZjMwMDA4MTNAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.nPKeq-eyBGukb9oFj-0NIc1iZLlMv1NQfG3boAB2SL4re",
    base_url="https://aiproxy.sanand.workers.dev/openai/v1"
)

try:
    models = client.models.list()
    print("Available Models:", [model.id for model in models.data])
except Exception as e:
    print("Error:", e)

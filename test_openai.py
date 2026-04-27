from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

response = client.responses.create(
    model="gpt-5.4-mini",
    input="Responda apenas com: API do LexiFlow funcionando."
)

print(response.output_text)
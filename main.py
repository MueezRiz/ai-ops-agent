from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(request: ChatRequest):
    response = client.chat.completions.create(
        model="llama3.2",
        messages=[
            {"role": "user", "content": request.message}
        ]
    )
    return {"reply": response.choices[0].message.content}
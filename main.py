
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from db import create_conversation, save_message, get_messages
from agent import agent

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

@app.post("/chat")
def chat(request: ChatRequest):
    # Get or create a conversation ID for memory tracking
    if request.conversation_id:
        conversation_id = request.conversation_id
    else:
        conversation_id = create_conversation()

    # Save the incoming user message to DB
    save_message(conversation_id, "user", request.message)

    # Run the full LangGraph agent — retrieval, decision, tool call, response
    result = agent.invoke({
        "user_message": request.message,
        "retrieved_context": "",
        "tool_name": None,
        "tool_input": None,
        "tool_result": None,
        "final_response": ""
    })

    reply = result["final_response"]

    # Save the assistant's reply to DB
    save_message(conversation_id, "assistant", reply)

    return {"reply": reply, "conversation_id": conversation_id}
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from db import create_conversation, save_message, get_messages
from agent import agent
from logger import logger

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

@app.post("/chat")
def chat(request: ChatRequest):
    logger.info(f"Received message: {request.message}")

    if request.conversation_id:
        conversation_id = request.conversation_id
    else:
        conversation_id = create_conversation()

    save_message(conversation_id, "user", request.message)

    result = agent.invoke({
        "user_message": request.message,
        "retrieved_context": "",
        "tool_name": None,
        "tool_input": None,
        "tool_result": None,
        "final_response": ""
    })

    reply = result["final_response"]
    logger.info(f"Final response generated for conversation {conversation_id}")

    save_message(conversation_id, "assistant", reply)

    return {"reply": reply, "conversation_id": conversation_id}

@app.post("/test-retry")
def test_retry():
    conversation_id = create_conversation()
    user_message = "Can you check the order status for me please?"
    logger.info(f"Received message: {user_message}")

    save_message(conversation_id, "user", user_message)

    result = agent.invoke({
        "user_message": user_message,
        "retrieved_context": "",
        "tool_name": None,
        "tool_input": None,
        "tool_result": None,
        "final_response": "",
        "retry_count": 0
    })

    reply = result["final_response"]
    logger.info(f"Final response generated for conversation {conversation_id}")
    save_message(conversation_id, "assistant", reply)

    return {"response": reply}
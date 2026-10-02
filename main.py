from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from db import create_conversation, save_message, get_messages
from agent import agent
from logger import logger
from langchain_core.messages import HumanMessage, AIMessage

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

    # Load prior messages from DB and convert to LangChain message objects
    history = get_messages(conversation_id)
    prior_messages = []
    for msg in history[:-1]:  # exclude the message we just saved
        if msg["role"] == "user":
            prior_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            prior_messages.append(AIMessage(content=msg["content"]))

    result = agent.invoke({
        "user_message": request.message,
        "retrieved_context": "",
        "tool_name": None,
        "tool_input": None,
        "tool_result": None,
        "final_response": "",
        "messages": prior_messages,
        "retry_count": 0
    })

    reply = result["final_response"]
    logger.info(f"Final response generated for conversation {conversation_id}")

    save_message(conversation_id, "assistant", reply)

    return {"reply": reply, "conversation_id": conversation_id}
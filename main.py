from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import json
from tools import check_order_status, create_ticket, escalate_to_human
from db import create_conversation, save_message, get_messages
from typing import Optional


app = FastAPI()
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "check_order_status",
            "description": "Check the status of a customer order by order ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to check"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Creates a support ticket for a customer issue",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue": {
                        "type": "string",
                        "description": "A description of the customer's issue"
                    }
                },
                "required": ["issue"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "Escalates the conversation to a human support agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "The reason for escalating to a human"
                    }
                },
                "required": ["reason"]
            }
        }
    }
]

TOOL_MAP = {
    "check_order_status": check_order_status,
    "create_ticket": create_ticket,
    "escalate_to_human": escalate_to_human,
}

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

@app.post("/chat")
def chat(request: ChatRequest):
    if request.conversation_id:
        conversation_id = request.conversation_id
    else:
        conversation_id = create_conversation()

    history = get_messages(conversation_id)

    messages = [
        {
            "role": "system",
            "content": """You are a helpful customer service assistant for a clothing brand.
Use the available tools when appropriate:
- check_order_status: when a customer asks about an order
- create_ticket: when a customer reports a problem that needs tracking
- escalate_to_human: when a customer is frustrated or requests a human agent

When you receive a tool result, summarize it naturally in plain English. Never repeat the function call syntax in your response."""
        }
    ]

    messages.extend(history)
    messages.append({"role": "user", "content": request.message})

    save_message(conversation_id, "user", request.message)

    response = client.chat.completions.create(
        model="qwen2.5",
        messages=messages,
        tools=tools
    )

    choice = response.choices[0]

    
if choice.finish_reason == "tool_calls":
    tool_call = choice.message.tool_calls[0]
    tool_name = tool_call.function.name

    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as e:
        reply = "I tried to use a tool but something went wrong parsing the request. Could you rephrase that?"
        save_message(conversation_id, "assistant", reply)
        return {"reply": reply, "conversation_id": conversation_id}

    tool_fn = TOOL_MAP.get(tool_name)

    if not tool_fn:
        reply = f"I tried to use an unknown tool '{tool_name}'. Please try again."
        save_message(conversation_id, "assistant", reply)
        return {"reply": reply, "conversation_id": conversation_id}

    try:
        tool_result = tool_fn(**arguments)
    except Exception as e:
        reply = "I ran into an issue while processing your request. Please try again or rephrase your question."
        save_message(conversation_id, "assistant", reply)
        return {"reply": reply, "conversation_id": conversation_id}

    messages.append(choice.message)
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(tool_result)
    })

    final_response = client.chat.completions.create(
        model="qwen2.5",
        messages=messages,
        tools=tools
    )

    reply = final_response.choices[0].message.content
    save_message(conversation_id, "assistant", reply)
    return {"reply": reply, "conversation_id": conversation_id}
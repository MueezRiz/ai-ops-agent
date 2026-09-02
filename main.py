from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import json
from tools import check_order_status, create_ticket, escalate_to_human

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


@app.post("/chat")
def chat(request: ChatRequest):
    messages = [
        {
            "role": "system",
            "content": """ou are a helpful customer service assistant for a clothing brand.
Use the available tools when appropriate:
- check_order_status: when a customer asks about an order
- create_ticket: when a customer reports a problem that needs tracking
- escalate_to_human: when a customer is frustrated or requests a human agent

When you receive a tool result, summarise it naturally in plain English. Never repeat the function call syntax in your response."""
        },
        {"role": "user", "content": request.message}
    ]

    response = client.chat.completions.create(
        model="qwen2.5",
        messages=messages,
        tools=tools
    )

    choice = response.choices[0]

    if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
        # Append the assistant's message as a plain dict (not the raw SDK object)
        # so it serializes correctly on the next API call, including all tool_calls.
        messages.append({
            "role": "assistant",
            "content": choice.message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in choice.message.tool_calls
            ]
        })

        # Handle EVERY tool call the model asked for, not just the first one.
        for tool_call in choice.message.tool_calls:
            tool_name = tool_call.function.name
            tool_fn = TOOL_MAP.get(tool_name)

            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_result = {"error": "Invalid arguments returned by model"}
            else:
                if tool_fn is None:
                    tool_result = {"error": f"Unknown tool: {tool_name}"}
                else:
                    try:
                        tool_result = tool_fn(**arguments)
                    except Exception as e:
                        tool_result = {"error": f"Tool execution failed: {str(e)}"}

            # Each tool result must be its own message, matched by tool_call_id.
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result)
            })

        final_response = client.chat.completions.create(
            model="qwen2.5",
            messages=messages
        )

        return {"reply": final_response.choices[0].message.content}

    # No tool needed — return direct response
    return {"reply": choice.message.content}
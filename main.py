from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import json
from tools import check_order_status

app = FastAPI()

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

# Define the tool in a format the model understands
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
    }
]

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(request: ChatRequest):
    messages = [
        {
            "role": "system",
            "content": """You are a helpful customer service assistant for a clothing brand.
When a customer asks about an order status, you MUST use the check_order_status tool.
Do not answer order status questions from memory — always call the tool first."""
        },
        {
            "role": "user",
            "content": request.message
        }
    ]
    
    # First call — let model decide if it needs a tool
    response = client.chat.completions.create(
        model="mistral",
        messages=messages,
        tools=tools
    )
    
    choice = response.choices[0]
    
    # Check if model wants to call a tool
    if choice.finish_reason == "tool_calls":
        tool_call = choice.message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)
        
        # Call the actual tool function
        tool_result = check_order_status(arguments["order_id"])
        
        # Second call — send tool result back to model for final answer
        messages.append(choice.message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(tool_result)
        })
        
        final_response = client.chat.completions.create(
            model="mistral",
            messages=messages
        )
        
        return {"reply": final_response.choices[0].message.content}
    
    # No tool needed — return direct response
    return {"reply": choice.message.content}
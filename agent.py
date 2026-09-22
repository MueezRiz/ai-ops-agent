from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from tools import check_order_status, create_ticket, escalate_to_human
from retriever import retrieve

# LLM setup — runs locally via Ollama, no API key needed
llm = ChatOllama(model="llama3.2")

# Everything the agent needs to pass between nodes
class AgentState(TypedDict):
    user_message: str
    retrieved_context: str
    tool_name: Optional[str]
    tool_input: Optional[dict]
    tool_result: Optional[str]
    final_response: str

# Wrap your existing tool functions so LangChain can bind them
@tool
def check_order_status_tool(order_id: str) -> str:
    """Check the status of an order by order ID."""
    return str(check_order_status(order_id))

@tool
def create_ticket_tool(issue: str) -> str:
    """Create a support ticket for a customer issue."""
    return str(create_ticket(issue))

@tool
def escalate_to_human_tool(reason: str) -> str:
    """Escalate a conversation to a human agent."""
    return str(escalate_to_human(reason))

tools = [check_order_status_tool, create_ticket_tool, escalate_to_human_tool]
llm_with_tools = llm.bind_tools(tools)

# Node 1: retrieve relevant FAQ context for the user's message
def retrieve_node(state: AgentState) -> AgentState:
    context = retrieve(state["user_message"])
    return {"retrieved_context": context}

# Node 2: ask the LLM what to do — answer directly or call a tool
def decide_node(state: AgentState) -> AgentState:
    messages = [
        SystemMessage(content=f"You are a helpful assistant for a small business. Use this context to answer if relevant:\n{state['retrieved_context']}"),
        HumanMessage(content=state["user_message"])
    ]

    response = llm_with_tools.invoke(messages)

    # Check if the model wants to call a tool
    if response.tool_calls:
        first_tool = response.tool_calls[0]
        return {
            "tool_name": first_tool["name"],
            "tool_input": first_tool["args"]
        }

    # No tool needed — return the text response directly
    return {
        "tool_name": None,
        "final_response": response.content
    }

# Node 3: actually run whichever tool the LLM chose
def call_tool_node(state: AgentState) -> AgentState:
    tool = state["tool_name"]
    tool_input = state.get("tool_input") or {}

    if tool == "check_order_status_tool":
        result = check_order_status(tool_input.get("order_id", ""))
    elif tool == "create_ticket_tool":
        result = create_ticket(tool_input.get("issue", ""))
    elif tool == "escalate_to_human_tool":
        result = escalate_to_human(tool_input.get("reason", ""))
    else:
        result = "Unknown tool requested"

    return {"tool_result": str(result)}

# Node 4: generate a natural final response using the tool result
def respond_node(state: AgentState) -> AgentState:
    messages = [
        SystemMessage(content="You are a helpful assistant. Summarize the tool result naturally for the user."),
        HumanMessage(content=state["user_message"]),
        HumanMessage(content=f"Tool result: {state['tool_result']}")
    ]

    response = llm.invoke(messages)
    return {"final_response": response.content}

# Route after decide: tool needed → call_tool, otherwise → END
def route_after_decide(state: AgentState) -> str:
    if state.get("tool_name"):
        return "call_tool"
    return END

# Build the graph
def build_agent():
    graph = StateGraph(AgentState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("decide", decide_node)
    graph.add_node("call_tool", call_tool_node)
    graph.add_node("respond", respond_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "decide")
    graph.add_conditional_edges("decide", route_after_decide, {
        "call_tool": "call_tool",
        END: END
    })
    graph.add_edge("call_tool", "respond")
    graph.add_edge("respond", END)

    return graph.compile()

agent = build_agent()

if __name__ == "__main__":
    result = agent.invoke({
        "user_message": "What are your opening hours?",
        "retrieved_context": "",
        "tool_name": None,
        "tool_input": None,
        "tool_result": None,
        "final_response": ""
    })
    print(result["final_response"])
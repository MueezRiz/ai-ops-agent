from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from tools import check_order_status, create_ticket, escalate_to_human
from retriever import retrieve
from langchain_core.messages import BaseMessage


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
    messages: list[BaseMessage]  

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
    system = SystemMessage(content=f"""You are a helpful customer service assistant for a small business.
Use this context to answer if relevant:\n{context}
When asked to take action based on a condition, check the condition from tool results and act immediately without asking for confirmation.
Once you have completed all required actions, give a final summary response to the user.""")
    human = HumanMessage(content=state["user_message"])
    return {"retrieved_context": context, "messages": [system, human]}

# Node 2: ask the LLM what to do — loop until no more tool calls
def decide_node(state: AgentState) -> AgentState:
    response = llm_with_tools.invoke(state["messages"])
    updated_messages = state["messages"] + [response]

    print(f"DEBUG tool_calls: {response.tool_calls}")
    print(f"DEBUG content: {response.content[:200]}")

    if response.tool_calls:
        return {
            "messages": updated_messages,
            "tool_name": response.tool_calls[0]["name"],   # just for routing
            "tool_input": response.tool_calls,             # store ALL tool calls
            "tool_result": None
        }

    return {
        "messages": updated_messages,
        "tool_name": None,
        "final_response": response.content
    }

# Node 3: run the chosen tool, then route back to decide for another pass
def call_tool_node(state: AgentState) -> AgentState:
    from langchain_core.messages import ToolMessage

    tool_calls = state.get("tool_input") or []
    updated_messages = list(state["messages"])
    results = []

    for tc in tool_calls:
        name = tc["name"]
        args = tc.get("args", {})
        tool_call_id = tc.get("id", "unknown")

        if name == "check_order_status_tool":
            result = check_order_status(args.get("order_id", ""))
        elif name == "create_ticket_tool":
            result = create_ticket(args.get("issue", ""))
        elif name == "escalate_to_human_tool":
            result = escalate_to_human(args.get("reason", ""))
        else:
            result = "Unknown tool"

        result_str = str(result)
        results.append(result_str)
        print(f"DEBUG ran tool: {name} → {result_str}")
        updated_messages.append(ToolMessage(content=result_str, tool_call_id=tool_call_id))

    return {
        "tool_result": " | ".join(results),
        "messages": updated_messages
    }

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
    graph.add_edge("call_tool", "decide")  # loop back after each tool call
    graph.add_edge("respond", END)

    return graph.compile()

agent = build_agent()


if __name__ == "__main__":
    result = agent.invoke({
    "user_message": request.message,
    "retrieved_context": "",
    "tool_name": None,
    "tool_input": None,
    "tool_result": None,
    "final_response": "",
    "messages": []
   })

    print(result["final_response"])
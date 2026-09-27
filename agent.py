from typing import Optional, TypedDict
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from retriever import retrieve
from tools import check_order_status, create_ticket, escalate_to_human
from logger import logger

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
    messages: Annotated[list, add_messages]
    retry_count: int

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

tools = [
    check_order_status_tool,
    create_ticket_tool,
    escalate_to_human_tool,
]

llm_with_tools = llm.bind_tools(tools)

# Node 1: retrieve relevant FAQ context for the user's message
def retrieve_node(state: AgentState) -> AgentState:
    logger.info(f"Retrieving context for: {state['user_message']}")
    context = retrieve(state["user_message"])

    system = SystemMessage(
        content=f"""You are a helpful customer service assistant for a small business. Use this context to answer if relevant: {context}

When asked to take action based on a condition, check the condition from tool results and act immediately without asking for confirmation.

Once you have completed all required actions, give a final summary response to the user."""
    )

    human = HumanMessage(content=state["user_message"])

    return {
        "retrieved_context": context,
        "messages": [system, human],
    }

# Node 2: ask the LLM what to do — loop until no more tool calls
def decide_node(state: AgentState) -> AgentState:
    response = llm_with_tools.invoke(state["messages"])
    updated_messages = state["messages"] + [response]

    if response.tool_calls:
        tool_name = response.tool_calls[0]["name"]
        logger.info(f"Tool selected: {tool_name} with args: {response.tool_calls[0].get('args', {})}")
        return {
            "messages": updated_messages,
            "tool_name": tool_name,
            "tool_input": response.tool_calls,
            "tool_result": None,
        }

    logger.info("No tool call — generating final response")
    return {
        "messages": updated_messages,
        "tool_name": None,
        "final_response": response.content,
    }

def validate_tool_args(name: str, args: dict) -> Optional[str]:
    """Returns an error string if args are invalid, None if OK."""
    if name == "check_order_status_tool" and not args.get("order_id"):
        return "Missing required argument: order_id"
    if name == "create_ticket_tool" and not args.get("issue"):
        return "Missing required argument: issue"
    if name == "escalate_to_human_tool" and not args.get("reason"):
        return "Missing required argument: reason"
    return None

# Node 3: run the chosen tool, then route back to decide
def call_tool_node(state: AgentState):
    messages = state["messages"]
    retry_count = state.get("retry_count", 0)
    last_message = messages[-1]
    tool_calls = last_message.additional_kwargs.get("tool_calls", [])

    if hasattr(last_message, "tool_calls"):
        tool_calls = last_message.tool_calls

    updated_messages = []
    needs_retry = False

    for tc in tool_calls:
        name = tc["name"]
        args = tc.get("args", {})
        tool_call_id = tc.get("id", "unknown")

        validation_error = validate_tool_args(name, args)

        if validation_error and retry_count < 1:
            logger.warning(f"Retry triggered for {name}: {validation_error}")
            updated_messages.append(
                ToolMessage(
                    content=f"Error: {validation_error}. Please retry the tool call with all required arguments.",
                    tool_call_id=tool_call_id
                )
            )
            needs_retry = True
        else:
            try:
                logger.info(f"Calling tool: {name} with args: {args}")
                if name == "check_order_status_tool":
                    result = check_order_status(args.get("order_id", ""))
                elif name == "create_ticket_tool":
                    result = create_ticket(args.get("issue", ""))
                elif name == "escalate_to_human_tool":
                    result = escalate_to_human(args.get("reason", ""))
                else:
                    result = f"Unknown tool: {name}"
                logger.info(f"Tool {name} returned: {result}")
            except Exception as e:
                logger.error(f"Tool '{name}' failed with error: {e}")
                result = f"Tool '{name}' failed with error: {str(e)}"

            updated_messages.append(
                ToolMessage(content=str(result), tool_call_id=tool_call_id)
            )

    new_retry_count = retry_count + 1 if needs_retry else 0
    return {"messages": updated_messages, "retry_count": new_retry_count}

# Node 4: generate a natural final response using the tool result
def respond_node(state: AgentState) -> AgentState:
    logger.info("Generating final response from tool result")
    messages = [
        SystemMessage(
            content=(
                "You are a helpful assistant. Summarize the tool result "
                "naturally for the user."
            )
        ),
        HumanMessage(content=state["user_message"]),
        HumanMessage(content=f"Tool result: {state['tool_result']}"),
    ]

    response = llm.invoke(messages)

    return {
        "final_response": response.content,
    }

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

    graph.add_conditional_edges(
        "decide",
        route_after_decide,
        {
            "call_tool": "call_tool",
            END: END,
        },
    )

    graph.add_edge("call_tool", "decide")
    graph.add_edge("respond", END)

    return graph.compile()

agent = build_agent()

if __name__ == "__main__":
    result = agent.invoke(
        {
            "user_message": "What are your hours?",
            "retrieved_context": "",
            "tool_name": None,
            "tool_input": None,
            "tool_result": None,
            "final_response": "",
            "messages": [],
        }
    )

    print(result["final_response"])
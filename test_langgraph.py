from typing import TypedDict
from langgraph.graph import StateGraph, END

# This defines what "state" looks like as it moves through the graph
class State(TypedDict):
    message: str
    response: str

# This is one node — it receives state and returns updated state
def respond(state: State) -> State:
    return {"response": f"Agent received: {state['message']}"}

# Build the graph
graph = StateGraph(State)
graph.add_node("respond", respond)
graph.set_entry_point("respond")
graph.add_edge("respond", END)

app = graph.compile()

# Run it
result = app.invoke({"message": "hello from LangGraph"})
print(result)
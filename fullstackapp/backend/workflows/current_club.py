from typing import TypedDict, Annotated, List
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from operator import add


class InputState(TypedDict):
    article: str


class OutputState(TypedDict):
    agent_output: str


class OverallState(InputState, OutputState):
    messages: Annotated[List[BaseMessage], add]


@tool
def get_current_club(player_name: str):
    """Gets current club of a player"""
    fake_db = {
        "Lionel Messi": "Paris Saint-Germain",
        "Cristiano Ronaldo": "Al Nassr FC",
    }
    return fake_db.get(player_name, "Current club information not available.")


tools_current_club = [get_current_club]
model_current_club = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools_current_club)


def call_model_current_club(state: OverallState):
    local_messages = state.get("messages", [])
    if not local_messages:
        human_message = HumanMessage(content=state["article"])
        local_messages.append(human_message)
    system_message = SystemMessage(
        content="You are an agent tasked with determining the current club of a player."
    )
    response = model_current_club.invoke([system_message] + local_messages)
    state["agent_output"] = response.content
    state["messages"] = local_messages + [response]
    return state


current_club_graph = StateGraph(OverallState, input=InputState, output=OutputState)
current_club_graph.add_node("call_model_current_club", call_model_current_club)
current_club_graph.add_edge(START, "call_model_current_club")
current_club_graph.add_edge("call_model_current_club", END)

current_club_researcher_agent = current_club_graph.compile()

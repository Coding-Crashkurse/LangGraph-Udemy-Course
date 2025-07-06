from operator import add
from typing import Annotated, List, Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

# Load environment variables
load_dotenv()


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


def create_current_club_agent():
    tools_current_club = [get_current_club]
    model_current_club = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools_current_club)

    async def call_model_current_club(state: OverallState):
        local_messages = state.get("messages", [])
        if not local_messages:
            human_message = HumanMessage(content=state["article"])
            local_messages.append(human_message)

        system_message = SystemMessage(
            content="""You are an agent tasked with determining the current club of a player.
If the current club is mentioned, return it. Otherwise, return 'Current club information not available.'"""
        )

        response = await model_current_club.ainvoke([system_message] + local_messages)

        state["agent_output"] = response.content
        state["messages"] = local_messages + [response]
        return state

    def should_continue(state: OverallState) -> Literal["tools", END]:
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "tools"
        return END

    current_club_graph = StateGraph(state_schema=OverallState, input_schema=InputState, output_schema=OutputState)
    current_club_graph.add_node("call_model_current_club", call_model_current_club)
    current_club_graph.add_node("tools", ToolNode(tools_current_club))
    current_club_graph.add_edge(START, "call_model_current_club")
    current_club_graph.add_conditional_edges("call_model_current_club", should_continue)
    current_club_graph.add_edge("tools", "call_model_current_club")

    return current_club_graph.compile()

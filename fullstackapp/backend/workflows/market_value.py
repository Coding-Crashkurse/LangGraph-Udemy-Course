import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated, List, Literal
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from operator import add

# Load environment variables
load_dotenv()


class InputState(TypedDict):
    article: str


class OutputState(TypedDict):
    agent_output: str


class OverallState(InputState, OutputState):
    messages: Annotated[List[BaseMessage], add]


@tool
def get_market_value(player_name: str):
    """Gets current market value of a player"""
    fake_market_value_db = {
        "Lionel Messi": "€50 million",
        "Cristiano Ronaldo": "€30 million",
    }
    return fake_market_value_db.get(
        player_name, "Market value information not available."
    )


def create_market_value_agent():
    tools_market_value = [get_market_value]
    model_market_value = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools_market_value)

    def call_model_market_value(state: OverallState):

        local_messages = state.get("messages", [])
        if not local_messages:
            human_message = HumanMessage(content=state["article"])
            local_messages.append(human_message)

        system_message = SystemMessage(
            content="""You are an agent tasked with determining the market value of a player.
If the market value is mentioned, return it. Otherwise, return 'Market value information not available.'"""
        )

        response = model_market_value.invoke([system_message] + local_messages)

        state["agent_output"] = response.content
        state["messages"] = local_messages + [response]

        return state

    def should_continue(state: OverallState) -> Literal["tools", END]:
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "tools"
        return END

    market_value_graph = StateGraph(OverallState, input=InputState, output=OutputState)
    market_value_graph.add_node("call_model_market_value", call_model_market_value)
    market_value_graph.add_node("tools", ToolNode(tools_market_value))
    market_value_graph.add_edge(START, "call_model_market_value")
    market_value_graph.add_conditional_edges("call_model_market_value", should_continue)
    market_value_graph.add_edge("tools", "call_model_market_value")

    return market_value_graph.compile()

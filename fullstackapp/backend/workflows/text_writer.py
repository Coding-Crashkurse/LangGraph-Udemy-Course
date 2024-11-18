from typing import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI


class InputState(TypedDict):
    article: str


class OutputState(TypedDict):
    agent_output: str


class OverallState(InputState, OutputState):
    pass


model_text_writer = ChatOpenAI(model="gpt-4o-mini")


def expand_text_to_100_words(state: OverallState):
    human_message = HumanMessage(content=state["article"])
    system_message = SystemMessage(
        content="Expand the following text to be at least 100 words. Maintain the original meaning while adding detail."
    )
    response = model_text_writer.invoke([system_message, human_message])
    state["agent_output"] = response.content
    return state


text_writer_graph = StateGraph(OverallState, input=InputState, output=OutputState)
text_writer_graph.add_node("expand_text_to_100_words", expand_text_to_100_words)
text_writer_graph.add_edge(START, "expand_text_to_100_words")
text_writer_graph.add_edge("expand_text_to_100_words", END)

text_writer_agent = text_writer_graph.compile()

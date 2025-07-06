from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph


class InputState(TypedDict):
    article: str


class OutputState(TypedDict):
    agent_output: str


class OverallState(InputState, OutputState):
    pass


def create_text_writer_agent():
    model_text_writer = ChatOpenAI(model="gpt-4o-mini")

    async def expand_text_to_100_words(state: OverallState):
        human_message = HumanMessage(content=state["article"])
        system_message = SystemMessage(
            content="Expand the following text to be at least 100 words. Maintain the original meaning while adding detail. Treat the original text as credible source. Just expand the text, no interpretation or anything else!"
        )
        response = await model_text_writer.ainvoke([system_message, human_message])
        state["agent_output"] = response.content
        return state

    text_writer_graph = StateGraph(state_schema=OverallState, input_schema=InputState, output_schema=OutputState)
    text_writer_graph.add_node("expand_text_to_100_words", expand_text_to_100_words)
    text_writer_graph.add_edge(START, "expand_text_to_100_words")
    text_writer_graph.add_edge("expand_text_to_100_words", END)

    return text_writer_graph.compile()

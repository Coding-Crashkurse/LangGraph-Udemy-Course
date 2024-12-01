import pytest
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage

from code_to_test import AgentState


@pytest.fixture
def state():
    """
    Fixture for the AgentState, keeping in mind that it is mutable.
    """
    return AgentState(
        question="What is AI?",
        messages=[HumanMessage(content="What is AI?")],
        prompt="Please answer the question:",
        answer="",
        on_topic="yes",
        context=[Document(page_content="test1"), Document(page_content="test2")],
    )

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from unit_tests.code_to_test import llm_node


@patch("unit_tests.code_to_test.create_llm")
@pytest.mark.asyncio
async def test_llm_node(mock_create_llm, state):
    """
    Test the async llm_node function with a mocked LLM.
    """
    mock_llm = AsyncMock()
    mock_response = AsyncMock()
    mock_response.content = "Mocked AI response"
    mock_llm.ainvoke.return_value = mock_response
    mock_create_llm.return_value = mock_llm

    mock_prompt = MagicMock()
    mock_prompt.messages = state["messages"]
    state["prompt"] = mock_prompt

    updated_state = await llm_node(state)

    assert updated_state["answer"] == "Mocked AI response"
    assert updated_state["messages"][-1] == AIMessage(content="Mocked AI response")
    mock_llm.ainvoke.assert_called_once_with(state["messages"])
    mock_create_llm.assert_called_once()

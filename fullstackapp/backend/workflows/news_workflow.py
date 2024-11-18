from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from current_club import current_club_researcher_agent
from market_value import market_value_researcher_agent
from text_writer import text_writer_agent


class InputArticleState(TypedDict):
    article: str


class OutputFinalArticleState(TypedDict):
    final_article: str


class SharedArticleState(InputArticleState, OutputFinalArticleState):
    mentions_market_value: str
    mentions_current_club: str
    meets_100_words: str


def update_article_state(state: SharedArticleState) -> SharedArticleState:
    # Simulate an evaluation of the article state
    state["mentions_market_value"] = (
        "no" if "market value" not in state["article"] else "yes"
    )
    state["mentions_current_club"] = "no" if "club" not in state["article"] else "yes"
    state["meets_100_words"] = "yes" if len(state["article"].split()) >= 100 else "no"
    return state


def market_value_researcher_node(state: SharedArticleState) -> SharedArticleState:
    response = market_value_researcher_agent.invoke({"article": state["article"]})
    state["article"] += f" {response['agent_output']}"
    return state


def current_club_researcher_node(state: SharedArticleState) -> SharedArticleState:
    response = current_club_researcher_agent.invoke({"article": state["article"]})
    state["article"] += f" {response['agent_output']}"
    return state


def word_count_rewriter_node(state: SharedArticleState) -> SharedArticleState:
    response = text_writer_agent.invoke({"article": state["article"]})
    state["article"] += f" {response['agent_output']}"
    state["final_article"] = response["agent_output"]
    return state


def news_chef_decider(
    state: SharedArticleState,
) -> Literal[
    "market_value_researcher", "current_club_researcher", "word_count_rewriter", END
]:
    if state["mentions_market_value"] == "no":
        return "market_value_researcher"
    elif state["mentions_current_club"] == "no":
        return "current_club_researcher"
    elif state["meets_100_words"] == "no":
        return "word_count_rewriter"
    else:
        return END


workflow = StateGraph(
    SharedArticleState, input=InputArticleState, output=OutputFinalArticleState
)
workflow.add_node("news_chef", update_article_state)
workflow.add_node("market_value_researcher", market_value_researcher_node)
workflow.add_node("current_club_researcher", current_club_researcher_node)
workflow.add_node("word_count_rewriter", word_count_rewriter_node)
workflow.set_entry_point("news_chef")
workflow.add_conditional_edges(
    "news_chef",
    news_chef_decider,
    {
        "market_value_researcher": "market_value_researcher",
        "current_club_researcher": "current_club_researcher",
        "word_count_rewriter": "word_count_rewriter",
        END: END,
    },
)
workflow.add_edge("market_value_researcher", "news_chef")
workflow.add_edge("current_club_researcher", "news_chef")
workflow.add_edge("word_count_rewriter", "news_chef")

app = workflow.compile()
checkpointer = MemorySaver()
human_app = workflow.compile(checkpointer=checkpointer, interrupt_after=["news_chef"])

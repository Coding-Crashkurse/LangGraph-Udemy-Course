from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from .current_club import create_current_club_agent
from .market_value import create_market_value_agent
from .text_writer import create_text_writer_agent


class InputArticleState(TypedDict):
    article: str


class OutputFinalArticleState(TypedDict):
    final_article: str


class SharedArticleState(InputArticleState, OutputFinalArticleState):
    mentions_market_value: str
    mentions_current_club: str
    meets_100_words: str


class NewsWorkflow:
    def __init__(self):
        self.current_club_agent = create_current_club_agent()
        self.market_value_agent = create_market_value_agent()
        self.text_writer_agent = create_text_writer_agent()
        self.workflow = self._create_workflow()

    def update_article_state(self, state: SharedArticleState) -> SharedArticleState:
        state["mentions_market_value"] = (
            "no" if "market value" not in state["article"] else "yes"
        )
        state["mentions_current_club"] = (
            "no" if "club" not in state["article"] else "yes"
        )
        state["meets_100_words"] = (
            "yes" if len(state["article"].split()) >= 100 else "no"
        )
        return state

    def market_value_researcher_node(
        self, state: SharedArticleState
    ) -> SharedArticleState:
        response = self.market_value_agent.invoke({"article": state["article"]})
        state["article"] += f" {response['agent_output']}"
        return state

    def current_club_researcher_node(
        self, state: SharedArticleState
    ) -> SharedArticleState:
        response = self.current_club_agent.invoke({"article": state["article"]})
        state["article"] += f" {response['agent_output']}"
        return state

    def word_count_rewriter_node(self, state: SharedArticleState) -> SharedArticleState:
        response = self.text_writer_agent.invoke({"article": state["article"]})
        state["article"] += f" {response['agent_output']}"
        state["final_article"] = response["agent_output"]
        return state

    def news_chef_decider(
        self,
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

    def _create_workflow(self):
        workflow = StateGraph(
            SharedArticleState, input=InputArticleState, output=OutputFinalArticleState
        )
        workflow.add_node("news_chef", self.update_article_state)
        workflow.add_node("market_value_researcher", self.market_value_researcher_node)
        workflow.add_node("current_club_researcher", self.current_club_researcher_node)
        workflow.add_node("word_count_rewriter", self.word_count_rewriter_node)
        workflow.set_entry_point("news_chef")
        workflow.add_conditional_edges(
            "news_chef",
            self.news_chef_decider,
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

        return workflow.compile()

    def invoke(self, state: InputArticleState):
        return self.workflow.invoke(state)

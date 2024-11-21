from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from .current_club import create_current_club_agent
from .market_value import create_market_value_agent
from .text_writer import create_text_writer_agent


class ArticlePostabilityGrader(BaseModel):
    """Binary scores for verifying if an article mentions market value, current club, and meets the minimum word count of 100 words."""

    mentions_market_value: str = Field(
        description="The article mentions the player's market value, 'yes' or 'no'"
    )
    mentions_current_club: str = Field(
        description="The article mentions the player's current club, 'yes' or 'no'"
    )
    meets_100_words: str = Field(
        description="The article has at least 100 words, 'yes' or 'no'"
    )


class InputArticleState(TypedDict):
    article: str


class OutputFinalArticleState(TypedDict):
    final_article: str


class SharedArticleState(InputArticleState, OutputFinalArticleState):
    mentions_market_value: str
    mentions_current_club: str
    meets_100_words: str


class NewsWorkflow:
    def __init__(self, llm_model="gpt-4o-mini", temperature=0):
        self.current_club_agent = create_current_club_agent()
        self.market_value_agent = create_market_value_agent()
        self.text_writer_agent = create_text_writer_agent()
        self.llm_postability = ChatOpenAI(model=llm_model, temperature=temperature)
        self.workflow = self._create_workflow()

    def _create_postability_grader(self):
        prompt_template = """
        You are a grader assessing whether a news article meets the following criteria:
        1. The article explicitly mentions the player's market value, for example, by stating "market value" or a specific currency amount (e.g., "$50 million"). If this is present, respond with 'yes' for mentions_market_value; otherwise, respond 'no'.
        2. The article mentions the player's current club or indicates that the current club information is unavailable (e.g., "Current club information not available"). If this is present, respond with 'yes' for mentions_current_club; otherwise, respond 'no'.
        3. The article contains at least 100 words. If this is met, respond with 'yes' for meets_100_words; otherwise, respond 'no'.

        Provide three binary scores ('yes' or 'no') as follows:
        - mentions_market_value: 'yes' or 'no' depending on whether the article mentions the player's market value.
        - mentions_current_club: 'yes' or 'no' depending on whether the article mentions the player's current club or states that the information is unavailable.
        - meets_100_words: 'yes' or 'no' depending on whether the article has at least 100 words.
        """
        postability_system = ChatPromptTemplate.from_messages(
            [("system", prompt_template), ("human", "News Article:\n\n{article}")]
        )
        return postability_system | self.llm_postability.with_structured_output(
            ArticlePostabilityGrader
        )

    def update_article_state(self, state: SharedArticleState) -> SharedArticleState:
        news_chef = self._create_postability_grader()
        response = news_chef.invoke({"article": state["article"]})
        state["mentions_market_value"] = response.mentions_market_value
        state["mentions_current_club"] = response.mentions_current_club
        state["meets_100_words"] = response.meets_100_words
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
            next_node = "market_value_researcher"
        elif state["mentions_current_club"] == "no":
            next_node = "current_club_researcher"
        elif state["meets_100_words"] == "no":
            next_node = "word_count_rewriter"
        else:
            next_node = END
        return next_node

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

    def invoke(self, *args, **kwargs):
        return self.workflow.invoke(*args, **kwargs)

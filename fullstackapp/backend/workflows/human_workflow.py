from typing import TypedDict
from langgraph.graph import StateGraph, END
from .news_workflow import NewsWorkflow
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
import os

DB_URI = "postgresql://postgres:postgres@postgres_local:5432/postgres"


class InputState(TypedDict):
    question: str


class IntermediateState(InputState):
    answer: str
    error: bool


class FinalState(IntermediateState):
    confirmed: str


class HumanWorkflow:
    def __init__(self):
        self.app = NewsWorkflow()
        self.checkpointer = self._create_postgres_checkpointer()
        self.workflow = self._create_workflow()

    def _create_postgres_checkpointer(self):
        connection_kwargs = {
            "autocommit": True,
            "prepare_threshold": 0,
        }
        self.pool = ConnectionPool(
            conninfo=DB_URI,
            max_size=20,
            kwargs=connection_kwargs,
        )
        checkpointer = PostgresSaver(self.pool)
        checkpointer.setup()
        return checkpointer

    def newsagent_node(self, state: IntermediateState) -> IntermediateState:
        try:

            response = self.app.invoke(
                {"article": state["question"]},
            )
            state["answer"] = response.get(
                "final_article", "Article not relevant for news agency"
            )
            state["off_or_ontopic"] = response["off_or_ontopic"]
            state["error"] = False
        except Exception as e:
            state["answer"] = "Error occured while creating a message"
            state["error"] = True
            # Optionally log the exception for debugging
            print(f"Error invoking newsagent_node: {e}")
        return state

    def confirm_node(self, state: FinalState) -> FinalState:
        state["confirmed"] = "true"
        return state

    def _create_workflow(self):
        workflow = StateGraph(FinalState, input=InputState, output=FinalState)
        workflow.add_node("newsagent_node", self.newsagent_node)
        workflow.add_node("confirm_node", self.confirm_node)
        workflow.set_entry_point("newsagent_node")
        workflow.add_edge("newsagent_node", "confirm_node")
        workflow.add_edge("confirm_node", END)
        return workflow.compile(
            checkpointer=self.checkpointer, interrupt_after=["newsagent_node"]
        )

    def invoke(self, *args, **kwargs):
        return self.workflow.invoke(*args, **kwargs)

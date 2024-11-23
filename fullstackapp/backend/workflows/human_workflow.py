from typing import TypedDict
from langgraph.graph import StateGraph, END
from .news_workflow import NewsWorkflow
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

DB_URI = "postgresql://postgres:postgres@localhost:5433/postgres?sslmode=disable"


class InputState(TypedDict):
    question: str


class IntermediateState(InputState):
    answer: str


class FinalState(IntermediateState):
    api_response: str
    status_code: int


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
        response = self.app.invoke({"article": state["question"]})
        state["answer"] = response["final_article"]
        return state

    def api_call_node(self, state: FinalState) -> FinalState:
        state["status_code"] = 200
        state["api_response"] = f"API received answer: {state['answer']}"
        return state

    def _create_workflow(self):
        workflow = StateGraph(FinalState, input=InputState, output=FinalState)
        workflow.add_node("newsagent_node", self.newsagent_node)
        workflow.add_node("api_call_node", self.api_call_node)
        workflow.set_entry_point("newsagent_node")
        workflow.add_edge("newsagent_node", "api_call_node")
        workflow.add_edge("api_call_node", END)
        return workflow.compile(
            checkpointer=self.checkpointer, interrupt_after=["newsagent_node"]
        )

    def invoke(self, *args, **kwargs):
        return self.workflow.invoke(*args, **kwargs)

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .news_workflow import NewsWorkflow


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
        self.checkpointer = MemorySaver()
        self.workflow = self._create_workflow()

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

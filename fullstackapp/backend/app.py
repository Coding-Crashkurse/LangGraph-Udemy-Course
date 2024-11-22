from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from dotenv import load_dotenv
from workflows.human_workflow import HumanWorkflow
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI()

threads = {}  # Dictionary to store thread states


class FakeHumanWorkflow:
    def invoke(self, input=None, config=None, subgraphs=False):
        return {"answer": "Fake HumanWorkflow response for debugging."}


class StartThreadResponse(BaseModel):
    thread_id: str


class ChatRequest(BaseModel):
    question: Optional[str] = None
    config: Optional[dict] = None  # Config with at least thread_id


class ChatResponse(BaseModel):
    human_interrupted: bool
    answer: Optional[str] = None
    api_response: Optional[str] = None
    status_code: Optional[int] = None


@app.post("/start_thread", response_model=StartThreadResponse)
def start_thread():
    thread_id = str(uuid4())
    threads[thread_id] = None  # Initialize thread state
    return StartThreadResponse(thread_id=thread_id)


@app.post("/chat/{debug}", response_model=ChatResponse)
def chat_endpoint(
    debug: bool,
    request: ChatRequest,
):
    # Determine which workflow to use
    if debug:
        human_workflow = FakeHumanWorkflow()
    else:
        human_workflow = HumanWorkflow()

    thread_id = request.config.get("thread_id") if request.config else None

    if not thread_id or thread_id not in threads:
        raise HTTPException(status_code=400, detail="Invalid or missing thread_id.")

    if request.question is not None:
        response_state = human_workflow.invoke(
            input={"question": request.question},
            config={"configurable": {"thread_id": thread_id}},
            subgraphs=True,
        )
    else:
        response_state = human_workflow.invoke(
            input=None,
            config={"configurable": {"thread_id": thread_id}},
            subgraphs=True,
        )

    if isinstance(response_state, tuple) and len(response_state) == 2:
        human_interrupted = True
        response_data = response_state[1]
    else:
        human_interrupted = False
        response_data = response_state

    threads[thread_id] = response_data  # Update thread state

    return ChatResponse(
        human_interrupted=human_interrupted,
        answer=response_data.get("answer"),
        api_response=response_data.get("api_response"),
        status_code=response_data.get("status_code"),
    )


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from workflows.human_workflow import HumanWorkflow
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI()


def get_human_workflow():
    return HumanWorkflow()


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    human_interrupted: bool
    answer: str
    api_response: Optional[str] = None
    status_code: Optional[int] = None


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest, human_workflow: HumanWorkflow = Depends(get_human_workflow)
):
    response_state = human_workflow.invoke(
        input={"question": request.question},
        config={"configurable": {"thread_id": "2"}},
        subgraphs=True,
    )

    if isinstance(response_state, tuple) and len(response_state) == 2:
        human_interrupted = True
        response_data = response_state[1]
    else:
        human_interrupted = False
        response_data = response_state

    return ChatResponse(
        human_interrupted=human_interrupted,
        answer=response_data.get("answer", ""),
        api_response=response_data.get("api_response"),
        status_code=response_data.get("status_code"),
    )


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)

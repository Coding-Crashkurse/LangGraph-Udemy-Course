# app.py
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from workflows.human_workflow import HumanWorkflow
import uvicorn

load_dotenv()

app = FastAPI()


def get_human_workflow():
    return HumanWorkflow()


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    api_response: str
    status_code: int


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest, human_workflow: HumanWorkflow = Depends(get_human_workflow)
):
    initial_state = {"question": request.question}
    response_state = human_workflow.invoke(initial_state)
    print(response_state)
    return ChatResponse(
        answer=response_state["answer"],
        api_response=response_state["api_response"],
        status_code=response_state["status_code"],
    )


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)

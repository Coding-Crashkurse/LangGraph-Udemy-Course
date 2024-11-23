from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
from uuid import uuid4
from dotenv import load_dotenv
from workflows.human_workflow import HumanWorkflow
import uvicorn
from sqlalchemy import Column, String, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Load environment variables
load_dotenv()

app = FastAPI()

# SQLAlchemy setup
DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5433/threads_db"
Base = declarative_base()
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Thread(Base):
    __tablename__ = "threads"
    thread_id = Column(String, primary_key=True, index=True)
    question_asked = Column(Boolean, default=False)
    answered = Column(Boolean, default=False)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class StartThreadResponse(BaseModel):
    thread_id: str
    question_asked: bool
    answered: bool


class ChatRequest(BaseModel):
    question: Optional[str] = None
    config: Optional[dict] = None  # Must contain at least thread_id


class ChatResponse(BaseModel):
    thread_id: str
    answer: Optional[str] = None
    api_response: Optional[str] = None
    status_code: Optional[int] = None


def get_human_workflow():
    return HumanWorkflow()


@app.post("/start_thread", response_model=StartThreadResponse)
def start_thread(db: Session = Depends(get_db)):
    """
    Starts a new conversation and generates a unique thread_id.
    """
    thread_id = str(uuid4())
    new_thread = Thread(thread_id=thread_id, question_asked=False, answered=False)
    db.add(new_thread)
    db.commit()
    db.refresh(new_thread)
    return StartThreadResponse(
        thread_id=thread_id,
        question_asked=new_thread.question_asked,
        answered=new_thread.answered,
    )


@app.post("/ask_question", response_model=ChatResponse)
def ask_question(
    request: ChatRequest,
    human_workflow: HumanWorkflow = Depends(get_human_workflow),
    db: Session = Depends(get_db),
):
    """
    Sends a question within an existing conversation.
    """
    thread_id = request.config.get("thread_id") if request.config else None

    if not thread_id:
        raise HTTPException(status_code=400, detail="Missing thread_id in config.")

    thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()

    if not thread:
        raise HTTPException(status_code=400, detail="Thread ID does not exist.")

    if not request.question:
        raise HTTPException(status_code=400, detail="Missing question.")

    response_state = human_workflow.invoke(
        input={"question": request.question},
        config={"configurable": {"thread_id": thread_id}},
        subgraphs=True,
    )

    if isinstance(response_state, tuple) and len(response_state) == 2:
        response_data = response_state[1]
    else:
        response_data = response_state

    # Update thread to indicate a question has been asked
    thread.question_asked = True
    thread.answered = True
    db.commit()

    return ChatResponse(
        thread_id=thread_id,
        answer=response_data.get("answer"),
        api_response=response_data.get("api_response"),
        status_code=response_data.get("status_code"),
    )


@app.post("/confirm", response_model=ChatResponse)
def confirm(
    request: ChatRequest,
    human_workflow: HumanWorkflow = Depends(get_human_workflow),
    db: Session = Depends(get_db),
):
    """
    Confirms an existing conversation by sending None as the question.
    """
    thread_id = request.config.get("thread_id") if request.config else None

    if not thread_id:
        raise HTTPException(status_code=400, detail="Missing thread_id in config.")

    thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()

    if not thread:
        raise HTTPException(status_code=400, detail="Thread ID does not exist.")

    # Check if a question has been asked in this thread
    if not thread.question_asked:
        raise HTTPException(
            status_code=400,
            detail="No question has been asked in this thread yet.",
        )

    if request.question is not None:
        raise HTTPException(
            status_code=400,
            detail="Confirm endpoint expects question to be None.",
        )

    response_state = human_workflow.invoke(
        input=None,
        config={"configurable": {"thread_id": thread_id}},
        subgraphs=True,
    )

    if isinstance(response_state, tuple) and len(response_state) == 2:
        response_data = response_state[1]
    else:
        response_data = response_state

    return ChatResponse(
        thread_id=thread_id,
        answer=response_data.get("answer"),
        api_response=response_data.get("api_response"),
        status_code=response_data.get("status_code"),
    )


@app.get("/sessions", response_model=List[StartThreadResponse])
def list_sessions(db: Session = Depends(get_db)):
    """
    Returns all existing threads with their statuses.
    """
    threads = db.query(Thread).all()
    return [
        StartThreadResponse(
            thread_id=thread.thread_id,
            question_asked=thread.question_asked,
            answered=thread.answered,
        )
        for thread in threads
    ]


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)

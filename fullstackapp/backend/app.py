from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, create_engine, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy_utils import database_exists, create_database
from contextlib import asynccontextmanager
from workflows.human_workflow import HumanWorkflow
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Database URLs
DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5433/postgres"
TARGET_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5433/threads_db"

# SQLAlchemy Engines
default_engine = create_engine(DEFAULT_DATABASE_URL, future=True)
target_engine = create_engine(TARGET_DATABASE_URL, future=True)

# SQLAlchemy Base and Session
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=target_engine)


class Thread(Base):
    __tablename__ = "threads"
    thread_id = Column(String, primary_key=True, index=True)
    question_asked = Column(Boolean, default=False)
    question = Column(String, nullable=True)  # Stores the question
    answer = Column(Text, nullable=True)  # Stores the answer
    confirmed = Column(Boolean, default=False)  # Indicates if the thread is confirmed
    error = Column(Boolean, default=False)  # Indicates if there was an error


def initialize_database():
    """
    Ensures the threads_db database exists. Creates it if it doesn't.
    """
    if not database_exists(TARGET_DATABASE_URL):
        create_database(url=TARGET_DATABASE_URL)
        print("Database threads_db created.")


def ensure_tables():
    """
    Ensures all tables in the target database are created.
    """
    Base.metadata.create_all(bind=target_engine)


def get_db():
    """
    Dependency to provide database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_human_workflow():
    return HumanWorkflow()


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    ensure_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ThreadResponse(BaseModel):
    thread_id: str
    question_asked: bool
    question: Optional[str] = None
    answer: Optional[str] = None
    confirmed: bool
    error: bool


class StartThreadResponse(BaseModel):
    thread_id: str


class ChatRequest(BaseModel):
    question: Optional[str] = None
    config: Optional[dict] = None  # Must contain at least thread_id


class ChatResponse(BaseModel):
    thread_id: str
    question: Optional[str] = None
    answer: Optional[str] = None
    human_interrupted: bool


class UpdateAnswerRequest(BaseModel):
    answer: str


@app.post("/start_thread", response_model=StartThreadResponse)
def start_thread(db: Session = Depends(get_db)):
    """
    Starts a new conversation and generates a unique thread_id.
    """
    thread_id = str(uuid4())
    new_thread = Thread(
        thread_id=thread_id, question_asked=False, confirmed=False, error=False
    )
    db.add(new_thread)
    db.commit()
    db.refresh(new_thread)
    return StartThreadResponse(thread_id=new_thread.thread_id)


@app.post("/ask_question", response_model=ThreadResponse)
def ask_question(
    request: ChatRequest,
    db: Session = Depends(get_db),
    human_workflow: HumanWorkflow = Depends(get_human_workflow),
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

    if thread.question_asked:
        raise HTTPException(
            status_code=400,
            detail=f"Question has already been asked for thread ID: {thread_id}.",
        )

    if not request.question:
        raise HTTPException(status_code=400, detail="Missing question.")

    response_state = human_workflow.invoke(
        input={"question": request.question},
        # config={"configurable": {"thread_id": thread_id}},
        config={"recursion_limit": 5, "configurable": {"thread_id": thread_id}},
        subgraphs=True,
    )

    # Update thread with the question, answer, and error state
    thread.question_asked = True
    thread.question = request.question
    thread.answer = response_state[1].get("answer")
    thread.error = response_state[1].get("error", False)
    db.commit()

    return ThreadResponse(
        thread_id=thread.thread_id,
        question_asked=thread.question_asked,
        question=thread.question,
        answer=thread.answer,
        confirmed=thread.confirmed,
        error=thread.error,
    )


@app.post("/confirm", response_model=ThreadResponse)
def confirm(
    request: ChatRequest,
    db: Session = Depends(get_db),
    human_workflow: HumanWorkflow = Depends(get_human_workflow),
):
    """
    Confirms an existing conversation by marking it as confirmed.
    """
    thread_id = request.config.get("thread_id") if request.config else None

    if not thread_id:
        raise HTTPException(status_code=400, detail="Missing thread_id in config.")

    thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()

    if not thread:
        raise HTTPException(status_code=400, detail="Thread ID does not exist.")

    if not thread.question_asked:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot confirm thread {thread_id} as no question has been asked.",
        )

    response_state = human_workflow.invoke(
        input=None,
        config={"configurable": {"thread_id": thread_id}},
    )

    # Mark the thread as confirmed and update the answer
    thread.confirmed = bool(response_state.get("confirmed"))
    thread.answer = response_state.get("answer")
    db.commit()

    return ThreadResponse(
        thread_id=thread.thread_id,
        question_asked=thread.question_asked,
        question=thread.question,
        answer=thread.answer,
        confirmed=thread.confirmed,
        error=thread.error,
    )


@app.delete("/delete_thread/{thread_id}", response_model=ThreadResponse)
def delete_thread(
    thread_id: str,
    db: Session = Depends(get_db),
):
    """
    Deletes a specific thread by its thread_id.
    """
    thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()

    if not thread:
        raise HTTPException(status_code=404, detail="Thread ID does not exist.")

    db.delete(thread)
    db.commit()

    return ThreadResponse(
        thread_id=thread.thread_id,
        question_asked=thread.question_asked,
        question=thread.question,
        answer=thread.answer,
        confirmed=thread.confirmed,
        error=thread.error,
    )


@app.get("/sessions", response_model=list[ThreadResponse])
def list_sessions(db: Session = Depends(get_db)):
    """
    Returns all existing threads with their statuses.
    """
    threads = db.query(Thread).all()
    return [
        ThreadResponse(
            thread_id=thread.thread_id,
            question_asked=thread.question_asked,
            question=thread.question,
            answer=thread.answer,
            confirmed=thread.confirmed,
            error=thread.error,
        )
        for thread in threads
    ]


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)

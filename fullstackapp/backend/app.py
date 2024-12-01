from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from contextlib import asynccontextmanager
from workflows.human_workflow import HumanWorkflow
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text

DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://postgres:postgres@postgres_local:5432/postgres"
)
TARGET_DATABASE_URL = (
    "postgresql+psycopg://postgres:postgres@postgres_local:5432/threads_db"
)

default_engine = create_engine(DEFAULT_DATABASE_URL, future=True)
target_engine = create_engine(TARGET_DATABASE_URL, future=True)

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=target_engine)


class Thread(Base):
    __tablename__ = "threads"
    thread_id = Column(String, primary_key=True, index=True)
    question_asked = Column(Boolean, default=False)
    question = Column(String, nullable=True)
    answer = Column(Text, nullable=True)
    confirmed = Column(Boolean, default=False)
    error = Column(Boolean, default=False)


def initialize_database():
    with default_engine.connect() as connection:
        result = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'threads_db'")
        ).fetchone()
        if not result:
            connection.execution_options(isolation_level="AUTOCOMMIT").execute(
                text("CREATE DATABASE threads_db")
            )
            print("Database threads_db created.")


def ensure_tables():
    Base.metadata.create_all(bind=target_engine)


def get_db():
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


class UpdateStateRequest(BaseModel):
    answer: str


@app.post("/start_thread", response_model=StartThreadResponse)
def start_thread(db: Session = Depends(get_db)):
    thread_id = str(uuid4())
    new_thread = Thread(
        thread_id=thread_id, question_asked=False, confirmed=False, error=False
    )
    db.add(new_thread)
    db.commit()
    db.refresh(new_thread)
    return StartThreadResponse(thread_id=new_thread.thread_id)


@app.post("/ask_question/{thread_id}", response_model=ThreadResponse)
def ask_question(
    thread_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db),
    human_workflow: HumanWorkflow = Depends(get_human_workflow),
):
    thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()

    if not thread:
        raise HTTPException(status_code=404, detail="Thread ID does not exist.")

    if thread.question_asked:
        raise HTTPException(
            status_code=400,
            detail=f"Question has already been asked for thread ID: {thread_id}.",
        )

    if not request.question:
        raise HTTPException(status_code=400, detail="Missing question.")

    response_state = human_workflow.invoke(
        input={"question": request.question},
        config={"recursion_limit": 5, "configurable": {"thread_id": thread_id}},
        subgraphs=True,
    )

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


@app.patch("/edit_state/{thread_id}", response_model=ThreadResponse)
def edit_state(
    thread_id: str,
    request: UpdateStateRequest,
    db: Session = Depends(get_db),
    human_workflow: HumanWorkflow = Depends(get_human_workflow),
):
    thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread ID does not exist.")

    if not thread.question_asked:
        raise HTTPException(
            status_code=400, detail="Cannot edit a thread without a question."
        )

    if thread.confirmed:
        raise HTTPException(
            status_code=400, detail="Cannot edit a thread after it has been confirmed."
        )

    human_workflow.workflow.update_state(
        config={"configurable": {"thread_id": thread_id}},
        values={"answer": request.answer},
    )
    thread.answer = request.answer
    db.commit()

    return ThreadResponse(
        thread_id=thread.thread_id,
        question_asked=thread.question_asked,
        question=thread.question,
        answer=thread.answer,
        confirmed=thread.confirmed,
        error=thread.error,
    )


@app.post("/confirm/{thread_id}", response_model=ThreadResponse)
def confirm(
    thread_id: str,
    db: Session = Depends(get_db),
    human_workflow: HumanWorkflow = Depends(get_human_workflow),
):
    thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()

    if not thread:
        raise HTTPException(status_code=404, detail="Thread ID does not exist.")

    if not thread.question_asked:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot confirm thread {thread_id} as no question has been asked.",
        )

    response_state = human_workflow.invoke(
        input=None,
        config={"configurable": {"thread_id": thread_id}},
    )

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

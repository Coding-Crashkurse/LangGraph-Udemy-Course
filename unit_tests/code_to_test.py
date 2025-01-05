from typing import TypedDict

from dotenv import load_dotenv
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

embedding_function = OpenAIEmbeddings()

docs = [
    Document(
        page_content="Bella Vista is owned by Antonio Rossi, a renowned chef with over 20 years of experience in the culinary industry. He started Bella Vista to bring authentic Italian flavors to the community.",
        metadata={"source": "owner.txt"},
    ),
    Document(
        page_content="Bella Vista offers a range of dishes with prices that cater to various budgets. Appetizers start at $8, main courses range from $15 to $35, and desserts are priced between $6 and $12.",
        metadata={"source": "dishes.txt"},
    ),
    Document(
        page_content="Bella Vista is open from Monday to Sunday. Weekday hours are 11:00 AM to 10:00 PM, while weekend hours are extended from 11:00 AM to 11:00 PM.",
        metadata={"source": "restaurant_info.txt"},
    ),
    Document(
        page_content="Bella Vista offers a variety of menus including a lunch menu, dinner menu, and a special weekend brunch menu. The lunch menu features light Italian fare, the dinner menu offers a more extensive selection of traditional and contemporary dishes, and the brunch menu includes both classic breakfast items and Italian specialties.",
        metadata={"source": "restaurant_info.txt"},
    ),
]

db = Chroma.from_documents(docs, embedding_function)


@tool
def get_weather(location: str):
    """Determines weather of a given city"""
    if location.lower() in ["munich"]:
        return "It's 15 degrees Celsius and cloudy."
    else:
        return "It's 32 degrees Celsius and sunny."


def create_llm(model_name: str = "gpt-4o-mini") -> ChatOpenAI:
    tools = [get_weather]
    model = ChatOpenAI(model=model_name)
    model = model.bind_tools(tools)
    return model


def create_chat_prompt_template(context: str, question: str) -> ChatPromptTemplate:
    template = """Answer the question based only on the following context:
    {context}
    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)
    return prompt


def create_retriever(db, k: int = 2):
    return db.as_retriever(search_kwargs={"k": k})


class AgentState(TypedDict):
    question: str
    messages: list[BaseMessage]
    prompt: str
    context: list[Document]
    answer: str
    on_topic: str


async def llm_node(state: AgentState) -> AgentState:
    print("State in llm node:", state)
    llm = create_llm()

    messages = state.get("messages", [])
    messages.append(state["prompt"])

    response = await llm.ainvoke(state["prompt"].messages)

    messages.append(AIMessage(content=response.content))
    new_state = state.copy()
    new_state["messages"] = messages
    new_state["answer"] = response.content
    return new_state


async def prompt_node(state: AgentState) -> AgentState:
    print("State in prompt node:", state)
    question = state["question"]
    context = state["context"]
    formatted_context = [doc.page_content for doc in context]

    prompt = create_chat_prompt_template(context, question)

    prompt_result = await prompt.ainvoke(
        {"question": question, "context": formatted_context}
    )
    new_state = state.copy()
    new_state["prompt"] = prompt_result
    return new_state


async def retrieve_node(state: AgentState) -> AgentState:
    print("State in retrieval node:", state)
    retriever = create_retriever(db, k=2)

    context = await retriever.ainvoke(state["question"])
    new_state = state.copy()
    new_state["context"] = context
    return new_state

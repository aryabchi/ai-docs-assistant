from ollama import AsyncClient
import httpx
from fastapi import FastAPI, Body
from contextlib import asynccontextmanager
from qdrant_client import AsyncQdrantClient
from sentence_transformers import SentenceTransformer
from qdrant_client.models import VectorParams, Distance, PointStruct

from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from typing import Annotated, TypedDict
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver

from settings import settings
from utils import load_documents_from_fs
from schemas import GenerateTaskRequest
from logger import logger

# Инициализация моделей и клиентов (один раз при старте)
embedding_model = SentenceTransformer(settings.embedding_model)
qdrant = AsyncQdrantClient(settings.qdrant_host, port=settings.qdrant_port)
ollama = AsyncClient(host=settings.ollama_host)


# Инициализация объектов langgraph
# === Состояние ===
class State(TypedDict):
    messages: Annotated[list, add_messages]
    task_id: str


# === Инструменты ===
@tool
def create_task(config: RunnableConfig) -> str:
    """Создаёт задачу и возвращает её TASK_ID."""
    user_id = "UNKNOWN"
    if "configurable" in config and "thread_id" in config["configurable"]:
        user_id = config["configurable"]["thread_id"]
    logger.debug(f"Tool 'create_task' for user_id={user_id}")
    if "123" in user_id:
        return f"TASK-123_{user_id}"  # fake task id
    elif "456" in user_id:
        return f"TASK-456_{user_id}"  # fake task id
    else:
        return f"UNKNOWN_{user_id}"  # fake task id


@tool
def add_comment(task_id: str, comment: str, config: RunnableConfig) -> str:
    """Добавляет комментарий к задаче по TASK_ID."""
    user_id = "UNKNOWN"
    if "configurable" in config and "thread_id" in config["configurable"]:
        user_id = config["configurable"]["thread_id"]
    logger.debug(
        f"Tool 'add_comment' was called with task_id={task_id} for user_id={user_id}"
    )
    return f'Комментарий "{comment}" успешно добавлен к задаче с TASK_ID {task_id}.'


tools = [create_task, add_comment]
tool_node = ToolNode(tools)


# === LLM ===
llm = ChatOllama(model="gpt-oss:20b-cloud", temperature=0.0)  # settings.llm_model
llm_with_tools = llm.bind_tools(tools)


# === Узел агента ===
def call_model(state: State, config: RunnableConfig):
    system = SystemMessage(
        content="Ты — агент управления задачами."
        f"Текущий task_id: {state['task_id'] or 'не задан'}. "
        # "Если задача не создана - вызови только create_task. Не выдумывай ID."
        # "Если задача создана - вызови только add_comment."
        # "Если текущий task_id равен 'не задан' - вызови только create_task. Не выдумывай ID. Верни текущий task_id."
        # "Иначе - вызови только add_comment и верни описание задачи с ID и добавленным комментарием."
        # "Если текущий task_id равен 'не задан' - вызови только create_task. Не выдумывай TASK_ID. Верни текущий task_id."
        # "Иначе - вызови только add_comment и верни описание задачи с TASK_ID и добавленным комментарием."
        "Если нужно создать задачу - вызови только create_task, ничего больше. Не выдумывай её TASK_ID."
        "Если нужно добавить комментарий к задаче TASK_ID - вызови только add_comment."
        # "Всегда выбирай только один инструмент из доступных."
        "Верни TASK_ID задачи и все что ты знаешь по ней."
    )
    user_id = "UNKNOWN"
    if "configurable" in config and "thread_id" in config["configurable"]:
        user_id = config["configurable"]["thread_id"]
    logger.debug(
        f"'call_model' was called with task_id={state['task_id']} for user_id={user_id}"
    )
    messages = [system] + state["messages"]
    return {"messages": [llm_with_tools.invoke(messages)]}


# === Узел обновления состояния ===
def update_task_id(state: State):
    for msg in reversed(state["messages"]):
        if isinstance(msg, ToolMessage) and msg.name == "create_task":
            # сохраняет task_id в state
            return {
                "task_id": msg.content,
            }
    return {
        "task_id": state["task_id"],
    }


# === Сборка графа ===
workflow = StateGraph(State)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_node("update_task_id", update_task_id)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent", lambda state: "tools" if state["messages"][-1].tool_calls else "__end__"
)
workflow.add_edge("tools", "update_task_id")
workflow.add_edge("update_task_id", "agent")  # results in tool calls cycling sometimes
# workflow.add_edge("update_task_id", "__end__")

memory = MemorySaver()

# === компиляция workflow агента с сохраняемыми в памяти состояниями ===
graph = workflow.compile(checkpointer=memory)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при запуске и очистка при завершении"""
    global embedding_model, qdrant

    # --- Startup ---
    if await qdrant.collection_exists(settings.collection_name):
        await qdrant.delete_collection(settings.collection_name)

    await qdrant.create_collection(
        collection_name=settings.collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    docs = load_documents_from_fs()
    embeddings = embedding_model.encode([doc.page_content for doc in docs])
    points = [
        PointStruct(
            id=i,
            vector=emb.tolist(),
            payload={"text": doc.page_content, "source": doc.metadata["source"]},
        )
        for i, (doc, emb) in enumerate(zip(docs, embeddings))
    ]

    await qdrant.upsert(settings.collection_name, points)
    logger.info(f"Коллекция '{settings.collection_name}' создана и заполнена.")

    yield  # <-- запуск приложения

    # --- Shutdown (опционально) ---
    # Например, закрытие соединений
    await qdrant.delete_collection(settings.collection_name)
    await qdrant.close()


# Старт REST сервиса
app = FastAPI(title="LangGraph Service", lifespan=lifespan)


@app.post("/generate")
async def generate(request: GenerateTaskRequest):
    # получаем state текущего user_id
    config = {"configurable": {"thread_id": request.user_id}}
    current_user_state = graph.get_state(config)
    current_task_id = current_user_state.values.get("task_id", "")
    logger.debug(f"Current task_id={current_task_id}")
    state = {
        "messages": current_user_state.values.get("messages"),
        "task_id": current_task_id,
    }

    # вызываем агента для создания задачи или комментария
    logger.debug("---- Шаг агента ----")
    state = graph.invoke(
        {
            **state,
            "messages": [HumanMessage(content=request.query)],
        },
        config=config,
    )
    logger.debug(f"Состояние после шага: task_id={state['task_id']}")
    logger.debug(f"История сообщений после шага: messages={state['messages']}")

    # возвращаем финальный ответ
    last_msg = state["messages"][-1]

    logger.debug("---- Ответ агента ----")
    logger.debug(last_msg.content)
    return {"answer": last_msg.content}


@app.post("/ask")
async def ask(question: str = Body(..., embed=True)):
    """
    RAG-эндпоинт: получает вопрос => возвращает ответ от LLM в контексте наденного документа.
    """
    # 1. Эмбеддинг запроса
    query_vector = embedding_model.encode(question).tolist()

    # 2. Поиск в Qdrant (асинхронно)
    search_result = await qdrant.query_points(
        collection_name=settings.collection_name, query=query_vector, limit=1
    )
    logger.info(
        f"Из {settings.collection_name} получен контекст из {len(search_result.points)} документов"
    )
    context = ""
    doc_sources = []
    for point in search_result.points:
        context += point.payload["text"] + "\n"
        doc_sources.append(point.payload["source"])
    logger.debug(f"В контекст попали документы из источников: {doc_sources}")

    # 3. Генерация ответа через Ollama (асинхронно)
    prompt = f"""
    Отвечай только на основе контекста, не выдумывай ответ, не используй собственные знания, не дополняй контекст. Если не знаешь — скажи "Не знаю".
    Контекст: {context}
    Вопрос: {question}
    """
    response = await ollama.chat(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.01},
    )
    return {"answer": response.message.content}


@app.get("/health")
async def health():
    """
    Healthcheck — эндпоинт для проверки работоспособности сервиса.
    Используется оркестраторами (например, Kubernetes) для перезапуска
    недоступных компонентов.
    """
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            # Проверяем, отвечает ли Ollama на базовый запрос
            await client.get(settings.ollama_host)
        return {"status": "healthy"}
    except Exception as e:
        logger.error("healthcheck_failed", error=str(e))
        return {"status": "unhealthy"}


# запуск
# uvicorn main:app --port=8080

from pathlib import Path
from qdrant_client import QdrantClient
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client.models import VectorParams, Distance

from app.logger import logger
from app.settings import settings


# Конфигурация векторного хранилища
collection_name = settings.QDRANT_COLLECTION_NAME
embedding_model_name = settings.EMBEDDING_MODEL_NAME
vector_size = settings.VECTOR_SIZE

# Инициализация клиента Qdrant и создание коллекции
client = QdrantClient(settings.QDRANT_HOST, port=settings.QDRANT_PORT)

if client.collection_exists(collection_name):
    client.delete_collection(collection_name)

client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
)

# Инициализация embedding-модели через Ollama
embeddings = OllamaEmbeddings(model=embedding_model_name)

# Векторное хранилище LangChain
vector_store = QdrantVectorStore(
    client=client,
    collection_name=collection_name,
    embedding=embeddings,
    distance=Distance.COSINE,
)


def initialize_rag_from_docs() -> None:
    """Загружает все .md-файлы из директории docs/ в векторную базу при старте сервиса."""
    docs_dir = Path("docs")
    if not docs_dir.exists():
        logger.warning("Директория docs/ не найдена")
        return

    documents = []
    for file_path in docs_dir.glob("*.md"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    documents.append(
                        Document(
                            page_content=content, metadata={"source": str(file_path)}
                        )
                    )
        except Exception as exc:
            logger.error(f"Ошибка чтения файла {file_path}: {exc}")

    if documents:
        vector_store.add_documents(documents)
        logger.info(f"Загружено {len(documents)} документов в RAG-хранилище")
    else:
        logger.warning("В директории docs/ не найдено .md-файлов")


if __name__ == "__main__":
    initialize_rag_from_docs()

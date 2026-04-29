from pathlib import Path
from langchain_core.documents import Document
from logger import logger


def load_documents_from_fs() -> list[Document] | None:
    """Загружает все .md-файлы из директории docs/ в векторную базу при старте сервиса."""
    docs_dir = Path("docs")
    if not docs_dir.exists():
        logger.warning("Директория docs/ не найдена")
        return None

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
        logger.debug(f"Из директории docs/ прочитано {len(documents)} документов")
        return documents

    else:
        logger.warning("В директории docs/ не найдено .md-файлов")
        return None

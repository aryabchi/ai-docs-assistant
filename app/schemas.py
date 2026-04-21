from pydantic import BaseModel


class SearchRequest(BaseModel):
    """
    Вход: JSON с полем query (например, "создай эндпоинт для получения активных задач")
    """

    query: str


class SearchResponse(BaseModel):
    """
    Выход:
    {
      "found": true,
      "content": "#### Метод /api/v1/joke\n\n**Описание**: Возвращает случайную шутку...",
    }
    или
    {
      "found": false,
      "message": "Ошибка генерации: ..."
    }
    """

    found: bool
    content: str | None = None
    message: str | None = None


class GenerateRequest(BaseModel):
    """
    Вход: JSON с полем query (например, "создай эндпоинт для получения активных задач")
    """

    query: str


class GenerateResponse(BaseModel):
    """
    Выход:
    {
      "success": true,
      "message": "Документ успешно создан и сохранён.",
      "content": "#### Метод /api/v1/joke\n\n**Описание**: Возвращает случайную шутку...",
      "file_path": "docs/api.md"
    }
    или
    {
      "success": false,
      "message": "Ошибка генерации: ..."
    }
    """

    success: bool
    message: str
    content: str | None = None
    file_path: str | None = None

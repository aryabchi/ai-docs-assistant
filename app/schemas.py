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

    found: bool
    content: str | None = None
    message: str | None = None

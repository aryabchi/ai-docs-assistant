from pydantic import BaseModel


class GenerateTaskRequest(BaseModel):
    """
    JSON для генерации задач и комментариев
    """

    user_id: str
    query: str

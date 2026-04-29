from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    qdrant_host: str
    qdrant_port: int
    ollama_host: str
    embedding_model: str
    llm_model: str
    collection_name: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# ai-docs-assistant
AI agentic mini-project with RAG

## Features
- two agents (generator and validator)
- fine-tuned LoRA adapter
- RAG search/update
- health-check
- pydantic validation
- local logging
- endpoints autotests
- containerazed


## Stack
- LLM: Mistral-7B-Instruct-v0.3 + LoRA adapter
- Multi-agent: CrewAI
- Vectore DB: Qdrant
- Backend: FastAPI
- Infrastructure: Docker


## Endpoints
* POST /generate
* POST /search
* GET /health

## Swagger query samples
1. **http://127.0.0.1:8080/generate**

```
{
  "query": "Удаляет пользователя по его идентификатору"
}
``` 
Expected response

```
{
  "success": true,
  "message": "Документ успешно создан и сохранён.",
  "content": "### DELETE /api/v1/users/{userId}\n\n**Описание**: Удаляет пользователя по его идентификатору.\n\n**Параметры пути**:\n- `userId` (integer): уникальный идентификатор пользователя\n\n**Ответ**:\n```json\n{\"message\": \"User deleted\"}\n```",
  "file_path": "docs\\delete_user_1.md"
}
```

1. **http://127.0.0.1:8080/search**

```
{
  "query": "Как удалить пользователя по его идентификатору"
}
```
Expected response

```
{
  "found": true,
  "content": "### DELETE /api/v1/users/{id}\n\n**Описание**: Удаляет пользователя по его идентификатору.\n\n**Параметры пути**:\n- `id` (integer): уникальный идентификатор пользователя\n\n**Ответ**:\n```json\n{\"message\": \"User deleted\"}\n```",
  "message": null
}
```

1. **http://127.0.0.1:8080/health**
Expected response

```
{
  "status": "healthy",
  "checks": {
    "qdrant": true,
    "ollama": true,
    "docs": true,
    "rag_canary": true
  }
}
```
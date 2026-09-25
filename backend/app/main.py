from fastapi import FastAPI

from app.api.users import router as users_router
from app.api.incidents import router as incidents_router
from app.api.tickets import router as tickets_router
from app.api.chat import router as chat_router


app = FastAPI(title="OpsAI")


app.include_router(users_router)
app.include_router(incidents_router)
app.include_router(tickets_router)
app.include_router(chat_router)


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "opsai"
    }
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import chat, conversations, logs, folders

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="LLM Inference Logger", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(conversations.router, prefix="/api", tags=["conversations"])
app.include_router(logs.router, prefix="/api", tags=["logs"])
app.include_router(folders.router, prefix="/api", tags=["folders"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

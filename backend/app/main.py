from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.seed import seed_incidents
from app.db.session import create_tables
from app.routers import chat, incidents, rca


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    await seed_incidents()
    yield


app = FastAPI(title="Incident Copilot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(rca.router, prefix="/api")
app.include_router(incidents.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}

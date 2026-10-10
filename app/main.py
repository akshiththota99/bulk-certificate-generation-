# FastAPI application entry point
from fastapi import FastAPI

from app.database import Base, engine
from app.routes.certificates import router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bulk Certificate Generator")
app.include_router(router)
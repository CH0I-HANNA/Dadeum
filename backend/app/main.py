from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyze, report, thumbnail, upload

app = FastAPI(title="다듬 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
app.include_router(thumbnail.router, prefix="/api")
app.include_router(report.router, prefix="/api")

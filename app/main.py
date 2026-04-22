from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import book_routes, auth_routes
from app.db.session import engine, Base
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(book_routes.router)
app.include_router(auth_routes.router)
"""
FastAPI приложение: Учебная платформа по основам тестирования программного обеспечения
Улучшенная версия с модульной архитектурой, SQLAlchemy и безопасной аутентификацией
"""

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

# Импорт роутеров
from app.routers import auth, categories, topics, quizzes, glossary, feedback, progress, gamification, social
from app.db.database import engine, Base
from app.db import models  # Импортируем модели для регистрации в Alembic
from app.services import seed_initial_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler для инициализации БД при запуске."""
    # Создание таблиц при старте (для совместимости)
    Base.metadata.create_all(bind=engine)
    # Заполнение начальными данными
    seed_initial_data()
    yield
    # Очистка при завершении (если нужно)


app = FastAPI(
    title="TestLearn — Основы тестирования ПО",
    description="Учебная платформа по основам тестирования программного обеспечения",
    version="2.0.0",
    lifespan=lifespan
)

# Статика и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Подключение роутеров
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])
app.include_router(topics.router, prefix="/api/topics", tags=["Topics"])
app.include_router(quizzes.router, prefix="/api/quizzes", tags=["Quizzes"])
app.include_router(glossary.router, prefix="/api/glossary", tags=["Glossary"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(progress.router, prefix="/api/progress", tags=["Progress"])
app.include_router(gamification.router, prefix="/api/gamification", tags=["Gamification"])
app.include_router(social.router, prefix="/api/social", tags=["Social"])


@app.get("/", include_in_schema=False)
async def home(request: Request):
    """Главная страница."""
    from sqlalchemy.orm import Session
    from app.db.database import get_db
    from app.db.models import Category, Topic, Question, GlossaryTerm
    
    # Получаем статистику
    db = next(get_db())
    try:
        stats = {
            "categories": db.query(Category).count(),
            "topics": db.query(Topic).count(),
            "questions": db.query(Question).count(),
            "glossary": db.query(GlossaryTerm).count()
        }
    finally:
        db.close()
    
    return templates.TemplateResponse("index.html", {"request": request, "stats": stats})

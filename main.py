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


# Frontend pages
@app.get("/theory", include_in_schema=False)
async def theory_page(request: Request):
    """Теория раздел."""
    from sqlalchemy.orm import Session
    from app.db.database import get_db
    from app.db.models import Category, Topic
    
    db: Session = next(get_db())
    try:
        # Get all categories
        categories = db.query(Category).order_by(Category.order_num, Category.title).all()
        
        # Get all topics
        topics = db.query(Topic).order_by(Topic.order_num, Topic.title).all()
        
        # Organize topics by category
        topics_by_category = {}
        for topic in topics:
            if topic.category_id not in topics_by_category:
                topics_by_category[topic.category_id] = []
            topics_by_category[topic.category_id].append(topic)
        
        # Get all topic titles for datalist
        all_topic_titles = [topic.title for topic in topics]
        
        # For now, assume no topics read (would be user-specific in real app)
        topics_read = 0
        total_topics = len(topics)
        
        # Get query parameters
        query_params = dict(request.query_params)
        active_category_id = int(query_params.get("category_id", 0)) if query_params.get("category_id") else None
        search_query = query_params.get("search", "")
        
        return templates.TemplateResponse("theory.html", {
            "request": request,
            "categories": categories,
            "topics_by_category": topics_by_category,
            "all_topic_titles": all_topic_titles,
            "topics_read": topics_read,
            "total_topics": total_topics,
            "active_category_id": active_category_id,
            "search_query": search_query
        })
    finally:
        db.close()


@app.get("/quiz", include_in_schema=False)
async def quiz_page(request: Request):
    """Тесты раздел."""
    return templates.TemplateResponse("quiz.html", {"request": request})


@app.get("/glossary", include_in_schema=False)
async def glossary_page(request: Request):
    """Глоссарий раздел."""
    return templates.TemplateResponse("glossary.html", {"request": request})


@app.get("/bookmarks", include_in_schema=False)
async def bookmarks_page(request: Request):
    """Закладки раздел."""
    return templates.TemplateResponse("bookmarks.html", {"request": request})


@app.get("/stats", include_in_schema=False)
async def stats_page(request: Request):
    """Статистика раздел."""
    return templates.TemplateResponse("stats.html", {"request": request})


@app.get("/database", include_in_schema=False)
async def database_page(request: Request):
    """База данных раздел."""
    return templates.TemplateResponse("database.html", {"request": request})


@app.get("/about", include_in_schema=False)
async def about_page(request: Request):
    """О проекте раздел."""
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/feedback", include_in_schema=False)
async def feedback_page(request: Request):
    """Обратная связь раздел."""
    return templates.TemplateResponse("feedback.html", {"request": request})


@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    """Страница входа."""
    return templates.TemplateResponse("login.html", {"request": request})


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

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
from app.services import seed_initial_data, LeaderboardService


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
app.include_router(gamification.router, prefix="/api", tags=["Gamification"])
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
        # Get all categories (ordered by name)
        categories = db.query(Category).order_by(Category.name).all()

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
    from sqlalchemy.orm import Session
    from app.db.database import get_db
    from app.db.models import Quiz, Question

    db: Session = next(get_db())
    try:
        # Get the first quiz available (or create a default one if none)
        quiz = db.query(Quiz).first()
        if not quiz:
            # If no quiz exists, we'll create a placeholder for demonstration
            # In a real app, you might redirect to a create quiz page or show a message
            quiz = Quiz(id=0, title="Доступные тесты", description="Пока нет доступных тестов")
            questions = []
        else:
            # Get questions for this quiz
            questions = db.query(Question).filter(Question.quiz_id == quiz.id).order_by(Question.order_num).all()
            # Convert to list of dicts for template
            questions = [{
                "id": q.id,
                "question_text": q.question_text,
                "option_a": q.option_a,
                "option_b": q.option_b,
                "option_c": q.option_c,
                "option_d": q.option_d
            } for q in questions]

        # Set a default time limit (15 minutes in seconds)
        time_limit = 900

        return templates.TemplateResponse("quiz.html", {
            "request": request,
            "quiz": quiz,
            "questions": questions,
            "time_limit": time_limit
        })
    finally:
        db.close()


@app.get("/glossary", include_in_schema=False)
async def glossary_page(request: Request):
    """Глоссарий раздел."""
    from sqlalchemy.orm import Session
    from app.db.database import get_db
    from app.db.models import GlossaryTerm

    db: Session = next(get_db())
    try:
        # Get query parameters
        query_params = dict(request.query_params)
        active_letter = query_params.get("letter", "")
        search_query = query_params.get("search", "")

        # Build query
        query = db.query(GlossaryTerm)

        # Filter by letter if provided
        if active_letter:
            query = query.filter(GlossaryTerm.letter == active_letter.upper())

        # Filter by search query if provided
        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(
                (GlossaryTerm.term.ilike(search_term)) |
                (GlossaryTerm.definition.ilike(search_term))
            )

        # Get terms
        terms = query.order_by(GlossaryTerm.term).all()

        # Get all distinct letters for navigation
        all_letters = [chr(i) for i in range(ord('A'), ord('Z')+1)]

        return templates.TemplateResponse("glossary.html", {
            "request": request,
            "terms": terms,
            "all_letters": all_letters,
            "active_letter": active_letter,
            "search_query": search_query
        })
    finally:
        db.close()


@app.get("/stats", include_in_schema=False)
async def stats_page(request: Request):
    """Статистика раздел."""
    from sqlalchemy.orm import Session
    from app.db.database import get_db
    from app.db.models import UserProgress, Topic, Category, QuizResult, Quiz
    from sqlalchemy import func

    db: Session = next(get_db())
    try:
        # Get or create user progress (using a default session for simplicity)
        session_id = 'default_session'
        progress = db.query(UserProgress).filter(UserProgress.session_id == session_id).first()
        if progress is None:
            # Create a temporary progress object with zeros
            class Progress:
                topics_read = 0
                quizzes_passed = 0
                total_score = 0
            progress = Progress()

        # Get total topics
        total_topics = db.query(Topic).count()

        # Get categories with topic count
        categories_with_stats = db.query(Category, func.count(Topic.id).label('topic_count'))\
            .outerjoin(Topic, Category.id == Topic.category_id)\
            .group_by(Category.id)\
            .all()
        # Convert to list of objects with name and topic_count attributes
        categories_with_stats = [{'name': cat.Category.name, 'topic_count': cat.topic_count} for cat in categories_with_stats]

        # Get total quiz results
        total_results = db.query(QuizResult).count()

        # Get average score percentage
        avg_score_result = db.query(func.avg(QuizResult.score * 100.0 / QuizResult.total)).scalar()
        avg_score = round(avg_score_result) if avg_score_result is not None else 0

        # Get total quizzes
        total_quizzes = db.query(Quiz).count()

        # Get score distribution (ranges: 0-49, 50-69, 70-89, 90-100)
        score_distribution = []
        ranges = [(0, 49), (50, 69), (70, 89), (90, 100)]
        for min_score, max_score in ranges:
            count = db.query(QuizResult).filter(
                (QuizResult.score * 100.0 / QuizResult.total) >= min_score,
                (QuizResult.score * 100.0 / QuizResult.total) <= max_score
            ).count()
            score_distribution.append({
                'range_label': f'{min_score}-{max_score}%',
                'count': count
            })

        # Get top results (top 5 by score percentage)
        top_results_query = db.query(QuizResult, Quiz.title.label('quiz_title'))\
            .join(Quiz, QuizResult.quiz_id == Quiz.id)\
            .order_by((QuizResult.score * 100.0 / QuizResult.total).desc())\
            .limit(5)\
            .all()
        top_results = []
        for result, quiz_title in top_results_query:
            percentage = int((result.score / result.total * 100)) if result.total > 0 else 0
            top_results.append({
                'quiz_title': quiz_title,
                'score': result.score,
                'total': result.total,
                'created_at': result.created_at.strftime('%Y-%m-%d') if result.created_at else '',
                'percentage': percentage
            })

        return templates.TemplateResponse("stats.html", {
            "request": request,
            "progress": progress,
            "total_topics": total_topics,
            "categories_with_stats": categories_with_stats,
            "total_results": total_results,
            "avg_score": avg_score,
            "total_quizzes": total_quizzes,
            "score_distribution": score_distribution,
            "top_results": top_results
        })
    finally:
        db.close()


@app.get("/bookmarks", include_in_schema=False)
async def bookmarks_page(request: Request):
    """Закладки раздел."""
    return templates.TemplateResponse("bookmarks.html", {"request": request})


@app.get("/database", include_in_schema=False)
async def database_page(request: Request):
    """База данных раздел."""
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    from app.db.database import get_db

    db: Session = next(get_db())
    try:
        # Get list of tables (excluding SQLite system tables)
        tables_query = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"))
        table_names = [row[0] for row in tables_query.fetchall()]

        tables_info = []
        for table_name in table_names:
            # Get row count
            count_query = db.execute(text(f'SELECT COUNT(*) as count FROM "{table_name}";'))
            count = count_query.scalar() or 0

            # Get column info using PRAGMA
            pragma_query = db.execute(text(f'PRAGMA table_info("{table_name}");'))
            columns = []
            for col in pragma_query.fetchall():
                # col: (cid, name, type, notnull, dflt_value, pk)
                columns.append({
                    'name': col[1],
                    'type': col[2],
                    'pk': bool(col[5]),
                    'notnull': bool(col[3])
                })
            tables_info.append({
                'name': table_name,
                'count': count,
                'columns': columns
            })

        return templates.TemplateResponse("database.html", {
            "request": request,
            "tables_info": tables_info
        })
    finally:
        db.close()


@app.get("/leaderboard", include_in_schema=False)
async def leaderboard_page(request: Request):
    """Таблица лидеров раздел."""
    # Get leaderboard data from service
    leaderboard_data = LeaderboardService.get_leaderboard(limit=10)
    return templates.TemplateResponse("leaderboard.html", {
        "request": request,
        "leaderboard": leaderboard_data
    })


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

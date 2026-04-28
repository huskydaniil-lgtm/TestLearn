"""
Сервисный слой для бизнес-логики образовательной платформы
"""
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.models import (
    Category, Topic, Quiz, Question, QuizResult,
    GlossaryTerm, Feedback, UserProgress, Achievement,
    DailyChallenge, SearchResults, CategoryStats,
    LeaderboardEntry, Certificate, Comment, Notification
)


def get_db_connection(db_name: str = "testlearn.db"):
    """Создать подключение к БД."""
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


class ProgressService:
    """Сервис для управления прогрессом пользователя и геймификацией."""
    
    @staticmethod
    def calculate_level(experience: int) -> tuple:
        """Рассчитать уровень и опыт на основе общего опыта."""
        level = 1
        xp_required = 100
        total_xps = experience
        
        while total_xps >= xp_required:
            total_xps -= xp_required
            level += 1
            xp_required = int(xp_required * 1.5)
        
        return level, total_xps, xp_required
    
    @staticmethod
    def add_experience(session_id: str, amount: int, db_name: str = "testlearn.db"):
        """Добавить опыт пользователю."""
        conn = get_db_connection(db_name)
        try:
            cursor = conn.cursor()
            
            # Получить текущий прогресс
            cursor.execute(
                "SELECT id, total_score FROM user_progress WHERE session_id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            
            if row:
                new_total = row["total_score"] + amount
                cursor.execute(
                    "UPDATE user_progress SET total_score = ?, last_visit = ? WHERE session_id = ?",
                    (new_total, datetime.now().isoformat(), session_id)
                )
            else:
                user_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO user_progress (id, session_id, topics_read, quizzes_passed, total_score, last_visit) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, session_id, 0, 0, amount, datetime.now().isoformat())
                )
            
            conn.commit()
        finally:
            conn.close()
    
    @staticmethod
    def get_achievements(session_id: str, db_name: str = "testlearn.db") -> List[Achievement]:
        """Получить список достижений пользователя."""
        conn = get_db_connection(db_name)
        try:
            cursor = conn.cursor()
            
            # Получить статистику пользователя
            cursor.execute(
                "SELECT topics_read, quizzes_passed, total_score FROM user_progress WHERE session_id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return []
            
            topics_read = row["topics_read"]
            quizzes_passed = row["quizzes_passed"]
            total_score = row["total_score"]
            
            achievements = [
                Achievement(
                    id=1,
                    name="Первые шаги",
                    description="Прочитать первую тему",
                    icon="📚",
                    unlocked=topics_read >= 1
                ),
                Achievement(
                    id=2,
                    name="Любопытный",
                    description="Прочитать 5 тем",
                    icon="🔍",
                    unlocked=topics_read >= 5
                ),
                Achievement(
                    id=3,
                    name="Эрудит",
                    description="Прочитать 10 тем",
                    icon="🎓",
                    unlocked=topics_read >= 10
                ),
                Achievement(
                    id=4,
                    name="Новичок в тестировании",
                    description="Пройти первый тест",
                    icon="✅",
                    unlocked=quizzes_passed >= 1
                ),
                Achievement(
                    id=5,
                    name="Опытный тестировщик",
                    description="Пройти 5 тестов",
                    icon="🏆",
                    unlocked=quizzes_passed >= 5
                ),
                Achievement(
                    id=6,
                    name="Мастер тестирования",
                    description="Набрать 100+ баллов в тестах",
                    icon="👑",
                    unlocked=total_score >= 100
                ),
            ]
            
            return achievements
        finally:
            conn.close()
    
    @staticmethod
    def get_daily_challenge(db_name: str = "testlearn.db") -> Optional[DailyChallenge]:
        """Получить ежедневное испытание."""
        conn = get_db_connection(db_name)
        try:
            cursor = conn.cursor()
            
            # Выбрать случайный тест для ежедневного испытания
            cursor.execute("""
                SELECT q.id, q.title, q.description 
                FROM quizzes q 
                ORDER BY RANDOM() 
                LIMIT 1
            """)
            row = cursor.fetchone()
            
            if not row:
                return None
            
            expires = datetime.now().replace(hour=23, minute=59, second=59)
            
            return DailyChallenge(
                id=1,
                quiz_id=row["id"],
                title="Ежедневный вызов",
                description=f"Пройдите тест: {row['title']} и получите 50 XP!",
                bonus_xp=50,
                completed=False,
                expires_at=expires.isoformat()
            )
        finally:
            conn.close()
    
    @staticmethod
    def get_category_stats(session_id: str, db_name: str = "testlearn.db") -> List[CategoryStats]:
        """Получить статистику по категориям."""
        conn = get_db_connection(db_name)
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    c.id as category_id,
                    c.name as category_name,
                    COUNT(DISTINCT t.id) as total_topics,
                    COUNT(DISTINCT rt.topic_id) as read_topics,
                    COUNT(DISTINCT q.id) as total_quizzes,
                    COUNT(DISTINCT qr.id) as passed_quizzes,
                    COALESCE(AVG(CAST(qr.score AS FLOAT) / qr.total * 100), 0) as average_score
                FROM categories c
                LEFT JOIN topics t ON c.id = t.category_id
                LEFT JOIN read_topics rt ON t.id = rt.topic_id AND rt.session_id = ?
                LEFT JOIN quizzes q ON c.id = q.category_id
                LEFT JOIN quiz_results qr ON q.id = qr.quiz_id
                GROUP BY c.id, c.name
            """, (session_id,))
            
            stats = []
            for row in cursor.fetchall():
                completion = 0.0
                if row["total_topics"] > 0:
                    completion = (row["read_topics"] / row["total_topics"]) * 100
                
                stats.append(CategoryStats(
                    category_id=row["category_id"],
                    category_name=row["category_name"],
                    total_topics=row["total_topics"],
                    read_topics=row["read_topics"],
                    total_quizzes=row["total_quizzes"],
                    passed_quizzes=row["passed_quizzes"],
                    average_score=row["average_score"] or 0.0,
                    completion_percentage=completion
                ))
            
            return stats
        finally:
            conn.close()


class SearchService:
    """Сервис для поиска по материалам."""
    
    @staticmethod
    def search(query: str, db_name: str = "testlearn.db") -> SearchResults:
        """Поиск по темам и глоссарию."""
        conn = get_db_connection(db_name)
        try:
            cursor = conn.cursor()
            search_term = f"%{query}%"
            
            # Поиск по темам
            cursor.execute("""
                SELECT t.id, t.title, t.content, c.name as category_name
                FROM topics t
                JOIN categories c ON t.category_id = c.id
                WHERE t.title LIKE ? OR t.content LIKE ?
                LIMIT 10
            """, (search_term, search_term))
            
            topics = [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "snippet": row["content"][:200] + "...",
                    "category": row["category_name"]
                }
                for row in cursor.fetchall()
            ]
            
            # Поиск по глоссарию
            cursor.execute("""
                SELECT id, term, definition
                FROM glossary
                WHERE term LIKE ? OR definition LIKE ?
                LIMIT 10
            """, (search_term, search_term))
            
            glossary_terms = [
                {
                    "id": row["id"],
                    "term": row["term"],
                    "definition": row["definition"]
                }
                for row in cursor.fetchall()
            ]
            
            return SearchResults(
                topics=topics,
                glossary_terms=glossary_terms,
                query=query,
                total_results=len(topics) + len(glossary_terms)
            )
        finally:
            conn.close()


class RecommendationService:
    """Сервис для рекомендаций контента."""
    
    @staticmethod
    def get_recommendations(session_id: str, limit: int = 3, db_name: str = "testlearn.db") -> List[Topic]:
        """Получить рекомендации тем для изучения."""
        conn = get_db_connection(db_name)
        try:
            cursor = conn.cursor()
            
            # Получить категории, которые пользователь ещё не изучал
            cursor.execute("""
                SELECT c.id, c.name
                FROM categories c
                WHERE c.id NOT IN (
                    SELECT DISTINCT t.category_id
                    FROM topics t
                    JOIN read_topics rt ON t.id = rt.topic_id
                    WHERE rt.session_id = ?
                )
                LIMIT ?
            """, (session_id, limit))
            
            unread_categories = cursor.fetchall()
            
            if not unread_categories:
                # Если все категории изучены, вернуть случайные темы
                cursor.execute("""
                    SELECT t.id, t.category_id, t.title, t.content, t.order_num, c.name as category_name
                    FROM topics t
                    JOIN categories c ON t.category_id = c.id
                    ORDER BY RANDOM()
                    LIMIT ?
                """, (limit,))
            else:
                category_ids = [cat["id"] for cat in unread_categories]
                placeholders = ",".join("?" * len(category_ids))
                cursor.execute(f"""
                    SELECT t.id, t.category_id, t.title, t.content, t.order_num, c.name as category_name
                    FROM topics t
                    JOIN categories c ON t.category_id = c.id
                    WHERE t.category_id IN ({placeholders})
                    AND t.id NOT IN (
                        SELECT topic_id FROM read_topics WHERE session_id = ?
                    )
                    ORDER BY t.order_num
                    LIMIT ?
                """, (*category_ids, session_id, limit))
            
            recommendations = []
            for row in cursor.fetchall():
                recommendations.append(Topic(
                    id=row["id"],
                    category_id=row["category_id"],
                    title=row["title"],
                    content=row["content"],
                    order_num=row["order_num"],
                    category_name=row["category_name"]
                ))
            
            return recommendations
        finally:
            conn.close()


class LeaderboardService:
    """Сервис для управления таблицей лидеров."""
    
    @staticmethod
    def get_leaderboard(limit: int = 10, db_name: str = "testlearn.db") -> List[LeaderboardEntry]:
        """Получить таблицу лидеров."""
        conn = get_db_connection(db_name)
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    id as user_id,
                    session_id as username,
                    total_score as experience,
                    quizzes_passed,
                    topics_read
                FROM user_progress
                ORDER BY total_score DESC, quizzes_passed DESC
                LIMIT ?
            """, (limit,))
            
            leaderboard = []
            for rank, row in enumerate(cursor.fetchall(), 1):
                # Рассчитать уровень
                level, xp, _ = ProgressService.calculate_level(row["experience"])
                
                # Рассчитать средний балл
                avg_score = 0.0
                if row["quizzes_passed"] > 0:
                    cursor.execute("""
                        SELECT AVG(CAST(score AS FLOAT) / total * 100)
                        FROM quiz_results
                    """)
                    avg_result = cursor.fetchone()[0]
                    if avg_result:
                        avg_score = round(avg_result, 1)
                
                leaderboard.append(LeaderboardEntry(
                    rank=rank,
                    user_id=row["user_id"],
                    username=f"User_{row['username'][:8]}",
                    level=level,
                    experience=row["experience"],
                    quizzes_passed=row["quizzes_passed"],
                    average_score=avg_score
                ))
            
            return leaderboard
        finally:
            conn.close()


class CertificateService:
    """Сервис для генерации сертификатов."""
    
    @staticmethod
    def generate_certificate(session_id: str, db_name: str = "testlearn.db") -> Optional[Certificate]:
        """Сгенерировать сертификат о прохождении курса."""
        conn = get_db_connection(db_name)
        try:
            cursor = conn.cursor()
            
            # Получить прогресс пользователя
            cursor.execute("""
                SELECT id, total_score, quizzes_passed, topics_read
                FROM user_progress
                WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Проверить минимальные требования (5 тестов пройдено)
            if row["quizzes_passed"] < 5:
                return None
            
            # Рассчитать уровень
            level, xp, _ = ProgressService.calculate_level(row["total_score"])
            
            # Рассчитать средний балл
            cursor.execute("""
                SELECT AVG(CAST(score AS FLOAT) / total * 100)
                FROM quiz_results
            """)
            avg_result = cursor.fetchone()[0]
            average_score = round(avg_result, 1) if avg_result else 0.0
            
            cert_id = str(uuid.uuid4())
            issued_at = datetime.now().isoformat()
            
            return Certificate(
                id=cert_id,
                user_id=row["id"],
                username=f"User_{session_id[:8]}",
                issued_at=issued_at,
                level=level,
                topics_completed=row["topics_read"],
                quizzes_passed=row["quizzes_passed"],
                average_score=average_score,
                certificate_url=f"/certificates/{cert_id}"
            )
        finally:
            conn.close()


class CommentService:
    """Сервис для управления комментариями к темам."""
    
    @staticmethod
    def add_comment(topic_id: int, user_id: str, content: str, db_name: str = "testlearn.db") -> Comment:
        """Добавить комментарий к теме."""
        conn = get_db_connection(db_name)
        try:
            cursor = conn.cursor()
            comment_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO comments (id, topic_id, user_id, content, created_at, likes)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (comment_id, topic_id, user_id, content, created_at))
            
            conn.commit()
            
            return Comment(
                id=comment_id,
                topic_id=topic_id,
                user_id=user_id,
                username=f"User_{user_id[:8]}",
                content=content,
                created_at=created_at,
                likes=0
            )
        finally:
            conn.close()
    
    @staticmethod
    def get_comments(topic_id: int, db_name: str = "testlearn.db") -> List[Comment]:
        """Получить комментарии к теме."""
        conn = get_db_connection(db_name)
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, topic_id, user_id, content, created_at, likes
                FROM comments
                WHERE topic_id = ?
                ORDER BY created_at DESC
            """, (topic_id,))
            
            comments = []
            for row in cursor.fetchall():
                comments.append(Comment(
                    id=row["id"],
                    topic_id=row["topic_id"],
                    user_id=row["user_id"],
                    username=f"User_{row['user_id'][:8]}",
                    content=row["content"],
                    created_at=row["created_at"],
                    likes=row["likes"]
                ))
            
            return comments
        finally:
            conn.close()
    
    @staticmethod
    def like_comment(comment_id: str, db_name: str = "testlearn.db") -> bool:
        """Поставить лайк комментарию."""
        conn = get_db_connection(db_name)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE comments SET likes = likes + 1 WHERE id = ?
            """, (comment_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()


class NotificationService:
    """Сервис для управления уведомлениями."""
    
    @staticmethod
    def create_notification(user_id: str, title: str, message: str, 
                          notification_type: str, db_name: str = "testlearn.db") -> Notification:
        """Создать уведомление."""
        conn = get_db_connection(db_name)
        try:
            cursor = conn.cursor()
            notif_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO notifications (id, user_id, title, message, type, is_read, created_at)
                VALUES (?, ?, ?, ?, ?, 0, ?)
            """, (notif_id, user_id, title, message, notification_type, created_at))
            
            conn.commit()
            
            return Notification(
                id=notif_id,
                user_id=user_id,
                title=title,
                message=message,
                type=notification_type,
                is_read=False,
                created_at=created_at
            )
        finally:
            conn.close()
    
    @staticmethod
    def get_unread_notifications(user_id: str, db_name: str = "testlearn.db") -> List[Notification]:
        """Получить непрочитанные уведомления."""
        conn = get_db_connection(db_name)
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, user_id, title, message, type, is_read, created_at
                FROM notifications
                WHERE user_id = ? AND is_read = 0
                ORDER BY created_at DESC
            """, (user_id,))
            
            notifications = []
            for row in cursor.fetchall():
                notifications.append(Notification(
                    id=row["id"],
                    user_id=row["user_id"],
                    title=row["title"],
                    message=row["message"],
                    type=row["type"],
                    is_read=bool(row["is_read"]),
                    created_at=row["created_at"]
                ))
            
            return notifications
        finally:
            conn.close()
    
    @staticmethod
    def mark_as_read(notification_id: str, db_name: str = "testlearn.db") -> bool:
        """Отметить уведомление как прочитанное."""
        conn = get_db_connection(db_name)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE notifications SET is_read = 1 WHERE id = ?
            """, (notification_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()


def seed_initial_data():
    """Заполнение БД начальными данными через SQLAlchemy."""
    from sqlalchemy.orm import Session
    from app.db.database import SessionLocal
    from app.db.models import Category, Topic, Quiz, Question, GlossaryTerm
    
    db = SessionLocal()
    try:
        # Проверяем, есть ли уже данные
        if db.query(Category).count() > 0:
            return
        
        # --- Категории ---
        categories_data = [
            Category(name="Функциональное тестирование", slug="functional", description="Проверка функциональности приложения согласно требованиям", icon="check-circle"),
            Category(name="Нефункциональное тестирование", slug="non-functional", description="Тестирование производительности, безопасности и удобства", icon="shield"),
            Category(name="Методологии тестирования", slug="methodologies", description="Подходы к организации процесса тестирования", icon="layers"),
            Category(name="Инструменты тестирования", slug="tools", description="Обзор популярных инструментов и фреймворков", icon="wrench"),
            Category(name="Процесс создания тестов", slug="test-creation", description="Разработка тест-кейсов, сценариев и чек-листов", icon="file-text"),
        ]
        
        for cat in categories_data:
            db.add(cat)
        db.commit()
        
        # Получаем созданные категории
        categories = db.query(Category).all()
        cat_by_slug = {cat.slug: cat for cat in categories}
        
        # --- Темы ---
        topics_data = [
            ("functional", "Что такое функциональное тестирование",
             "Функциональное тестирование — это вид тестирования программного обеспечения, "
             "при котором проверяется соответствие системы функциональным требованиям."),
            ("functional", "Чёрный и белый ящики: подходы к тестированию",
             "Существует два основных подхода к проектированию тестов: чёрный и белый ящик."),
            ("non-functional", "Тестирование производительности",
             "Тестирование производительности оценивает скорость отклика и потребление ресурсов."),
            ("non-functional", "Тестирование безопасности",
             "Тестирование безопасности направлено на выявление уязвимостей в системе."),
            ("methodologies", "TDD: Разработка через тестирование",
             "TDD — методология, при которой тесты пишутся до написания кода."),
            ("methodologies", "BDD: Поведенческая разработка",
             "BDD описывает поведение системы на естественном языке."),
            ("tools", "Selenium для автоматизации",
             "Selenium — популярный инструмент для автоматизации веб-приложений."),
            ("tools", "Postman для тестирования API",
             "Postman позволяет тестировать REST API и создавать коллекции запросов."),
            ("test-creation", "Написание тест-кейсов",
             "Тест-кейс — документ, описывающий шаги для проверки функциональности."),
            ("test-creation", "Чек-листы в тестировании",
             "Чек-лист — список проверок для быстрого тестирования."),
        ]
        
        for idx, (slug, title, content) in enumerate(topics_data):
            category = cat_by_slug.get(slug)
            if category:
                topic = Topic(
                    category_id=category.id,
                    title=title,
                    content=content,
                    order_num=idx + 1
                )
                db.add(topic)
        
        # --- Тесты и вопросы ---
        quiz = Quiz(category_id=cat_by_slug["functional"].id, title="Основы функционального тестирования", description="Проверьте свои знания")
        db.add(quiz)
        db.commit()
        
        questions_data = [
            ("Что проверяет функциональное тестирование?", "Соответствие требованиям", "Производительность", "Безопасность", "Удобство", "A", "Функциональное тестирование проверяет соответствие ПО функциональным требованиям."),
            ("Какой подход использует знание внутреннего устройства кода?", "Чёрный ящик", "Белый ящик", "Серый ящик", "Зелёный ящик", "B", "Белый ящик предполагает знание внутренней структуры кода."),
        ]
        
        for q_text, opt_a, opt_b, opt_c, opt_d, correct, explanation in questions_data:
            question = Question(
                quiz_id=quiz.id,
                question_text=q_text,
                option_a=opt_a,
                option_b=opt_b,
                option_c=opt_c,
                option_d=opt_d,
                correct_option=correct,
                explanation=explanation,
                order_num=1
            )
            db.add(question)
        
        # --- Глоссарий ---
        glossary_data = [
            ("Баг", "Ошибка в программном обеспечении", "Б"),
            ("Тест-кейс", "Документ с шагами для проверки функциональности", "Т"),
            ("Регрессионное тестирование", "Повторное тестирование после изменений", "Р"),
            ("Смоук-тестирование", "Быстрая проверка основной функциональности", "С"),
        ]
        
        for term, definition, letter in glossary_data:
            db.add(GlossaryTerm(term=term, definition=definition, letter=letter))
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

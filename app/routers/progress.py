"""
User Progress API router
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, UTC
import uuid

from app.db.database import get_db
from app.db.models import UserProgress, ReadTopic, Bookmark, QuizResult, Topic
from app.schemas import UserProgressResponse

router = APIRouter()


@router.get("", response_model=UserProgressResponse)
def get_user_progress(request: Request, db: Session = Depends(get_db)):
    """Get current user's progress."""
    session_id = request.cookies.get("session_id")

    if not session_id:
        # Create a new session if none exists
        import uuid
        from datetime import datetime, UTC

        session_id = str(uuid.uuid4())
        progress = UserProgress(
            id=str(uuid.uuid4()),
            session_id=session_id,
            topics_read=0,
            quizzes_passed=0,
            total_score=0,
            last_visit=datetime.now(UTC)
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)

    progress = db.query(UserProgress).filter(UserProgress.session_id == session_id).first()

    if not progress:
        # Create new progress record
        import uuid
        from datetime import datetime, UTC

        progress = UserProgress(
            id=str(uuid.uuid4()),
            session_id=session_id,
            topics_read=0,
            quizzes_passed=0,
            total_score=0,
            last_visit=datetime.now(UTC)
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)

    # Calculate level and experience
    experience = progress.total_score
    level = 1
    xp_required = 100
    total_xp = experience

    while total_xp >= xp_required:
        total_xp -= xp_required
        level += 1
        xp_required = int(xp_required * 1.5)

    return {
        "id": progress.id,
        "session_id": progress.session_id,
        "topics_read": progress.topics_read,
        "quizzes_passed": progress.quizzes_passed,
        "total_score": progress.total_score,
        "last_visit": progress.last_visit.isoformat() if progress.last_visit else None,
        "level": level,
        "experience": experience
    }


@router.post("/mark-topic-read")
def mark_topic_read(topic_id: int, request: Request, db: Session = Depends(get_db)):
    """Mark a topic as read for the current user."""
    session_id = request.cookies.get("session_id")

    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())

    from datetime import datetime, UTC

    # Check if already marked
    existing = db.query(ReadTopic).filter(
        ReadTopic.session_id == session_id,
        ReadTopic.topic_id == topic_id
    ).first()

    if not existing:
        read_topic = ReadTopic(
            session_id=session_id,
            topic_id=topic_id,
            read_at=datetime.now(UTC)
        )
        db.add(read_topic)

        # Update progress
        progress = db.query(UserProgress).filter(UserProgress.session_id == session_id).first()
        if progress:
            progress.topics_read += 1
            progress.last_visit = datetime.now(UTC)
        else:
            import uuid
            progress = UserProgress(
                id=str(uuid.uuid4()),
                session_id=session_id,
                topics_read=1,
                quizzes_passed=0,
                total_score=0,
                last_visit=datetime.now(UTC)
            )
            db.add(progress)

        db.commit()

    return {"status": "success", "session_id": session_id}


@router.get("/bookmarks", response_model=List[dict])
def get_bookmarks(request: Request, db: Session = Depends(get_db)):
    """Get user's bookmarks."""
    session_id = request.cookies.get("session_id")

    if not session_id:
        return []

    bookmarks = db.query(Bookmark).filter(Bookmark.session_id == session_id).all()

    result = []
    for bm in bookmarks:
        result.append({
            "topic_id": bm.topic_id,
            "bookmarked_at": bm.bookmarked_at.isoformat() if bm.bookmarked_at else None
        })

    return result


@router.post("/bookmarks/{topic_id}")
def add_bookmark(topic_id: int, request: Request, db: Session = Depends(get_db)):
    """Add a bookmark for a topic."""
    session_id = request.cookies.get("session_id")

    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())

    from datetime import datetime, UTC

    # Check if already bookmarked
    existing = db.query(Bookmark).filter(
        Bookmark.session_id == session_id,
        Bookmark.topic_id == topic_id
    ).first()

    if not existing:
        bookmark = Bookmark(
            session_id=session_id,
            topic_id=topic_id,
            bookmarked_at=datetime.now(UTC)
        )
        db.add(bookmark)
        db.commit()

    return {"status": "success", "session_id": session_id}


@router.delete("/bookmarks/{topic_id}")
def remove_bookmark(topic_id: int, request: Request, db: Session = Depends(get_db)):
    """Remove a bookmark for a topic."""
    session_id = request.cookies.get("session_id")

    if session_id:
        bookmark = db.query(Bookmark).filter(
            Bookmark.session_id == session_id,
            Bookmark.topic_id == topic_id
        ).first()

        if bookmark:
            db.delete(bookmark)
            db.commit()

    return {"status": "success"}


@router.get("/stats")
def get_progress_stats(request: Request, db: Session = Depends(get_db)):
    """Get user progress statistics including unlocked achievements and daily challenge."""
    session_id = request.cookies.get("session_id", "anonymous")

    # Get user progress
    progress = db.query(UserProgress).filter(
        UserProgress.session_id == session_id
    ).first()

    if not progress:
        # Return default stats for new user
        return {
            "user_progress": {
                "topics_read": 0,
                "quizzes_passed": 0,
                "total_score": 0,
                "level": 1,
                "experience": 0
            },
            "unlocked_achievements": [],
            "daily_challenge": None
        }

    # Calculate level and experience
    experience = progress.total_score
    level = 1
    xp_required = 100
    total_xp = experience

    while total_xp >= xp_required:
        total_xp -= xp_required
        level += 1
        xp_required = int(xp_required * 1.5)

    # Get unlocked achievements
    achievements = [
        {
            "id": 1,
            "name": "Первые шаги",
            "description": "Прочитать первую тему",
            "icon": "📚",
            "unlocked": progress.topics_read >= 1
        },
        {
            "id": 2,
            "name": "Любопытный",
            "description": "Прочитать 5 тем",
            "icon": "🔍",
            "unlocked": progress.topics_read >= 5
        },
        {
            "id": 3,
            "name": "Эрудит",
            "description": "Прочитать 10 тем",
            "icon": "🎓",
            "unlocked": progress.topics_read >= 10
        },
        {
            "id": 4,
            "name": "Новичок в тестировании",
            "description": "Пройти первый тест",
            "icon": "✅",
            "unlocked": progress.quizzes_passed >= 1
        },
        {
            "id": 5,
            "name": "Опытный тестировщик",
            "description": "Пройти 5 тестов",
            "icon": "🏆",
            "unlocked": progress.quizzes_passed >= 5
        },
        {
            "id": 6,
            "name": "Мастер тестирования",
            "description": "Набрать 100+ баллов",
            "icon": "👑",
            "unlocked": progress.total_score >= 100
        }
    ]

    unlocked_achievements = [a for a in achievements if a["unlocked"]]

    # Get daily challenge
    from sqlalchemy import func
    quiz = db.query(QuizResult).order_by(func.random()).first()
    
    daily_challenge = None
    if quiz:
        expires = datetime.now(UTC).replace(hour=23, minute=59, second=59)
        daily_challenge = {
            "id": 1,
            "quiz_id": quiz.quiz_id,
            "title": "Ежедневный вызов",
            "description": "Пройдите тест и получите 50 XP!",
            "bonus_xp": 50,
            "completed": False,
            "expires_at": expires.isoformat()
        }

    return {
        "user_progress": {
            "topics_read": progress.topics_read,
            "quizzes_passed": progress.quizzes_passed,
            "total_score": progress.total_score,
            "level": level,
            "experience": experience
        },
        "unlocked_achievements": unlocked_achievements,
        "daily_challenge": daily_challenge
    }

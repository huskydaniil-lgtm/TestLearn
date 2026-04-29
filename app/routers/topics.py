"""
Topics API router
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import Topic, Category, ReadTopic
from app.schemas import TopicResponse, TopicCreate

router = APIRouter()


@router.get("", response_model=List[TopicResponse])
def get_topics(db: Session = Depends(get_db)):
    """Get all topics."""
    topics = db.query(Topic).order_by(Topic.order_num, Topic.title).all()
    
    result = []
    for topic in topics:
        category = db.query(Category).filter(Category.id == topic.category_id).first()
        result.append({
            "id": topic.id,
            "title": topic.title,
            "content": topic.content,
            "category_id": topic.category_id,
            "order_num": topic.order_num,
            "category_name": category.name if category else None
        })
    
    return result


@router.get("/{topic_id}", response_model=TopicResponse)
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    """Get a specific topic by ID."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    category = db.query(Category).filter(Category.id == topic.category_id).first()
    
    return {
        "id": topic.id,
        "title": topic.title,
        "content": topic.content,
        "category_id": topic.category_id,
        "order_num": topic.order_num,
        "category_name": category.name if category else None
    }


@router.post("", response_model=TopicResponse)
def create_topic(topic: TopicCreate, db: Session = Depends(get_db)):
    """Create a new topic (admin only)."""
    # Verify category exists
    category = db.query(Category).filter(Category.id == topic.category_id).first()
    if not category:
        raise HTTPException(status_code=400, detail="Category not found")
    
    db_topic = Topic(**topic.model_dump())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    
    return {
        "id": db_topic.id,
        "title": db_topic.title,
        "content": db_topic.content,
        "category_id": db_topic.category_id,
        "order_num": db_topic.order_num,
        "category_name": category.name
    }


@router.put("/{topic_id}", response_model=TopicResponse)
def update_topic(topic_id: int, topic: TopicCreate, db: Session = Depends(get_db)):
    """Update an existing topic (admin only)."""
    db_topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not db_topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Verify category exists
    category = db.query(Category).filter(Category.id == topic.category_id).first()
    if not category:
        raise HTTPException(status_code=400, detail="Category not found")
    
    for key, value in topic.model_dump().items():
        setattr(db_topic, key, value)
    
    db.commit()
    db.refresh(db_topic)
    
    return {
        "id": db_topic.id,
        "title": db_topic.title,
        "content": db_topic.content,
        "category_id": db_topic.category_id,
        "order_num": db_topic.order_num,
        "category_name": category.name
    }


@router.delete("/{topic_id}")
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    """Delete a topic (admin only)."""
    db_topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not db_topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    db.delete(db_topic)
    db.commit()

    return {"status": "deleted"}


@router.get("/recommendations", response_model=List[TopicResponse])
def get_recommendations(request: Request, db: Session = Depends(get_db)):
    """Get recommended topics for the user based on their progress."""
    session_id = request.cookies.get("session_id", "anonymous")

    # Get topics that the user has not read
    if session_id != "anonymous":
        read_topic_ids = db.query(ReadTopic.topic_id).filter(
            ReadTopic.session_id == session_id
        ).all()
        read_topic_ids = [id[0] for id in read_topic_ids]

        # Get unread topics
        unread_topics = db.query(Topic).filter(
            ~Topic.id.in_(read_topic_ids)
        ).order_by(Topic.order_num, Topic.title).all()
    else:
        # For anonymous users, return all topics (or maybe a default set)
        unread_topics = db.query(Topic).order_by(Topic.order_num, Topic.title).all()

    # If no unread topics, return all topics (so we always have something to recommend)
    if not unread_topics:
        unread_topics = db.query(Topic).order_by(Topic.order_num, Topic.title).all()

    # Limit to 5 recommendations
    recommendations = unread_topics[:5]

    result = []
    for topic in recommendations:
        category = db.query(Category).filter(Category.id == topic.category_id).first()
        result.append({
            "id": topic.id,
            "title": topic.title,
            "content": topic.content,
            "category_id": topic.category_id,
            "order_num": topic.order_num,
            "category_name": category.name if category else None
        })

    return result

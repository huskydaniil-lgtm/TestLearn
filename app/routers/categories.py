"""
Categories API router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import Category, Topic
from app.schemas import CategoryResponse, CategoryCreate

router = APIRouter()


@router.get("", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """Get all categories with topic counts."""
    categories = db.query(Category).all()
    
    result = []
    for cat in categories:
        topics_count = db.query(Topic).filter(Topic.category_id == cat.id).count()
        cat_dict = {
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "description": cat.description or "",
            "icon": cat.icon or "check-circle",
            "topics_count": topics_count
        }
        result.append(cat_dict)
    
    return result


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get a specific category by ID."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    topics_count = db.query(Topic).filter(Topic.category_id == category_id).count()
    
    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "description": category.description or "",
        "icon": category.icon or "check-circle",
        "topics_count": topics_count
    }


@router.post("", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category (admin only)."""
    # Check if slug already exists
    existing = db.query(Category).filter(Category.slug == category.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category with this slug already exists")
    
    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return {
        "id": db_category.id,
        "name": db_category.name,
        "slug": db_category.slug,
        "description": db_category.description or "",
        "icon": db_category.icon or "check-circle",
        "topics_count": 0
    }

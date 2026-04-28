"""
Security utilities for password hashing and authentication
"""
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid.uuid4())


def create_admin_session(username: str, db_session, expires_hours: int = 24) -> str:
    """Create a new admin session in the database."""
    from app.db.models import AdminSession
    
    session_id = generate_session_id()
    expires = datetime.utcnow() + timedelta(hours=expires_hours)
    
    admin_session = AdminSession(
        id=session_id,
        username=username,
        expires=expires,
        created_at=datetime.utcnow()
    )
    
    db_session.add(admin_session)
    db_session.commit()
    
    return session_id


def verify_admin_session(session_id: str, db_session) -> Optional[str]:
    """
    Verify an admin session and return username if valid.
    Returns None if session is invalid or expired.
    """
    from app.db.models import AdminSession
    
    session = db_session.query(AdminSession).filter(
        AdminSession.id == session_id
    ).first()
    
    if not session:
        return None
    
    if session.expires < datetime.utcnow():
        # Session expired, delete it
        db_session.delete(session)
        db_session.commit()
        return None
    
    return session.username


def delete_admin_session(session_id: str, db_session):
    """Delete an admin session (logout)."""
    from app.db.models import AdminSession
    
    session = db_session.query(AdminSession).filter(
        AdminSession.id == session_id
    ).first()
    
    if session:
        db_session.delete(session)
        db_session.commit()

"""Base database models and configuration"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, DateTime
from datetime import datetime

Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


def get_database_url():
    """Get database URL from environment"""
    from pydantic_settings import BaseSettings
    
    class Settings(BaseSettings):
        database_url: str = "sqlite:///./tbaml_dev.db"
        
        model_config = {
            "env_file": ".env",
            "extra": "ignore"  # Ignore extra fields from .env
        }
    
    settings = Settings()
    return settings.database_url


def create_database_engine():
    """Create database engine"""
    database_url = get_database_url()
    if database_url.startswith("sqlite"):
        engine = create_engine(
            database_url, 
            connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(database_url)
    return engine


def get_session_factory():
    """Get database session factory"""
    engine = create_database_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal, engine


def init_db():
    """Initialize database tables"""
    # Import models to register them with Base.metadata
    from app.models.lob import LOBVerification  # noqa: F401
    
    _, engine = get_session_factory()
    Base.metadata.create_all(bind=engine)


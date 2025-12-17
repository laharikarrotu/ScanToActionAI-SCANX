"""
Database setup for Supabase/Postgres
"""
from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from pydantic_settings import BaseSettings

class DatabaseSettings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./memory/scanx.db")
    
    class Config:
        env_file = ".env"

db_settings = DatabaseSettings()

# Create engine
if db_settings.database_url.startswith("postgresql"):
    # Postgres/Supabase
    engine = create_engine(db_settings.database_url, pool_pre_ping=True)
else:
    # SQLite fallback
    engine = create_engine(db_settings.database_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class ScanRequest(Base):
    __tablename__ = "scan_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=True)
    image_hash = Column(String, index=True)
    intent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class UISchema(Base):
    __tablename__ = "ui_schemas"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_request_id = Column(Integer, index=True, nullable=True)
    session_id = Column(String, index=True, nullable=True)
    page_type = Column(String)
    url_hint = Column(String, nullable=True)
    elements = Column(JSON)  # Store UI elements as JSON
    created_at = Column(DateTime, default=datetime.utcnow)

class ActionPlan(Base):
    __tablename__ = "action_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_request_id = Column(Integer, index=True, nullable=True)
    session_id = Column(String, index=True, nullable=True)
    task = Column(String)
    steps = Column(JSON)  # Store action steps as JSON
    estimated_time = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ExecutionResult(Base):
    __tablename__ = "execution_results"
    
    id = Column(Integer, primary_key=True, index=True)
    action_plan_id = Column(Integer, index=True, nullable=True)
    session_id = Column(String, index=True, nullable=True)
    status = Column(String)
    message = Column(Text)
    final_url = Column(String, nullable=True)
    screenshot_path = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    logs = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


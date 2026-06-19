from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.database import Base

class Vocabulary(Base):
    __tablename__ = "vocabulary"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, unique=True, index=True)
    meaning = Column(String)
    default_context = Column(String, default="No context provided.")
    default_translation = Column(String, default="Tərcümə qeyd edilməyib.")
    
    # Yeni əlavə edilən sütunlar
    category = Column(String, default="Personal")
    level = Column(String, default="Custom")
    
    # Spaced Repetition (Aralıqlı Təkrar) sisteminin parametrləri
    interval = Column(Integer, default=1)
    ease_factor = Column(Float, default=2.5)
    next_review = Column(DateTime, default=datetime.utcnow)
from sqlalchemy import Column, String, DateTime
from database.db import Base
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime


class Student(Base):
    __tablename__ = "students"

    gr_no = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    enrollment_number = Column(String)
    student_type = Column(String)
    batch_period = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

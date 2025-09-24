from sqlalchemy import Column, String, DateTime
from database.db import Base
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime


class Student(Base):
    __tablename__ = "students"
    student_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    enrollment_number = Column(String)
    student_type = Column(String)
    batch_period = Column(String)
    gr_no = Column(Integer)
    pcm = Column(Integer)  # o If not, add this
    tenth = Column(Integer)
    twelfth = Column(Integer)
    acpc = Column(String)
    admission_quota = Column(String)
    nationality = Column(String)
    gender = Column(String)
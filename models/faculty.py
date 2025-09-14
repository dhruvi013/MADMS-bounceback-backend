from sqlalchemy import Column, Integer, String, Date
from database.db import Base

class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    appointment_letter = Column(Date, nullable=True)
    salary_slip = Column(String, nullable=True)
    specialization = Column(String, nullable=True)
    subject_allocation = Column(String, nullable=True)
    type = Column(String, nullable=True)

# Database models
#Database tables
#Job table
#Certificate table

from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    status = Column(String, default="PROCESSING")

    total_recipients = Column(Integer)

    success_count = Column(Integer, default=0)

    failure_count = Column(Integer, default=0)


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)

    job_id = Column(Integer, ForeignKey("jobs.id"))

    recipient_name = Column(String)

    email = Column(String)

    course_name = Column(String)

    status = Column(String)

    certificate_path = Column(String)

    error_message = Column(String, nullable=True)
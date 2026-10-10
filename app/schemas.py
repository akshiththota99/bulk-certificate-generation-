# Pydantic schemas
#Input validation
#Recipient Schema
#CertificateRequest Schema

from pydantic import BaseModel, EmailStr
from typing import List


class Recipient(BaseModel):
    name: str
    email: EmailStr


class CertificateRequest(BaseModel):
    course_name: str
    recipients: List[Recipient]
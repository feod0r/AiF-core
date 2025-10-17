from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class OwnerOut(BaseModel):
    id: int
    name: str
    inn: str
    vendista_user: Optional[str] = None
    vendista_pass: Optional[str] = None
    start_date: datetime
    end_date: datetime

    model_config = ConfigDict(from_attributes=True)

class OwnerIn(BaseModel):
    name: str
    inn: str
    vendista_user: Optional[str] = None
    vendista_pass: Optional[str] = None

class OwnerUpdate(BaseModel):
    name: Optional[str] = None
    inn: Optional[str] = None
    vendista_user: Optional[str] = None
    vendista_pass: Optional[str] = None 
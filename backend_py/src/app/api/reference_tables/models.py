from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class ReferenceItemOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ReferenceItemIn(BaseModel):
    name: str
    description: Optional[str] = None

class ReferenceItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ReferenceItemCreateOrUpdate(BaseModel):
    name: str
    description: Optional[str] = None 
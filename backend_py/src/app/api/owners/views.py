from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .models import OwnerIn, OwnerOut, OwnerUpdate
from . import controllers
from app.external.sqlalchemy.session import get_db
from typing import List

router = APIRouter()

@router.get("/owners", response_model=List[OwnerOut])
def read_owners(
    skip: int = 0, 
    limit: int = 100, 
    search: str = None,
    start_date_from: str = None,
    start_date_to: str = None,
    db: Session = Depends(get_db)
):
    return controllers.get_owners(
        db, 
        skip=skip, 
        limit=limit,
        search=search,
        start_date_from=start_date_from,
        start_date_to=start_date_to
    )

@router.get("/owners/{owner_id}", response_model=OwnerOut)
def read_owner(owner_id: int, db: Session = Depends(get_db)):
    return controllers.get_owner(db, owner_id)

@router.post("/owners", response_model=OwnerOut)
def create_owner(owner: OwnerIn, db: Session = Depends(get_db)):
    return controllers.create_owner(db, owner)

@router.put("/owners/{owner_id}", response_model=OwnerOut)
def update_owner(owner_id: int, owner: OwnerUpdate, db: Session = Depends(get_db)):
    return controllers.update_owner(db, owner_id, owner)

@router.delete("/owners/{owner_id}")
def delete_owner(owner_id: int, db: Session = Depends(get_db)):
    return controllers.delete_owner(db, owner_id) 
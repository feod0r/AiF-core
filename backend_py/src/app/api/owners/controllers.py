from sqlalchemy.orm import Session
from fastapi import HTTPException
from .models import OwnerIn, OwnerUpdate
from app.external.sqlalchemy.utils import owners as owner_crud

def get_owner(db: Session, owner_id: int):
    owner = owner_crud.get_owner(db, owner_id)
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    return owner

def get_owners(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: str = None,
    start_date_from: str = None,
    start_date_to: str = None
):
    return owner_crud.get_owners(
        db, 
        skip=skip, 
        limit=limit,
        search=search,
        start_date_from=start_date_from,
        start_date_to=start_date_to
    )

def create_owner(db: Session, owner_in: OwnerIn):
    return owner_crud.create_owner(
        db, 
        name=owner_in.name, 
        inn=owner_in.inn, 
        vendista_user=owner_in.vendista_user, 
        vendista_pass=owner_in.vendista_pass
    )

def update_owner(db: Session, owner_id: int, owner_update: OwnerUpdate):
    owner = owner_crud.update_owner(
        db, 
        owner_id, 
        name=owner_update.name, 
        inn=owner_update.inn, 
        vendista_user=owner_update.vendista_user, 
        vendista_pass=owner_update.vendista_pass
    )
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    return owner

def delete_owner(db: Session, owner_id: int):
    success = owner_crud.delete_owner(db, owner_id)
    if not success:
        raise HTTPException(status_code=404, detail="Owner not found")
    return {"ok": True} 
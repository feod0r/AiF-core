from sqlalchemy.orm import Session
from ..models import Owner
from typing import List, Optional
from datetime import datetime

def get_owner(db: Session, owner_id: int) -> Optional[Owner]:
    return db.query(Owner).filter(Owner.id == owner_id, Owner.end_date > datetime.utcnow()).first()

def get_owners(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None
) -> List[Owner]:
    query = db.query(Owner).filter(Owner.end_date > datetime.utcnow())
    
    # Поиск по названию или ИНН
    if search:
        query = query.filter(
            (Owner.name.ilike(f"%{search}%")) | (Owner.inn.ilike(f"%{search}%"))
        )

    # Фильтр по дате начала
    if start_date_from:
        try:
            start_from_date = datetime.fromisoformat(start_date_from.replace('Z', '+00:00'))
            query = query.filter(Owner.start_date >= start_from_date)
        except ValueError:
            pass

    if start_date_to:
        try:
            start_to_date = datetime.fromisoformat(start_date_to.replace('Z', '+00:00'))
            query = query.filter(Owner.start_date <= start_to_date)
        except ValueError:
            pass

    return query.offset(skip).limit(limit).all()

def create_owner(db: Session, name: str, inn: str, vendista_user: Optional[str] = None, 
                vendista_pass: Optional[str] = None) -> Owner:
    db_owner = Owner(
        name=name,
        inn=inn,
        vendista_user=vendista_user,
        vendista_pass=vendista_pass,
        start_date=datetime.utcnow(),
        end_date=datetime(9999, 12, 31, 0, 0, 0)
    )
    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)
    return db_owner

def update_owner(db: Session, owner_id: int, name: Optional[str] = None, 
                inn: Optional[str] = None, vendista_user: Optional[str] = None, 
                vendista_pass: Optional[str] = None) -> Optional[Owner]:
    owner = db.query(Owner).filter(Owner.id == owner_id, Owner.end_date > datetime.utcnow()).first()
    if not owner:
        return None
    if name is not None:
        owner.name = name
    if inn is not None:
        owner.inn = inn
    if vendista_user is not None:
        owner.vendista_user = vendista_user
    if vendista_pass is not None:
        owner.vendista_pass = vendista_pass
    db.commit()
    db.refresh(owner)
    return owner

# Мягкое удаление владельца (soft delete)
def delete_owner(db: Session, owner_id: int) -> bool:
    owner = db.query(Owner).filter(Owner.id == owner_id, Owner.end_date > datetime.utcnow()).first()
    if not owner:
        return False
    owner.end_date = datetime.utcnow()
    db.commit()
    return True 
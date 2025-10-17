from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .models import TerminalIn, TerminalOut, TerminalUpdate
from . import controllers
from app.external.sqlalchemy.session import get_db
from typing import List

router = APIRouter()

@router.get("/terminals", response_model=List[TerminalOut])
def read_terminals(
    skip: int = 0, 
    limit: int = 100, 
    search: str = None,
    owner_id: int = None,
    account_id: int = None,
    start_date_from: str = None,
    start_date_to: str = None,
    db: Session = Depends(get_db)
):
    return controllers.get_terminals(
        db, 
        skip=skip, 
        limit=limit,
        search=search,
        owner_id=owner_id,
        account_id=account_id,
        start_date_from=start_date_from,
        start_date_to=start_date_to
    )

@router.get("/terminals/{terminal_id}", response_model=TerminalOut)
def read_terminal(terminal_id: int, db: Session = Depends(get_db)):
    return controllers.get_terminal(db, terminal_id)

@router.post("/terminals", response_model=TerminalOut)
def create_terminal(terminal: TerminalIn, db: Session = Depends(get_db)):
    return controllers.create_terminal(db, terminal)

@router.put("/terminals/{terminal_id}", response_model=TerminalOut)
def update_terminal(terminal_id: int, terminal: TerminalUpdate, db: Session = Depends(get_db)):
    return controllers.update_terminal(db, terminal_id, terminal)

@router.delete("/terminals/{terminal_id}")
def delete_terminal(terminal_id: int, db: Session = Depends(get_db)):
    return controllers.delete_terminal(db, terminal_id) 
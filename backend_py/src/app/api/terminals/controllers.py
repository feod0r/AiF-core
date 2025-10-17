from sqlalchemy.orm import Session
from fastapi import HTTPException
from .models import TerminalIn, TerminalUpdate
from app.external.sqlalchemy.utils import terminals as terminal_crud


def get_terminal(db: Session, terminal_id: int):
    terminal = terminal_crud.get_terminal_with_owner(db, terminal_id)
    if not terminal:
        raise HTTPException(status_code=404, detail="Terminal not found")
    return terminal


def get_terminals(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: str = None,
    owner_id: int = None,
    account_id: int = None,
    start_date_from: str = None,
    start_date_to: str = None
):
    return terminal_crud.get_terminals_with_owners(
        db, 
        skip=skip, 
        limit=limit,
        search=search,
        owner_id=owner_id,
        account_id=account_id,
        start_date_from=start_date_from,
        start_date_to=start_date_to
    )


def create_terminal(db: Session, terminal_in: TerminalIn):
    return terminal_crud.create_terminal(db, terminal_in)


def update_terminal(db: Session, terminal_id: int, terminal_update: TerminalUpdate):
    terminal = terminal_crud.update_terminal(db, terminal_id, terminal_update)
    if not terminal:
        raise HTTPException(status_code=404, detail="Terminal not found")
    return terminal


def delete_terminal(db: Session, terminal_id: int):
    success = terminal_crud.delete_terminal(db, terminal_id)
    if not success:
        raise HTTPException(status_code=404, detail="Terminal not found")
    return {"ok": True}

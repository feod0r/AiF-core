from sqlalchemy.orm import Session, joinedload
from sqlalchemy import cast, String
from ..models import Terminal, Owner
from typing import List, Optional
from datetime import datetime
from app.api.terminals.models import TerminalIn, TerminalUpdate


def get_terminal(db: Session, terminal_id: int) -> Optional[Terminal]:
    return (
        db.query(Terminal)
        .filter(Terminal.id == terminal_id, Terminal.end_date > datetime.utcnow())
        .first()
    )


def get_terminals(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    owner_id: Optional[int] = None,
    account_id: Optional[int] = None,
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None
) -> List[Terminal]:
    query = db.query(Terminal).filter(Terminal.end_date > datetime.utcnow())
    
    if search:
        query = query.filter(
            (Terminal.name.ilike(f"%{search}%")) | 
            (cast(Terminal.terminal, String).ilike(f"%{search}%"))
        )
    if owner_id is not None:
        query = query.filter(Terminal.owner_id == owner_id)
    if account_id is not None:
        query = query.filter(Terminal.account_id == account_id)
    if start_date_from:
        try:
            start_from_date = datetime.fromisoformat(start_date_from.replace('Z', '+00:00'))
            query = query.filter(Terminal.start_date >= start_from_date)
        except ValueError:
            pass
    if start_date_to:
        try:
            start_to_date = datetime.fromisoformat(start_date_to.replace('Z', '+00:00'))
            query = query.filter(Terminal.start_date <= start_to_date)
        except ValueError:
            pass
    
    return query.offset(skip).limit(limit).all()


def get_terminal_with_owner(db: Session, terminal_id: int) -> Optional[Terminal]:
    return (
        db.query(Terminal)
        .options(joinedload(Terminal.owner), joinedload(Terminal.account))
        .filter(Terminal.id == terminal_id, Terminal.end_date > datetime.utcnow())
        .first()
    )


def get_terminals_with_owners(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    owner_id: Optional[int] = None,
    account_id: Optional[int] = None,
    start_date_from: Optional[str] = None,
    start_date_to: Optional[str] = None
) -> List[Terminal]:
    query = (
        db.query(Terminal)
        .options(joinedload(Terminal.owner), joinedload(Terminal.account))
        .filter(Terminal.end_date > datetime.utcnow())
    )
    
    if search:
        query = query.filter(
            (Terminal.name.ilike(f"%{search}%")) | 
            (cast(Terminal.terminal, String).ilike(f"%{search}%"))
        )
    if owner_id is not None:
        query = query.filter(Terminal.owner_id == owner_id)
    if account_id is not None:
        query = query.filter(Terminal.account_id == account_id)
    if start_date_from:
        try:
            start_from_date = datetime.fromisoformat(start_date_from.replace('Z', '+00:00'))
            query = query.filter(Terminal.start_date >= start_from_date)
        except ValueError:
            pass
    if start_date_to:
        try:
            start_to_date = datetime.fromisoformat(start_date_to.replace('Z', '+00:00'))
            query = query.filter(Terminal.start_date <= start_to_date)
        except ValueError:
            pass
    
    return query.offset(skip).limit(limit).all()


def create_terminal(db: Session, terminal_data: TerminalIn) -> Terminal:
    db_terminal = Terminal(
        name=terminal_data.name,
        terminal=terminal_data.terminal,
        owner_id=terminal_data.owner_id,
        account_id=terminal_data.account_id,
        start_date=terminal_data.start_date
        if terminal_data.start_date
        else datetime.utcnow(),
        end_date=terminal_data.end_date
        if terminal_data.end_date
        else datetime(9999, 12, 31, 0, 0, 0),
    )
    db.add(db_terminal)
    db.commit()
    db.refresh(db_terminal)
    return db_terminal


# Функция-обёртка для обратной совместимости
def create_terminal_legacy(
    db: Session,
    name: str,
    terminal: Optional[int] = None,
    owner_id: Optional[int] = None,
    account_id: Optional[int] = None,
) -> Terminal:
    """Устаревшая функция для обратной совместимости"""
    terminal_data = TerminalIn(
        name=name,
        terminal=terminal,
        owner_id=owner_id,
        account_id=account_id,
    )
    return create_terminal(db, terminal_data)


def update_terminal(
    db: Session,
    terminal_id: int,
    terminal_data: TerminalUpdate,
) -> Optional[Terminal]:
    terminal_obj = (
        db.query(Terminal)
        .filter(Terminal.id == terminal_id, Terminal.end_date > datetime.utcnow())
        .first()
    )
    if not terminal_obj:
        return None

    # Обновляем только переданные поля
    if terminal_data.name is not None:
        terminal_obj.name = terminal_data.name
    if terminal_data.terminal is not None:
        terminal_obj.terminal = terminal_data.terminal
    if terminal_data.owner_id is not None:
        terminal_obj.owner_id = terminal_data.owner_id
    if terminal_data.account_id is not None:
        terminal_obj.account_id = terminal_data.account_id
    if terminal_data.start_date is not None:
        terminal_obj.start_date = terminal_data.start_date
    if terminal_data.end_date is not None:
        terminal_obj.end_date = terminal_data.end_date

    db.commit()
    db.refresh(terminal_obj)
    return terminal_obj


# Мягкое удаление терминала (soft delete)
def delete_terminal(db: Session, terminal_id: int) -> bool:
    terminal_obj = (
        db.query(Terminal)
        .filter(Terminal.id == terminal_id, Terminal.end_date > datetime.utcnow())
        .first()
    )
    if not terminal_obj:
        return False

    terminal_obj.end_date = datetime.utcnow()
    db.commit()
    return True


def get_active_terminals(db: Session) -> List[Terminal]:
    """Получить все активные терминалы с данными владельцев"""
    return (
        db.query(Terminal)
        .options(joinedload(Terminal.owner), joinedload(Terminal.account))
        .filter(Terminal.end_date > datetime.utcnow())
        .all()
    )

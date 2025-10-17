from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.external.sqlalchemy.utils import machines as machine_crud

from .models import MachineIn, MachineUpdate


def get_machine(db: Session, machine_id: int):
    machine = machine_crud.get_machine(db, machine_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine


def get_machines(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: str = None,
    is_active: bool = None,
    terminal_id: int = None,
    rent_id: int = None,
    phone_id: int = None,
    start_date_from: str = None,
    start_date_to: str = None
):
    return machine_crud.get_machines(
        db, 
        skip=skip, 
        limit=limit,
        search=search,
        is_active=is_active,
        terminal_id=terminal_id,
        rent_id=rent_id,
        phone_id=phone_id,
        start_date_from=start_date_from,
        start_date_to=start_date_to
    )


def create_machine(db: Session, machine_in: MachineIn):
    return machine_crud.create_machine(db, machine_in)


def update_machine(db: Session, machine_id: int, machine_update: MachineUpdate):
    machine = machine_crud.update_machine(db, machine_id, machine_update)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine


def delete_machine(db: Session, machine_id: int):
    success = machine_crud.delete_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=404, detail="Machine not found")
    return {"ok": True}

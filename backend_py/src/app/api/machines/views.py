from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .models import MachineIn, MachineOut, MachineUpdate
from . import controllers
from app.external.sqlalchemy.session import get_db
from typing import List

router = APIRouter()

@router.get("/machines", response_model=List[MachineOut])
def read_machines(
    skip: int = 0, 
    limit: int = 100, 
    search: str = None,
    is_active: bool = None,
    terminal_id: int = None,
    rent_id: int = None,
    phone_id: int = None,
    start_date_from: str = None,
    start_date_to: str = None,
    db: Session = Depends(get_db)
):
    return controllers.get_machines(
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

@router.get("/machines/{machine_id}", response_model=MachineOut)
def read_machine(machine_id: int, db: Session = Depends(get_db)):
    return controllers.get_machine(db, machine_id)

@router.post("/machines", response_model=MachineOut)
def create_machine(machine: MachineIn, db: Session = Depends(get_db)):
    return controllers.create_machine(db, machine)

@router.put("/machines/{machine_id}", response_model=MachineOut)
def update_machine(machine_id: int, machine: MachineUpdate, db: Session = Depends(get_db)):
    return controllers.update_machine(db, machine_id, machine)

@router.delete("/machines/{machine_id}")
def delete_machine(machine_id: int, db: Session = Depends(get_db)):
    return controllers.delete_machine(db, machine_id) 
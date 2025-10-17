"""
API endpoints для управления запланированными задачами
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.external.sqlalchemy.session import get_db
from app.external.sqlalchemy.models import User
from app.api.auth.dependencies import get_current_user
from .controllers import ScheduledJobController
from .models import (
    ScheduledJobCreate,
    ScheduledJobUpdate,
    ScheduledJobOut,
    ScheduledJobStats,
    JobExecutionResult,
    JobTemplate
)


router = APIRouter()


def get_controller(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ScheduledJobController:
    """Dependency для получения контроллера"""
    return ScheduledJobController(db, current_user)


@router.get("/jobs", response_model=List[ScheduledJobOut])
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    job_type: Optional[str] = Query(None, description="Фильтр по типу задачи"),
    controller: ScheduledJobController = Depends(get_controller)
):
    """Получить список всех запланированных задач"""
    return controller.list_jobs(
        skip=skip,
        limit=limit,
        is_active=is_active,
        job_type=job_type
    )


@router.get("/jobs/{job_id}", response_model=ScheduledJobOut)
async def get_job(
    job_id: int,
    controller: ScheduledJobController = Depends(get_controller)
):
    """Получить задачу по ID"""
    return controller.get_job(job_id)


@router.post("/jobs", response_model=ScheduledJobOut)
async def create_job(
    job_data: ScheduledJobCreate,
    controller: ScheduledJobController = Depends(get_controller)
):
    """Создать новую запланированную задачу"""
    return await controller.create_job(job_data)


@router.put("/jobs/{job_id}", response_model=ScheduledJobOut)
async def update_job(
    job_id: int,
    job_data: ScheduledJobUpdate,
    controller: ScheduledJobController = Depends(get_controller)
):
    """Обновить задачу"""
    return await controller.update_job(job_id, job_data)


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: int,
    controller: ScheduledJobController = Depends(get_controller)
):
    """Удалить задачу"""
    return await controller.delete_job(job_id)


@router.post("/jobs/{job_id}/activate", response_model=ScheduledJobOut)
async def activate_job(
    job_id: int,
    controller: ScheduledJobController = Depends(get_controller)
):
    """Активировать задачу"""
    return await controller.activate_job(job_id)


@router.post("/jobs/{job_id}/deactivate", response_model=ScheduledJobOut)
async def deactivate_job(
    job_id: int,
    controller: ScheduledJobController = Depends(get_controller)
):
    """Деактивировать задачу"""
    return await controller.deactivate_job(job_id)


@router.post("/jobs/{job_id}/execute", response_model=JobExecutionResult)
async def execute_job_now(
    job_id: int,
    controller: ScheduledJobController = Depends(get_controller)
):
    """Выполнить задачу немедленно"""
    return await controller.execute_now(job_id)


@router.get("/stats", response_model=ScheduledJobStats)
def get_stats(
    controller: ScheduledJobController = Depends(get_controller)
):
    """Получить статистику по запланированным задачам"""
    return controller.get_stats()


@router.get("/templates", response_model=List[JobTemplate])
def get_templates(
    controller: ScheduledJobController = Depends(get_controller)
):
    """Получить шаблоны для быстрого создания задач"""
    return controller.get_templates()


@router.get("/active-jobs")
async def get_active_jobs():
    """Получить список всех активных задач из планировщика (включая встроенные)"""
    from app.services.scheduler import task_scheduler
    return task_scheduler.get_all_jobs_info()


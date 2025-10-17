"""
Контроллеры для управления запланированными задачами
"""
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from app.external.sqlalchemy.models import ScheduledJob, User
from .models import (
    ScheduledJobCreate,
    ScheduledJobUpdate,
    ScheduledJobOut,
    ScheduledJobStats,
    JobExecutionResult,
    JOB_TEMPLATES
)


class ScheduledJobController:
    """Контроллер для работы с запланированными задачами"""
    
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
        
    def list_jobs(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        job_type: Optional[str] = None
    ) -> List[ScheduledJobOut]:
        """Получить список всех задач"""
        query = self.db.query(ScheduledJob)
        
        if is_active is not None:
            query = query.filter(ScheduledJob.is_active == is_active)
            
        if job_type:
            query = query.filter(ScheduledJob.job_type == job_type)
            
        jobs = query.offset(skip).limit(limit).all()
        return [ScheduledJobOut.model_validate(job) for job in jobs]
        
    def get_job(self, job_id: int) -> ScheduledJobOut:
        """Получить задачу по ID"""
        job = self.db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        return ScheduledJobOut.model_validate(job)
        
    async def create_job(self, job_data: ScheduledJobCreate) -> ScheduledJobOut:
        """Создать новую задачу"""
        # Проверяем, что задача с таким именем не существует
        existing = self.db.query(ScheduledJob).filter(
            ScheduledJob.name == job_data.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Задача с таким именем уже существует"
            )
            
        # Создаем задачу
        job = ScheduledJob(
            **job_data.model_dump(),
            created_by=self.current_user.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        # Добавляем задачу в планировщик
        from app.services.scheduler import task_scheduler
        import asyncio
        asyncio.create_task(task_scheduler.add_or_update_job(job.id))
        
        return ScheduledJobOut.model_validate(job)
        
    async def update_job(self, job_id: int, job_data: ScheduledJobUpdate) -> ScheduledJobOut:
        """Обновить задачу"""
        job = self.db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Задача не найдена")
            
        # Обновляем поля
        update_data = job_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job, field, value)
            
        job.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(job)
        
        # Обновляем задачу в планировщике
        from app.services.scheduler import task_scheduler
        import asyncio
        asyncio.create_task(task_scheduler.add_or_update_job(job.id))
        
        return ScheduledJobOut.model_validate(job)
        
    async def delete_job(self, job_id: int):
        """Удалить задачу"""
        job = self.db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Задача не найдена")
            
        # Удаляем из планировщика
        from app.services.scheduler import task_scheduler
        import asyncio
        asyncio.create_task(task_scheduler.remove_job(job.id))
        
        self.db.delete(job)
        self.db.commit()
        
        return {"message": "Задача успешно удалена"}
        
    async def activate_job(self, job_id: int) -> ScheduledJobOut:
        """Активировать задачу"""
        job = self.db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Задача не найдена")
            
        job.is_active = True
        job.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        
        # Добавляем в планировщик
        from app.services.scheduler import task_scheduler
        import asyncio
        asyncio.create_task(task_scheduler.add_or_update_job(job.id))
        
        return ScheduledJobOut.model_validate(job)
        
    async def deactivate_job(self, job_id: int) -> ScheduledJobOut:
        """Деактивировать задачу"""
        job = self.db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Задача не найдена")
            
        job.is_active = False
        job.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        
        # Удаляем из планировщика
        from app.services.scheduler import task_scheduler
        import asyncio
        asyncio.create_task(task_scheduler.remove_job(job.id))
        
        return ScheduledJobOut.model_validate(job)
        
    async def execute_now(self, job_id: int) -> JobExecutionResult:
        """Выполнить задачу немедленно"""
        job = self.db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Задача не найдена")
            
        # Запускаем задачу немедленно через планировщик
        from app.services.scheduler import task_scheduler
        import asyncio
        asyncio.create_task(task_scheduler._execute_job(job.id))
        
        return JobExecutionResult(
            success=True,
            message="Задача поставлена в очередь на выполнение",
            job_id=job.id,
            executed_at=datetime.now(timezone.utc)
        )
        
    def get_stats(self) -> ScheduledJobStats:
        """Получить статистику по задачам"""
        total_jobs = self.db.query(func.count(ScheduledJob.id)).scalar()
        active_jobs = self.db.query(func.count(ScheduledJob.id)).filter(
            ScheduledJob.is_active == True
        ).scalar()
        inactive_jobs = total_jobs - active_jobs
        
        total_runs = self.db.query(func.sum(ScheduledJob.run_count)).scalar() or 0
        total_errors = self.db.query(func.sum(ScheduledJob.error_count)).scalar() or 0
        
        # Группировка по типам
        jobs_by_type_query = self.db.query(
            ScheduledJob.job_type,
            func.count(ScheduledJob.id)
        ).group_by(ScheduledJob.job_type).all()
        
        jobs_by_type = {job_type: count for job_type, count in jobs_by_type_query}
        
        return ScheduledJobStats(
            total_jobs=total_jobs,
            active_jobs=active_jobs,
            inactive_jobs=inactive_jobs,
            total_runs=total_runs,
            total_errors=total_errors,
            jobs_by_type=jobs_by_type
        )
        
    def get_templates(self):
        """Получить шаблоны задач"""
        return JOB_TEMPLATES


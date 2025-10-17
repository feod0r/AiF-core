from typing import Annotated

from fastapi import APIRouter, Depends

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


status_router = APIRouter(prefix="/api", tags=["status"])


@status_router.get("/ping")
def ping():
    return "ok"


@status_router.get("/healthcheck")
async def healthcheck():
    return "ok"

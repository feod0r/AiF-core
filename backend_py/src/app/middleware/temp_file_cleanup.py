import os
from pathlib import Path
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class TempFileCleanupMiddleware(BaseHTTPMiddleware):
    """Middleware для очистки временных файлов после скачивания"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Проверяем, есть ли заголовок с временным файлом
        temp_file_path = response.headers.get("X-Temp-File")
        
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                # Удаляем временный файл после отправки ответа
                os.unlink(temp_file_path)
                print(f"✅ Cleaned up temp file: {temp_file_path}")
            except Exception as e:
                print(f"❌ Error cleaning up temp file {temp_file_path}: {e}")
        
        return response


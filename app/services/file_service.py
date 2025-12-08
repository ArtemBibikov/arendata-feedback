"""
File Upload Service for Arenadata Feedback System
Обработка загрузки и хранения файлов
"""

import os
import uuid
import aiofiles
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.models import FeedbackAttachment
from app.schemas import AttachmentCreate


class FileService:
    """Сервис для работы с файлами"""
    
    def __init__(self):
        self.upload_dir = os.getenv("UPLOAD_DIR", "uploads")
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB
        self.allowed_extensions = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
            'document': ['.pdf', '.doc', '.docx', '.txt', '.md'],
            'log': ['.log', '.txt'],
            'archive': ['.zip', '.tar', '.gz']
        }
        self.allowed_mime_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp',
            'application/pdf', 'text/plain', 'text/markdown',
            'application/zip', 'application/x-tar', 'application/gzip'
        ]
    
    def validate_file(self, file: UploadFile) -> None:
        """
        Валидация файла
        
        Args:
            file: Загружаемый файл
            
        Raises:
            HTTPException: Если файл не прошел валидацию
        """
        # Проверяем MIME тип
        if file.content_type not in self.allowed_mime_types:
            raise HTTPException(
                status_code=400,
                detail=f"Неподдерживаемый тип файла: {file.content_type}"
            )
        
        # Проверяем расширение
        file_ext = os.path.splitext(file.filename)[1].lower()
        allowed_exts = []
        for ext_list in self.allowed_extensions.values():
            allowed_exts.extend(ext_list)
        
        if file_ext not in allowed_exts:
            raise HTTPException(
                status_code=400,
                detail=f"Неподдерживаемое расширение файла: {file_ext}"
            )
    
    async def save_file(self, file: UploadFile) -> tuple[str, str]:
        """
        Сохранить файл на диск
        
        Args:
            file: Загружаемый файл
            
        Returns:
            Кортеж (имя_файла, путь_к_файлу)
        """
        # Создаем уникальное имя файла
        file_ext = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # Создаем директорию по дате
        from datetime import datetime
        date_dir = datetime.now().strftime("%Y/%m/%d")
        upload_path = os.path.join(self.upload_dir, date_dir)
        
        # Создаем директорию если нет
        os.makedirs(upload_path, exist_ok=True)
        
        # Полный путь к файлу
        file_path = os.path.join(upload_path, unique_filename)
        
        # Сохраняем файл
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            if len(content) > self.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"Файл слишком большой. Максимум: {self.max_file_size // (1024*1024)}MB"
                )
            await f.write(content)
        
        return unique_filename, file_path
    
    async def create_attachment(
        self, 
        db: Session, 
        feedback_id: int, 
        file: UploadFile
    ) -> FeedbackAttachment:
        """
        Создать запись о вложении
        
        Args:
            db: Сессия базы данных
            feedback_id: ID отзыва
            file: Загружаемый файл
            
        Returns:
            Объект вложения
        """
        # Валидация файла
        self.validate_file(file)
        
        # Сохранение файла
        filename, file_path = await self.save_file(file)
        
        # Получение размера файла
        file.seek(0, 2)  # Перемещаемся в конец файла
        file_size = file.tell()
        file.seek(0)  # Возвращаемся в начало
        
        # Создание записи в БД
        attachment_data = AttachmentCreate(
            feedback_id=feedback_id,
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            content_type=file.content_type
        )
        
        db_attachment = FeedbackAttachment(**attachment_data.dict())
        db.add(db_attachment)
        db.commit()
        db.refresh(db_attachment)
        
        return db_attachment
    
    async def create_multiple_attachments(
        self,
        db: Session,
        feedback_id: int,
        files: List[UploadFile]
    ) -> List[FeedbackAttachment]:
        """
        Создать несколько вложений
        
        Args:
            db: Сессия базы данных
            feedback_id: ID отзыва
            files: Список файлов
            
        Returns:
            Список объектов вложений
        """
        attachments = []
        
        for file in files:
            try:
                attachment = await self.create_attachment(db, feedback_id, file)
                attachments.append(attachment)
            except Exception as e:
                # Логируем ошибку, но продолжаем обработку других файлов
                print(f"Error uploading file {file.filename}: {e}")
                continue
        
        return attachments
    
    def get_feedback_attachments(self, db: Session, feedback_id: int) -> List[FeedbackAttachment]:
        """
        Получить все вложения отзыва
        
        Args:
            db: Сессия базы данных
            feedback_id: ID отзыва
            
        Returns:
            Список вложений
        """
        return db.query(FeedbackAttachment).filter(
            FeedbackAttachment.feedback_id == feedback_id
        ).all()
    
    def delete_attachment(self, db: Session, attachment_id: int) -> bool:
        """
        Удалить вложение
        
        Args:
            db: Сессия базы данных
            attachment_id: ID вложения
            
        Returns:
            True если успешно
        """
        attachment = db.query(FeedbackAttachment).filter(
            FeedbackAttachment.id == attachment_id
        ).first()
        
        if not attachment:
            return False
        
        # Удаляем файл с диска
        try:
            if os.path.exists(attachment.file_path):
                os.remove(attachment.file_path)
        except Exception as e:
            print(f"Error deleting file {attachment.file_path}: {e}")
        
        # Удаляем запись из БД
        db.delete(attachment)
        db.commit()
        
        return True


file_service = FileService()

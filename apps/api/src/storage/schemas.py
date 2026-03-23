from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class PresignUploadRequest(BaseModel):
    file_name: str
    mime_type: str
    size_bytes: int


class PresignUploadResponse(BaseModel):
    upload_url: str
    object_key: str
    expires_at: datetime


class CompleteUploadRequest(BaseModel):
    object_key: str
    file_name: str
    mime_type: str
    size_bytes: int


class FileObjectResponse(BaseModel):
    id: UUID
    object_key: str
    file_name: str
    mime_type: str
    size_bytes: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

import boto3
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from src.db.models import FileObject, Agreement

settings = get_settings()


class StorageService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.r2_endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name='auto',
        )
        self.bucket_name = settings.r2_bucket_name

    def generate_object_key(self, agreement_id: str, file_name: str) -> str:
        """Generate a unique object key for storage."""
        unique_id = uuid.uuid4().hex[:8]
        safe_name = file_name.replace(' ', '_')
        return f"agreements/{agreement_id}/{unique_id}_{safe_name}"

    def create_presigned_upload_url(
        self,
        agreement_id: str,
        file_name: str,
        mime_type: str,
        size_bytes: int,
        expires_in: int = 3600  # 1 hour
    ) -> tuple[str, str, datetime]:
        """Create a presigned URL for direct upload to R2."""
        object_key = self.generate_object_key(agreement_id, file_name)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        # Check file size limit (100MB default)
        max_size = 100 * 1024 * 1024
        if size_bytes > max_size:
            raise ValueError(f"File too large. Maximum size is {max_size // (1024*1024)}MB")

        presigned_url = self.s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': object_key,
                'ContentType': mime_type,
                'ContentLength': size_bytes,
            },
            ExpiresIn=expires_in,
        )

        return presigned_url, object_key, expires_at

    async def head_object(self, object_key: str) -> dict | None:
        """Check if object exists and get metadata."""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key,
            )
            return {
                "content_type": response.get("ContentType"),
                "content_length": response.get("ContentLength"),
                "etag": response.get("ETag", "").strip('"'),
                "last_modified": response.get("LastModified"),
            }
        except self.s3_client.exceptions.ClientError:
            return None

    async def record_file_object(
        self,
        agreement_id: str,
        object_key: str,
        file_name: str,
        mime_type: str,
        size_bytes: int,
        submission_id: str | None = None,
    ) -> FileObject:
        """Record file object metadata in database."""
        # Verify object exists in R2
        obj_meta = await self.head_object(object_key)
        if not obj_meta:
            raise ValueError("Object not found in storage")

        checksum = obj_meta.get("etag")

        file_obj = FileObject(
            agreement_id=agreement_id,
            submission_id=submission_id,
            object_key=object_key,
            file_name=file_name,
            mime_type=mime_type,
            size_bytes=size_bytes,
            checksum=checksum,
            uploaded_at=datetime.utcnow(),
        )

        self.db.add(file_obj)
        await self.db.commit()
        await self.db.refresh(file_obj)

        return file_obj

    async def get_file_object(self, object_key: str) -> FileObject | None:
        """Get file object by key."""
        result = await self.db.execute(
            select(FileObject).where(FileObject.object_key == object_key)
        )
        return result.scalar_one_or_none()

    async def get_file_objects_for_agreement(self, agreement_id: str) -> list[FileObject]:
        """Get all file objects for an agreement."""
        result = await self.db.execute(
            select(FileObject)
            .where(FileObject.agreement_id == agreement_id)
            .order_by(FileObject.created_at.desc())
        )
        return list(result.scalars().all())

    def get_public_url(self, object_key: str) -> str:
        """Get public URL for an object."""
        return f"{settings.r2_public_url}/{object_key}"

    def create_presigned_download_url(self, object_key: str, expires_in: int = 3600) -> str:
        """Create presigned URL for downloading."""
        return self.s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': object_key,
            },
            ExpiresIn=expires_in,
        )

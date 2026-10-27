"""S3 service manager with helper methods."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast
from testcontainers_aws.services.base import BaseServiceManager

if TYPE_CHECKING:
    from types_boto3_s3 import S3Client
    from types_boto3_s3.type_defs import (
        CreateBucketOutputTypeDef,
        GetObjectOutputTypeDef,
        ListBucketsOutputTypeDef,
        ObjectIdentifierTypeDef,
        PutObjectOutputTypeDef,
    )


class S3ServiceManager(BaseServiceManager):
    """Manages S3 operations and simplifies common testing tasks."""

    @property
    def client(self) -> 'S3Client':
        """Get S3 client."""
        if not self._client:
            self._client = self.environment.get_client('s3')
        return cast('S3Client', self._client)

    def create_bucket(
        self,
        bucket_name: str,
        region: Optional[str] = None,
        **kwargs: Any
    ) -> 'CreateBucketOutputTypeDef':
        """
        Create an S3 bucket.

        Args:
            bucket_name: Name of the bucket
            region: AWS region (defaults to us-east-1)
            **kwargs: Additional arguments passed to create_bucket

        Returns:
            Response from create_bucket API
        """
        create_params: Dict[str, Any] = {'Bucket': bucket_name}

        if region and region != 'us-east-1':
            create_params['CreateBucketConfiguration'] = {'LocationConstraint': region}

        create_params.update(kwargs)
        return self.client.create_bucket(**create_params)

    def put_object(
        self,
        bucket_name: str,
        key: str,
        body: Any,
        **kwargs: Any
    ) -> 'PutObjectOutputTypeDef':
        """
        Upload an object to S3.

        Args:
            bucket_name: Target bucket name
            key: Object key (path)
            body: Object content
            **kwargs: Additional arguments passed to put_object

        Returns:
            Response from put_object API
        """
        return self.client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=body,
            **kwargs
        )

    def get_object(self, bucket_name: str, key: str) -> 'GetObjectOutputTypeDef':
        """
        Retrieve an object from S3.

        Args:
            bucket_name: Source bucket name
            key: Object key (path)

        Returns:
            Response from get_object API
        """
        return self.client.get_object(Bucket=bucket_name, Key=key)

    def list_buckets(self) -> 'ListBucketsOutputTypeDef':
        """List all S3 buckets."""
        return self.client.list_buckets()

    def delete_bucket(self, bucket_name: str, force: bool = False) -> None:
        """
        Delete an S3 bucket.

        Args:
            bucket_name: Bucket to delete
            force: If True, deletes all objects in bucket first
        """
        if force:
            # Delete all objects first
            paginator = self.client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' in page:
                    objects: List['ObjectIdentifierTypeDef'] = [
                        {'Key': obj['Key']} for obj in page['Contents']
                    ]
                    self.client.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': objects}
                    )

        self.client.delete_bucket(Bucket=bucket_name)

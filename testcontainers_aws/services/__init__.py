"""AWS service managers for simplified resource management."""

from testcontainers_aws.services.s3 import S3ServiceManager
from testcontainers_aws.services.dynamodb import DynamoDBServiceManager
from testcontainers_aws.services.sqs import SQSServiceManager
from testcontainers_aws.services.kinesis import KinesisServiceManager
from testcontainers_aws.services.lambda_service import LambdaServiceManager
from testcontainers_aws.services.sns import SNSServiceManager

__all__ = [
    "S3ServiceManager",
    "DynamoDBServiceManager",
    "SQSServiceManager",
    "KinesisServiceManager",
    "LambdaServiceManager",
    "SNSServiceManager",
]

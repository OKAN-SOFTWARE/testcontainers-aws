"""SQS service manager with helper methods."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast
from testcontainers_aws.services.base import BaseServiceManager

if TYPE_CHECKING:
    from types_boto3_sqs import SQSClient
    from types_boto3_sqs.type_defs import (
        CreateQueueResultTypeDef,
        EmptyResponseMetadataTypeDef,
        MessageTypeDef,
        SendMessageResultTypeDef,
    )


class SQSServiceManager(BaseServiceManager):
    """Manages SQS operations and simplifies common testing tasks."""

    @property
    def client(self) -> 'SQSClient':
        """Get SQS client."""
        if not self._client:
            self._client = self.environment.get_client('sqs')
        return cast('SQSClient', self._client)

    def create_queue(
        self,
        queue_name: str,
        attributes: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> 'CreateQueueResultTypeDef':
        """
        Create an SQS queue.

        Args:
            queue_name: Name of the queue
            attributes: Queue attributes (e.g., VisibilityTimeout, MessageRetentionPeriod)
            **kwargs: Additional arguments passed to create_queue

        Returns:
            Response from create_queue API with QueueUrl
        """
        params: Dict[str, Any] = {'QueueName': queue_name}

        if attributes:
            params['Attributes'] = attributes

        params.update(kwargs)
        return self.client.create_queue(**params)

    def get_queue_url(self, queue_name: str) -> str:
        """
        Get the URL for a queue.

        Args:
            queue_name: Name of the queue

        Returns:
            Queue URL
        """
        response = self.client.get_queue_url(QueueName=queue_name)
        return response['QueueUrl']

    def send_message(
        self,
        queue_url: str,
        message_body: str,
        message_attributes: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> 'SendMessageResultTypeDef':
        """
        Send a message to an SQS queue.

        Args:
            queue_url: Target queue URL
            message_body: Message content
            message_attributes: Optional message attributes
            **kwargs: Additional arguments passed to send_message

        Returns:
            Response from send_message API
        """
        params: Dict[str, Any] = {
            'QueueUrl': queue_url,
            'MessageBody': message_body,
        }

        if message_attributes:
            params['MessageAttributes'] = message_attributes

        params.update(kwargs)
        return self.client.send_message(**params)

    def receive_messages(
        self,
        queue_url: str,
        max_messages: int = 1,
        wait_time_seconds: int = 0,
        **kwargs: Any
    ) -> List['MessageTypeDef']:
        """
        Receive messages from an SQS queue.

        Args:
            queue_url: Source queue URL
            max_messages: Maximum number of messages to retrieve (1-10)
            wait_time_seconds: Long polling wait time
            **kwargs: Additional arguments passed to receive_message

        Returns:
            List of messages
        """
        response = self.client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=wait_time_seconds,
            **kwargs
        )
        return response.get('Messages', [])

    def delete_message(self, queue_url: str, receipt_handle: str) -> 'EmptyResponseMetadataTypeDef':
        """
        Delete a message from an SQS queue.

        Args:
            queue_url: Queue URL
            receipt_handle: Receipt handle of the message to delete

        Returns:
            Response from delete_message API
        """
        return self.client.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )

    def purge_queue(self, queue_url: str) -> 'EmptyResponseMetadataTypeDef':
        """
        Purge all messages from a queue.

        Args:
            queue_url: Queue URL

        Returns:
            Response from purge_queue API
        """
        return self.client.purge_queue(QueueUrl=queue_url)

    def delete_queue(self, queue_url: str) -> 'EmptyResponseMetadataTypeDef':
        """
        Delete an SQS queue.

        Args:
            queue_url: Queue URL

        Returns:
            Response from delete_queue API
        """
        return self.client.delete_queue(QueueUrl=queue_url)

    def list_queues(self, prefix: Optional[str] = None) -> List[str]:
        """
        List all SQS queues.

        Args:
            prefix: Optional queue name prefix filter

        Returns:
            List of queue URLs
        """
        params: Dict[str, Any] = {}
        if prefix:
            params['QueueNamePrefix'] = prefix

        response = self.client.list_queues(**params)
        return response.get('QueueUrls', [])

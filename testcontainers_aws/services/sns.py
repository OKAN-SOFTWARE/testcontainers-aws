"""SNS service manager with helper methods."""

from typing import Any, Dict, List, Optional
from testcontainers_aws.services.base import BaseServiceManager


class SNSServiceManager(BaseServiceManager):
    """Manages SNS operations and simplifies common testing tasks."""

    @property
    def client(self) -> Any:
        """Get SNS client."""
        if not self._client:
            self._client = self.environment.get_client('sns')
        return self._client

    def create_topic(
        self,
        name: str,
        attributes: Optional[Dict[str, str]] = None,
        tags: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create an SNS topic.

        Args:
            name: Topic name
            attributes: Topic attributes (e.g., DisplayName, DeliveryPolicy)
            tags: Topic tags
            **kwargs: Additional arguments passed to create_topic

        Returns:
            Response from create_topic API with TopicArn

        Example:
            ```python
            response = manager.create_topic('notifications')
            topic_arn = response['TopicArn']
            ```
        """
        params = {'Name': name}

        if attributes:
            params['Attributes'] = attributes

        if tags:
            params['Tags'] = tags

        params.update(kwargs)
        return self.client.create_topic(**params)

    def publish(
        self,
        topic_arn: str,
        message: str,
        subject: Optional[str] = None,
        message_attributes: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Publish a message to an SNS topic.

        Args:
            topic_arn: ARN of the topic
            message: Message content
            subject: Optional subject for email notifications
            message_attributes: Optional message attributes
            **kwargs: Additional arguments passed to publish

        Returns:
            Response from publish API with MessageId

        Example:
            ```python
            response = manager.publish(
                topic_arn='arn:aws:sns:us-east-1:000000000000:my-topic',
                message='Hello from SNS!',
                subject='Test Notification'
            )
            ```
        """
        params = {
            'TopicArn': topic_arn,
            'Message': message,
        }

        if subject:
            params['Subject'] = subject

        if message_attributes:
            params['MessageAttributes'] = message_attributes

        params.update(kwargs)
        return self.client.publish(**params)

    def subscribe(
        self,
        topic_arn: str,
        protocol: str,
        endpoint: str,
        attributes: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Subscribe to an SNS topic.

        Args:
            topic_arn: ARN of the topic
            protocol: Protocol (e.g., 'sqs', 'lambda', 'email', 'http', 'https')
            endpoint: Endpoint to receive notifications (e.g., queue ARN, Lambda ARN, email)
            attributes: Subscription attributes
            **kwargs: Additional arguments passed to subscribe

        Returns:
            Response from subscribe API with SubscriptionArn

        Example:
            ```python
            # Subscribe SQS queue to SNS topic
            response = manager.subscribe(
                topic_arn='arn:aws:sns:us-east-1:000000000000:my-topic',
                protocol='sqs',
                endpoint='arn:aws:sqs:us-east-1:000000000000:my-queue'
            )
            ```
        """
        params = {
            'TopicArn': topic_arn,
            'Protocol': protocol,
            'Endpoint': endpoint,
        }

        if attributes:
            params['Attributes'] = attributes

        params.update(kwargs)
        return self.client.subscribe(**params)

    def unsubscribe(self, subscription_arn: str) -> Dict[str, Any]:
        """
        Unsubscribe from an SNS topic.

        Args:
            subscription_arn: ARN of the subscription

        Returns:
            Response from unsubscribe API
        """
        return self.client.unsubscribe(SubscriptionArn=subscription_arn)

    def list_topics(self) -> List[str]:
        """
        List all SNS topics.

        Returns:
            List of topic ARNs
        """
        response = self.client.list_topics()
        return [topic['TopicArn'] for topic in response.get('Topics', [])]

    def list_subscriptions(self) -> List[Dict[str, Any]]:
        """
        List all SNS subscriptions.

        Returns:
            List of subscriptions
        """
        response = self.client.list_subscriptions()
        return response.get('Subscriptions', [])

    def list_subscriptions_by_topic(self, topic_arn: str) -> List[Dict[str, Any]]:
        """
        List subscriptions for a specific topic.

        Args:
            topic_arn: ARN of the topic

        Returns:
            List of subscriptions for the topic
        """
        response = self.client.list_subscriptions_by_topic(TopicArn=topic_arn)
        return response.get('Subscriptions', [])

    def delete_topic(self, topic_arn: str) -> Dict[str, Any]:
        """
        Delete an SNS topic.

        Args:
            topic_arn: ARN of the topic

        Returns:
            Response from delete_topic API
        """
        return self.client.delete_topic(TopicArn=topic_arn)

    def get_topic_attributes(self, topic_arn: str) -> Dict[str, str]:
        """
        Get attributes of an SNS topic.

        Args:
            topic_arn: ARN of the topic

        Returns:
            Topic attributes
        """
        response = self.client.get_topic_attributes(TopicArn=topic_arn)
        return response.get('Attributes', {})

    def set_topic_attributes(
        self,
        topic_arn: str,
        attribute_name: str,
        attribute_value: str
    ) -> Dict[str, Any]:
        """
        Set an attribute of an SNS topic.

        Args:
            topic_arn: ARN of the topic
            attribute_name: Name of the attribute
            attribute_value: Value of the attribute

        Returns:
            Response from set_topic_attributes API
        """
        return self.client.set_topic_attributes(
            TopicArn=topic_arn,
            AttributeName=attribute_name,
            AttributeValue=attribute_value
        )

    def publish_batch(
        self,
        topic_arn: str,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Publish multiple messages to an SNS topic in a single request.

        Args:
            topic_arn: ARN of the topic
            messages: List of message entries, each with 'Id' and 'Message'
            **kwargs: Additional arguments passed to publish_batch

        Returns:
            Response from publish_batch API

        Example:
            ```python
            response = manager.publish_batch(
                topic_arn='arn:aws:sns:us-east-1:000000000000:my-topic',
                messages=[
                    {'Id': '1', 'Message': 'First message'},
                    {'Id': '2', 'Message': 'Second message'},
                ]
            )
            ```
        """
        return self.client.publish_batch(
            TopicArn=topic_arn,
            PublishBatchRequestEntries=messages,
            **kwargs
        )

    def add_permission(
        self,
        topic_arn: str,
        label: str,
        aws_account_ids: List[str],
        action_names: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Add permission to an SNS topic.

        Args:
            topic_arn: ARN of the topic
            label: Unique label for the statement
            aws_account_ids: List of AWS account IDs
            action_names: List of actions to allow (e.g., ['Publish', 'Subscribe'])
            **kwargs: Additional arguments passed to add_permission

        Returns:
            Response from add_permission API
        """
        return self.client.add_permission(
            TopicArn=topic_arn,
            Label=label,
            AWSAccountId=aws_account_ids,
            ActionName=action_names,
            **kwargs
        )

    def remove_permission(self, topic_arn: str, label: str) -> Dict[str, Any]:
        """
        Remove permission from an SNS topic.

        Args:
            topic_arn: ARN of the topic
            label: Label of the statement to remove

        Returns:
            Response from remove_permission API
        """
        return self.client.remove_permission(TopicArn=topic_arn, Label=label)

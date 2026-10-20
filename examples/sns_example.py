"""Example demonstrating SNS operations with testcontainers-aws."""

import json
from testcontainers_aws import AWSTestEnvironment


def main():
    """Demonstrate SNS topic creation, publishing, and subscriptions."""
    print("Starting AWS Test Environment with SNS and SQS...")

    with AWSTestEnvironment(services=['sns', 'sqs']) as aws:
        print(f"LocalStack running at: {aws.endpoint_url}\n")

        # Example 1: Create topic and publish message
        print("=" * 60)
        print("Example 1: Creating SNS topic and publishing")
        print("=" * 60)

        topic_response = aws.sns.create_topic('notifications')
        topic_arn = topic_response['TopicArn']
        print(f"Created topic: {topic_arn}")

        # Publish a message
        publish_response = aws.sns.publish(
            topic_arn=topic_arn,
            message='Hello from SNS!',
            subject='Test Notification'
        )
        print(f"Published message ID: {publish_response['MessageId']}\n")

        # Example 2: SNS to SQS subscription
        print("=" * 60)
        print("Example 2: SNS to SQS subscription")
        print("=" * 60)

        # Create SQS queue
        queue_response = aws.sqs.create_queue('notification-queue')
        queue_url = queue_response['QueueUrl']
        print(f"Created SQS queue: {queue_url}")

        # Get queue ARN
        sqs = aws.get_sqs_client()
        attrs = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['QueueArn']
        )
        queue_arn = attrs['Attributes']['QueueArn']

        # Subscribe SQS to SNS
        subscribe_response = aws.sns.subscribe(
            topic_arn=topic_arn,
            protocol='sqs',
            endpoint=queue_arn
        )
        print(f"Subscribed SQS to SNS: {subscribe_response['SubscriptionArn']}")

        # Publish message to topic
        aws.sns.publish(
            topic_arn=topic_arn,
            message=json.dumps({
                'event': 'user_created',
                'user_id': '12345',
                'email': 'user@example.com'
            })
        )
        print("Published message to SNS topic")

        # Receive message from SQS
        messages = aws.sqs.receive_messages(queue_url, max_messages=1, wait_time_seconds=2)
        if messages:
            body = json.loads(messages[0]['Body'])
            sns_message = json.loads(body['Message'])
            print(f"Received message from SQS: {sns_message}\n")

        # Example 3: Multiple subscriptions
        print("=" * 60)
        print("Example 3: Multiple subscriptions to one topic")
        print("=" * 60)

        # Create another queue
        queue2_response = aws.sqs.create_queue('alerts-queue')
        queue2_url = queue2_response['QueueUrl']

        attrs2 = sqs.get_queue_attributes(
            QueueUrl=queue2_url,
            AttributeNames=['QueueArn']
        )
        queue2_arn = attrs2['Attributes']['QueueArn']

        # Subscribe second queue
        aws.sns.subscribe(
            topic_arn=topic_arn,
            protocol='sqs',
            endpoint=queue2_arn
        )
        print("Subscribed second queue to SNS topic")

        # List subscriptions
        subscriptions = aws.sns.list_subscriptions_by_topic(topic_arn)
        print(f"Total subscriptions for topic: {len(subscriptions)}")
        for sub in subscriptions:
            print(f"  - {sub['Protocol']}: {sub['Endpoint']}")

        # Publish to topic (both queues will receive)
        aws.sns.publish(
            topic_arn=topic_arn,
            message='Broadcast message to all subscribers!'
        )
        print("\nPublished broadcast message")

        # Check both queues
        msgs1 = aws.sqs.receive_messages(queue_url, max_messages=1, wait_time_seconds=2)
        msgs2 = aws.sqs.receive_messages(queue2_url, max_messages=1, wait_time_seconds=2)
        print(f"Queue 1 received: {len(msgs1)} message(s)")
        print(f"Queue 2 received: {len(msgs2)} message(s)\n")

        # Example 4: Batch publishing
        print("=" * 60)
        print("Example 4: Batch publishing to SNS")
        print("=" * 60)

        batch_response = aws.sns.publish_batch(
            topic_arn=topic_arn,
            messages=[
                {'Id': '1', 'Message': 'First batch message'},
                {'Id': '2', 'Message': 'Second batch message'},
                {'Id': '3', 'Message': 'Third batch message'},
            ]
        )
        print(f"Published {len(batch_response.get('Successful', []))} messages in batch")

        # Example 5: Topic attributes
        print("\n" + "=" * 60)
        print("Example 5: Managing topic attributes")
        print("=" * 60)

        attributes = aws.sns.get_topic_attributes(topic_arn)
        print("Topic attributes:")
        for key, value in attributes.items():
            if key in ['TopicArn', 'DisplayName', 'SubscriptionsConfirmed']:
                print(f"  {key}: {value}")

        # Set display name
        aws.sns.set_topic_attributes(
            topic_arn=topic_arn,
            attribute_name='DisplayName',
            attribute_value='Test Notifications'
        )
        print("\nSet DisplayName attribute")

        # List all topics
        print("\n" + "=" * 60)
        print("All SNS topics:")
        print("=" * 60)
        topics = aws.sns.list_topics()
        for topic in topics:
            print(f"  - {topic}")

        print("\nSNS examples completed successfully!")


if __name__ == '__main__':
    main()

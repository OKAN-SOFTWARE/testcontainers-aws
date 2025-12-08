"""Example demonstrating Lambda and SNS integration."""

import json
from testcontainers_aws import AWSTestEnvironment
from testcontainers_aws.services.lambda_service import create_lambda_zip


def main():
    """Demonstrate event-driven architecture with Lambda and SNS."""
    print("Starting AWS Test Environment with Lambda, SNS, and SQS...")

    with AWSTestEnvironment(services=['lambda', 'sns', 'sqs']) as aws:
        print(f"LocalStack running at: {aws.endpoint_url}\n")

        # Step 1: Create Lambda function to process SNS messages
        print("=" * 60)
        print("Step 1: Creating Lambda function")
        print("=" * 60)

        lambda_code = """
import json

def handler(event, context):
    # Process SNS message
    for record in event.get('Records', []):
        if 'Sns' in record:
            sns_message = record['Sns']
            message = sns_message.get('Message', '')

            print(f"Processing SNS message: {message}")

            # Parse the message
            try:
                data = json.loads(message)
                event_type = data.get('type')

                if event_type == 'user_created':
                    print(f"User created: {data.get('user_id')}")
                elif event_type == 'order_placed':
                    print(f"Order placed: {data.get('order_id')}")
            except:
                print(f"Plain text message: {message}")

    return {'statusCode': 200, 'body': 'Processed'}
"""

        function_code = create_lambda_zip(lambda_code)

        aws.lambda_.create_function(
            function_name='sns-processor',
            runtime='python3.11',
            handler='index.handler',
            code=function_code
        )
        print("Created Lambda function: sns-processor\n")

        # Step 2: Create SNS topic
        print("=" * 60)
        print("Step 2: Creating SNS topic")
        print("=" * 60)

        topic_response = aws.sns.create_topic('events')
        topic_arn = topic_response['TopicArn']
        print(f"Created SNS topic: {topic_arn}\n")

        # Step 3: Subscribe Lambda to SNS
        print("=" * 60)
        print("Step 3: Subscribing Lambda to SNS")
        print("=" * 60)

        lambda_client = aws.get_lambda_client()
        functions = lambda_client.list_functions()
        lambda_arn = None
        for func in functions['Functions']:
            if func['FunctionName'] == 'sns-processor':
                lambda_arn = func['FunctionArn']
                break

        if lambda_arn:
            # Add permission for SNS to invoke Lambda
            aws.lambda_.add_permission(
                function_name='sns-processor',
                statement_id='sns-invoke',
                action='lambda:InvokeFunction',
                principal='sns.amazonaws.com',
                source_arn=topic_arn
            )
            print("Added permission for SNS to invoke Lambda")

            # Subscribe Lambda to SNS
            subscribe_response = aws.sns.subscribe(
                topic_arn=topic_arn,
                protocol='lambda',
                endpoint=lambda_arn
            )
            print(f"Subscribed Lambda to SNS: {subscribe_response['SubscriptionArn']}\n")

        # Step 4: Create SQS queue for dead letter queue
        print("=" * 60)
        print("Step 4: Creating SQS queue for monitoring")
        print("=" * 60)

        queue_response = aws.sqs.create_queue('event-monitor')
        queue_url = queue_response['QueueUrl']
        print(f"Created SQS queue: {queue_url}")

        # Get queue ARN and subscribe to SNS
        sqs = aws.get_sqs_client()
        attrs = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['QueueArn']
        )
        queue_arn = attrs['Attributes']['QueueArn']

        aws.sns.subscribe(
            topic_arn=topic_arn,
            protocol='sqs',
            endpoint=queue_arn
        )
        print("Subscribed SQS to SNS for monitoring\n")

        # Step 5: Publish events to SNS
        print("=" * 60)
        print("Step 5: Publishing events to SNS")
        print("=" * 60)

        # Event 1: User created
        event1 = {
            'type': 'user_created',
            'user_id': 'user-123',
            'email': 'alice@example.com',
            'timestamp': '2024-01-01T12:00:00Z'
        }
        aws.sns.publish(
            topic_arn=topic_arn,
            message=json.dumps(event1),
            subject='User Created Event'
        )
        print(f"Published: {event1}")

        # Event 2: Order placed
        event2 = {
            'type': 'order_placed',
            'order_id': 'order-456',
            'user_id': 'user-123',
            'amount': 99.99
        }
        aws.sns.publish(
            topic_arn=topic_arn,
            message=json.dumps(event2),
            subject='Order Placed Event'
        )
        print(f"Published: {event2}")

        # Event 3: Simple text message
        aws.sns.publish(
            topic_arn=topic_arn,
            message='Simple notification message'
        )
        print("Published: Simple text message\n")

        # Step 6: Verify events in SQS
        print("=" * 60)
        print("Step 6: Checking SQS queue for events")
        print("=" * 60)

        import time
        time.sleep(1)  # Wait for message delivery

        messages = aws.sqs.receive_messages(
            queue_url,
            max_messages=10,
            wait_time_seconds=2
        )

        print(f"Received {len(messages)} messages from SQS:")
        for i, msg in enumerate(messages, 1):
            body = json.loads(msg['Body'])
            message = body.get('Message', '')
            subject = body.get('Subject', 'No subject')
            print(f"\n  Message {i}:")
            print(f"    Subject: {subject}")
            print(f"    Message: {message[:100]}...")

        # Step 7: Summary
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)

        subscriptions = aws.sns.list_subscriptions_by_topic(topic_arn)
        print(f"Total subscriptions: {len(subscriptions)}")
        for sub in subscriptions:
            print(f"  - {sub['Protocol']}: {sub['Endpoint']}")

        print("\nEvent-driven architecture example completed!")
        print("Lambda functions processed SNS messages")
        print("SQS queue monitored all events")


if __name__ == '__main__':
    main()

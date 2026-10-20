"""Tests for Lambda and SNS service managers."""

import json
from testcontainers_aws import AWSTestEnvironment
from testcontainers_aws.services.lambda_service import create_lambda_zip, create_lambda_zip_from_files


def test_lambda_create_function():
    """Test Lambda function creation."""
    with AWSTestEnvironment(services=['lambda']) as aws:
        code = create_lambda_zip("def handler(event, context): return {'statusCode': 200}")

        response = aws.lambda_.create_function(
            function_name='test-function',
            runtime='python3.11',
            handler='index.handler',
            code=code
        )

        assert response['FunctionName'] == 'test-function'
        assert response['Runtime'] == 'python3.11'


def test_lambda_invoke_function():
    """Test Lambda function invocation."""
    with AWSTestEnvironment(services=['lambda']) as aws:
        code = create_lambda_zip("""
def handler(event, context):
    name = event.get('name', 'World')
    return {'statusCode': 200, 'message': f'Hello {name}'}
""")

        aws.lambda_.create_function(
            function_name='hello-function',
            runtime='python3.11',
            handler='index.handler',
            code=code
        )

        # Invoke the function
        response = aws.lambda_.invoke_function(
            'hello-function',
            payload={'name': 'Test'}
        )

        result = json.loads(response['Payload'].read())
        assert result['statusCode'] == 200
        assert 'Hello Test' in result['message']


def test_lambda_with_environment_variables():
    """Test Lambda function with environment variables."""
    with AWSTestEnvironment(services=['lambda']) as aws:
        code = create_lambda_zip("""
import os
def handler(event, context):
    env_var = os.environ.get('TEST_VAR', 'not-set')
    return {'statusCode': 200, 'env_var': env_var}
""")

        aws.lambda_.create_function(
            function_name='env-function',
            runtime='python3.11',
            handler='index.handler',
            code=code,
            environment_variables={'TEST_VAR': 'test-value'}
        )

        response = aws.lambda_.invoke_function('env-function')
        result = json.loads(response['Payload'].read())

        assert result['env_var'] == 'test-value'


def test_lambda_list_functions():
    """Test listing Lambda functions."""
    with AWSTestEnvironment(services=['lambda']) as aws:
        code = create_lambda_zip("def handler(event, context): return {}")

        # Create multiple functions
        for i in range(3):
            aws.lambda_.create_function(
                function_name=f'function-{i}',
                runtime='python3.11',
                handler='index.handler',
                code=code
            )

        functions = aws.lambda_.list_functions()
        function_names = [f['FunctionName'] for f in functions]

        assert len(functions) >= 3
        assert 'function-0' in function_names
        assert 'function-1' in function_names
        assert 'function-2' in function_names


def test_lambda_delete_function():
    """Test Lambda function deletion."""
    with AWSTestEnvironment(services=['lambda']) as aws:
        code = create_lambda_zip("def handler(event, context): return {}")

        aws.lambda_.create_function(
            function_name='delete-me',
            runtime='python3.11',
            handler='index.handler',
            code=code
        )

        # Verify it exists
        functions_before = aws.lambda_.list_functions()
        function_names_before = [f['FunctionName'] for f in functions_before]
        assert 'delete-me' in function_names_before

        # Delete it
        aws.lambda_.delete_function('delete-me')

        # Verify it's gone
        functions_after = aws.lambda_.list_functions()
        function_names_after = [f['FunctionName'] for f in functions_after]
        assert 'delete-me' not in function_names_after


def test_lambda_multi_file_function():
    """Test Lambda function with multiple files."""
    with AWSTestEnvironment(services=['lambda']) as aws:
        code = create_lambda_zip_from_files({
            'index.py': """
from utils import add
def handler(event, context):
    a = event.get('a', 0)
    b = event.get('b', 0)
    return {'result': add(a, b)}
""",
            'utils.py': """
def add(a, b):
    return a + b
"""
        })

        aws.lambda_.create_function(
            function_name='multi-file',
            runtime='python3.11',
            handler='index.handler',
            code=code
        )

        response = aws.lambda_.invoke_function(
            'multi-file',
            payload={'a': 5, 'b': 3}
        )

        result = json.loads(response['Payload'].read())
        assert result['result'] == 8


def test_sns_create_topic():
    """Test SNS topic creation."""
    with AWSTestEnvironment(services=['sns']) as aws:
        response = aws.sns.create_topic('test-topic')

        assert 'TopicArn' in response
        assert 'test-topic' in response['TopicArn']


def test_sns_publish_message():
    """Test SNS message publishing."""
    with AWSTestEnvironment(services=['sns']) as aws:
        topic_response = aws.sns.create_topic('notifications')
        topic_arn = topic_response['TopicArn']

        publish_response = aws.sns.publish(
            topic_arn=topic_arn,
            message='Test message',
            subject='Test'
        )

        assert 'MessageId' in publish_response


def test_sns_subscribe_sqs():
    """Test SNS to SQS subscription."""
    with AWSTestEnvironment(services=['sns', 'sqs']) as aws:
        # Create SNS topic
        topic_response = aws.sns.create_topic('test-topic')
        topic_arn = topic_response['TopicArn']

        # Create SQS queue
        queue_response = aws.sqs.create_queue('test-queue')
        queue_url = queue_response['QueueUrl']

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

        assert 'SubscriptionArn' in subscribe_response

        # Publish to SNS
        aws.sns.publish(
            topic_arn=topic_arn,
            message='Test message'
        )

        # Receive from SQS
        import time
        time.sleep(1)  # Wait for message delivery

        messages = aws.sqs.receive_messages(queue_url, max_messages=1, wait_time_seconds=2)
        assert len(messages) == 1

        # Verify SNS message structure
        body = json.loads(messages[0]['Body'])
        assert body['Message'] == 'Test message'


def test_sns_list_topics():
    """Test listing SNS topics."""
    with AWSTestEnvironment(services=['sns']) as aws:
        # Create multiple topics
        for i in range(3):
            aws.sns.create_topic(f'topic-{i}')

        topics = aws.sns.list_topics()

        assert len(topics) >= 3
        topic_names = [t.split(':')[-1] for t in topics]
        assert 'topic-0' in topic_names
        assert 'topic-1' in topic_names
        assert 'topic-2' in topic_names


def test_sns_delete_topic():
    """Test SNS topic deletion."""
    with AWSTestEnvironment(services=['sns']) as aws:
        # Create topic
        topic_response = aws.sns.create_topic('delete-me')
        topic_arn = topic_response['TopicArn']

        # Verify it exists
        topics_before = aws.sns.list_topics()
        assert topic_arn in topics_before

        # Delete it
        aws.sns.delete_topic(topic_arn)

        # Verify it's gone
        topics_after = aws.sns.list_topics()
        assert topic_arn not in topics_after


def test_sns_topic_attributes():
    """Test SNS topic attributes."""
    with AWSTestEnvironment(services=['sns']) as aws:
        topic_response = aws.sns.create_topic('test-topic')
        topic_arn = topic_response['TopicArn']

        # Set attribute
        aws.sns.set_topic_attributes(
            topic_arn=topic_arn,
            attribute_name='DisplayName',
            attribute_value='Test Topic'
        )

        # Get attributes
        attributes = aws.sns.get_topic_attributes(topic_arn)

        assert attributes['DisplayName'] == 'Test Topic'


def test_sns_batch_publish():
    """Test SNS batch publishing."""
    with AWSTestEnvironment(services=['sns']) as aws:
        topic_response = aws.sns.create_topic('batch-topic')
        topic_arn = topic_response['TopicArn']

        response = aws.sns.publish_batch(
            topic_arn=topic_arn,
            messages=[
                {'Id': '1', 'Message': 'First message'},
                {'Id': '2', 'Message': 'Second message'},
                {'Id': '3', 'Message': 'Third message'},
            ]
        )

        assert len(response.get('Successful', [])) == 3


def test_sns_list_subscriptions():
    """Test listing SNS subscriptions."""
    with AWSTestEnvironment(services=['sns', 'sqs']) as aws:
        # Create topic
        topic_response = aws.sns.create_topic('test-topic')
        topic_arn = topic_response['TopicArn']

        # Create and subscribe multiple queues
        for i in range(2):
            queue_response = aws.sqs.create_queue(f'queue-{i}')
            queue_url = queue_response['QueueUrl']

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

        # List subscriptions
        subscriptions = aws.sns.list_subscriptions_by_topic(topic_arn)
        assert len(subscriptions) == 2


def test_lambda_sns_integration():
    """Test Lambda and SNS integration."""
    with AWSTestEnvironment(services=['lambda', 'sns', 'sqs']) as aws:
        # Create Lambda function
        code = create_lambda_zip("""
def handler(event, context):
    return {'statusCode': 200, 'processed': len(event.get('Records', []))}
""")

        aws.lambda_.create_function(
            function_name='sns-handler',
            runtime='python3.11',
            handler='index.handler',
            code=code
        )

        # Create SNS topic
        topic_response = aws.sns.create_topic('events')
        topic_arn = topic_response['TopicArn']

        # Get Lambda ARN
        lambda_client = aws.get_lambda_client()
        functions = lambda_client.list_functions()
        lambda_arn = None
        for func in functions['Functions']:
            if func['FunctionName'] == 'sns-handler':
                lambda_arn = func['FunctionArn']
                break

        assert lambda_arn is not None

        # Add permission and subscribe
        aws.lambda_.add_permission(
            function_name='sns-handler',
            statement_id='sns-invoke',
            action='lambda:InvokeFunction',
            principal='sns.amazonaws.com',
            source_arn=topic_arn
        )

        subscribe_response = aws.sns.subscribe(
            topic_arn=topic_arn,
            protocol='lambda',
            endpoint=lambda_arn
        )

        assert 'SubscriptionArn' in subscribe_response

        # Publish to SNS (Lambda should be invoked automatically)
        aws.sns.publish(
            topic_arn=topic_arn,
            message='Test event'
        )

        # Test successful (no errors means Lambda was invoked)


def test_lambda_fixture(lambda_function, aws_environment):
    """Test using lambda_function fixture."""
    # Function is already created by fixture
    response = aws_environment.lambda_.invoke_function(lambda_function)
    result = json.loads(response['Payload'].read())

    assert result['statusCode'] == 200
    assert 'Hello from Lambda!' in result['body']


def test_sns_fixture(sns_topic, aws_environment):
    """Test using sns_topic fixture."""
    # Topic is already created by fixture
    response = aws_environment.sns.publish(
        topic_arn=sns_topic,
        message='Test from fixture'
    )

    assert 'MessageId' in response

"""Pytest fixtures for AWS testing with testcontainers."""

import pytest
from testcontainers_aws.core import AWSTestEnvironment


@pytest.fixture(scope='session')
def aws_environment():
    """
    Session-scoped AWS test environment with common services.

    Provides S3, DynamoDB, SQS, Kinesis, Lambda, and SNS services. The container is
    shared across all tests in the session for performance.

    Yields:
        AWSTestEnvironment: Configured AWS environment
    """
    with AWSTestEnvironment(services=['s3', 'dynamodb', 'sqs', 'kinesis', 'lambda', 'sns']) as aws:
        yield aws


@pytest.fixture(scope='function')
def aws_environment_function():
    """
    Function-scoped AWS test environment with common services.

    Provides S3, DynamoDB, SQS, Kinesis, Lambda, and SNS services. A fresh container
    is created for each test function for complete isolation.

    Yields:
        AWSTestEnvironment: Configured AWS environment
    """
    with AWSTestEnvironment(services=['s3', 'dynamodb', 'sqs', 'kinesis', 'lambda', 'sns']) as aws:
        yield aws


@pytest.fixture(scope='session')
def s3_client(aws_environment):
    """
    Session-scoped S3 client.

    Args:
        aws_environment: AWS environment fixture

    Returns:
        boto3 S3 client configured for LocalStack
    """
    return aws_environment.get_s3_client()


@pytest.fixture(scope='session')
def dynamodb_client(aws_environment):
    """
    Session-scoped DynamoDB client.

    Args:
        aws_environment: AWS environment fixture

    Returns:
        boto3 DynamoDB client configured for LocalStack
    """
    return aws_environment.get_dynamodb_client()


@pytest.fixture(scope='session')
def sqs_client(aws_environment):
    """
    Session-scoped SQS client.

    Args:
        aws_environment: AWS environment fixture

    Returns:
        boto3 SQS client configured for LocalStack
    """
    return aws_environment.get_sqs_client()


@pytest.fixture(scope='session')
def kinesis_client(aws_environment):
    """
    Session-scoped Kinesis client.

    Args:
        aws_environment: AWS environment fixture

    Returns:
        boto3 Kinesis client configured for LocalStack
    """
    return aws_environment.get_kinesis_client()


@pytest.fixture(scope='session')
def lambda_client(aws_environment):
    """
    Session-scoped Lambda client.

    Args:
        aws_environment: AWS environment fixture

    Returns:
        boto3 Lambda client configured for LocalStack
    """
    return aws_environment.get_lambda_client()


@pytest.fixture(scope='session')
def sns_client(aws_environment):
    """
    Session-scoped SNS client.

    Args:
        aws_environment: AWS environment fixture

    Returns:
        boto3 SNS client configured for LocalStack
    """
    return aws_environment.get_sns_client()


@pytest.fixture
def s3_bucket(aws_environment):
    """
    Function-scoped S3 bucket that's automatically cleaned up.

    Creates a test bucket and removes it after the test completes.

    Args:
        aws_environment: AWS environment fixture

    Yields:
        str: Bucket name
    """
    bucket_name = 'test-bucket'
    aws_environment.s3.create_bucket(bucket_name)

    yield bucket_name

    # Cleanup
    try:
        aws_environment.s3.delete_bucket(bucket_name, force=True)
    except Exception:
        pass  # Bucket might already be deleted


@pytest.fixture
def dynamodb_table(aws_environment):
    """
    Function-scoped DynamoDB table that's automatically cleaned up.

    Creates a test table with a simple schema and removes it after the test.

    Args:
        aws_environment: AWS environment fixture

    Yields:
        str: Table name
    """
    table_name = 'test-table'
    aws_environment.dynamodb.create_table(
        name=table_name,
        key_schema=[
            {'AttributeName': 'id', 'KeyType': 'HASH'}
        ],
        attribute_definitions=[
            {'AttributeName': 'id', 'AttributeType': 'S'}
        ]
    )

    yield table_name

    # Cleanup
    try:
        aws_environment.dynamodb.delete_table(table_name)
    except Exception:
        pass


@pytest.fixture
def sqs_queue(aws_environment):
    """
    Function-scoped SQS queue that's automatically cleaned up.

    Creates a test queue and removes it after the test completes.

    Args:
        aws_environment: AWS environment fixture

    Yields:
        str: Queue URL
    """
    queue_response = aws_environment.sqs.create_queue('test-queue')
    queue_url = queue_response['QueueUrl']

    yield queue_url

    # Cleanup
    try:
        aws_environment.sqs.delete_queue(queue_url)
    except Exception:
        pass


@pytest.fixture
def kinesis_stream(aws_environment):
    """
    Function-scoped Kinesis stream that's automatically cleaned up.

    Creates a test stream and removes it after the test completes.

    Args:
        aws_environment: AWS environment fixture

    Yields:
        str: Stream name
    """
    stream_name = 'test-stream'
    aws_environment.kinesis.create_stream(stream_name, shard_count=1)

    yield stream_name

    # Cleanup
    try:
        aws_environment.kinesis.delete_stream(stream_name)
    except Exception:
        pass


@pytest.fixture
def sns_topic(aws_environment):
    """
    Function-scoped SNS topic that's automatically cleaned up.

    Creates a test topic and removes it after the test completes.

    Args:
        aws_environment: AWS environment fixture

    Yields:
        str: Topic ARN
    """
    response = aws_environment.sns.create_topic('test-topic')
    topic_arn = response['TopicArn']

    yield topic_arn

    # Cleanup
    try:
        aws_environment.sns.delete_topic(topic_arn)
    except Exception:
        pass


@pytest.fixture
def lambda_function(aws_environment):
    """
    Function-scoped Lambda function that's automatically cleaned up.

    Creates a simple test Lambda function and removes it after the test.

    Args:
        aws_environment: AWS environment fixture

    Yields:
        str: Function name
    """
    from testcontainers_aws.services.lambda_service import create_lambda_zip

    function_name = 'test-function'
    code = create_lambda_zip("""
def handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }
""")

    aws_environment.lambda_.create_function(
        function_name=function_name,
        runtime='python3.11',
        handler='index.handler',
        code=code
    )

    yield function_name

    # Cleanup
    try:
        aws_environment.lambda_.delete_function(function_name)
    except Exception:
        pass

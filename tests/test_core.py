"""Tests for core AWSTestEnvironment functionality."""

import pytest
from testcontainers_aws import AWSTestEnvironment


def test_aws_environment_context_manager():
    """Test that AWSTestEnvironment works as a context manager."""
    with AWSTestEnvironment(services=['s3']) as aws:
        assert aws is not None
        assert aws.endpoint_url is not None


def test_get_s3_client():
    """Test getting an S3 client."""
    with AWSTestEnvironment(services=['s3']) as aws:
        client = aws.get_s3_client()
        assert client is not None

        # Test that it works
        response = client.list_buckets()
        assert 'Buckets' in response


def test_get_dynamodb_client():
    """Test getting a DynamoDB client."""
    with AWSTestEnvironment(services=['dynamodb']) as aws:
        client = aws.get_dynamodb_client()
        assert client is not None

        # Test that it works
        response = client.list_tables()
        assert 'TableNames' in response


def test_multiple_services():
    """Test initializing multiple services."""
    with AWSTestEnvironment(services=['s3', 'dynamodb', 'sqs']) as aws:
        s3 = aws.get_s3_client()
        dynamodb = aws.get_dynamodb_client()
        sqs = aws.get_sqs_client()

        assert s3 is not None
        assert dynamodb is not None
        assert sqs is not None


def test_auto_init_s3_buckets():
    """Test auto-initialization of S3 buckets."""
    with AWSTestEnvironment(
        services=['s3'],
        init_config={'s3_buckets': ['test-bucket-1', 'test-bucket-2']}
    ) as aws:
        s3 = aws.get_s3_client()
        buckets = [b['Name'] for b in s3.list_buckets()['Buckets']]

        assert 'test-bucket-1' in buckets
        assert 'test-bucket-2' in buckets


def test_auto_init_dynamodb_tables():
    """Test auto-initialization of DynamoDB tables."""
    with AWSTestEnvironment(
        services=['dynamodb'],
        init_config={
            'dynamodb_tables': [
                {
                    'name': 'test-table',
                    'key_schema': [{'AttributeName': 'id', 'KeyType': 'HASH'}],
                    'attribute_definitions': [{'AttributeName': 'id', 'AttributeType': 'S'}]
                }
            ]
        }
    ) as aws:
        dynamodb = aws.get_dynamodb_client()
        tables = dynamodb.list_tables()['TableNames']

        assert 'test-table' in tables


def test_auto_init_sqs_queues():
    """Test auto-initialization of SQS queues."""
    with AWSTestEnvironment(
        services=['sqs'],
        init_config={'sqs_queues': ['queue1', 'queue2']}
    ) as aws:
        queues = aws.sqs.list_queues()
        queue_names = [q.split('/')[-1] for q in queues]

        assert 'queue1' in queue_names
        assert 'queue2' in queue_names


def test_service_managers_accessible():
    """Test that service managers are accessible via properties."""
    with AWSTestEnvironment(services=['s3', 'dynamodb', 'sqs', 'kinesis']) as aws:
        assert aws.s3 is not None
        assert aws.dynamodb is not None
        assert aws.sqs is not None
        assert aws.kinesis is not None


def test_start_stop_manually():
    """Test manual start/stop of environment."""
    aws = AWSTestEnvironment(services=['s3'])

    # Start
    aws.start()
    assert aws.endpoint_url is not None

    # Use it
    client = aws.get_s3_client()
    response = client.list_buckets()
    assert 'Buckets' in response

    # Stop
    aws.stop()

"""Tests for AWS service managers."""

import pytest
from testcontainers_aws import AWSTestEnvironment


def test_s3_create_bucket():
    """Test S3 bucket creation."""
    with AWSTestEnvironment(services=['s3']) as aws:
        aws.s3.create_bucket('test-bucket')

        buckets = aws.s3.list_buckets()
        bucket_names = [b['Name'] for b in buckets['Buckets']]
        assert 'test-bucket' in bucket_names


def test_s3_put_get_object():
    """Test S3 object operations."""
    with AWSTestEnvironment(services=['s3']) as aws:
        aws.s3.create_bucket('test-bucket')
        aws.s3.put_object('test-bucket', 'test.txt', b'Hello World')

        response = aws.s3.get_object('test-bucket', 'test.txt')
        content = response['Body'].read()
        assert content == b'Hello World'


def test_s3_delete_bucket_force():
    """Test S3 bucket deletion with force flag."""
    with AWSTestEnvironment(services=['s3']) as aws:
        aws.s3.create_bucket('test-bucket')
        aws.s3.put_object('test-bucket', 'file1.txt', b'data1')
        aws.s3.put_object('test-bucket', 'file2.txt', b'data2')

        # Should delete bucket and all objects
        aws.s3.delete_bucket('test-bucket', force=True)

        buckets = aws.s3.list_buckets()
        bucket_names = [b['Name'] for b in buckets['Buckets']]
        assert 'test-bucket' not in bucket_names


def test_dynamodb_create_table():
    """Test DynamoDB table creation."""
    with AWSTestEnvironment(services=['dynamodb']) as aws:
        aws.dynamodb.create_table(
            name='users',
            key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            attribute_definitions=[{'AttributeName': 'id', 'AttributeType': 'S'}]
        )

        tables = aws.dynamodb.list_tables()
        assert 'users' in tables


def test_dynamodb_put_get_item():
    """Test DynamoDB item operations."""
    with AWSTestEnvironment(services=['dynamodb']) as aws:
        aws.dynamodb.create_table(
            name='users',
            key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            attribute_definitions=[{'AttributeName': 'id', 'AttributeType': 'S'}]
        )

        # Put item
        aws.dynamodb.put_item('users', {
            'id': {'S': '123'},
            'name': {'S': 'Alice'}
        })

        # Get item
        response = aws.dynamodb.get_item('users', {'id': {'S': '123'}})
        assert response['Item']['name']['S'] == 'Alice'


def test_sqs_create_queue():
    """Test SQS queue creation."""
    with AWSTestEnvironment(services=['sqs']) as aws:
        response = aws.sqs.create_queue('test-queue')

        assert 'QueueUrl' in response
        assert 'test-queue' in response['QueueUrl']


def test_sqs_send_receive_message():
    """Test SQS message operations."""
    with AWSTestEnvironment(services=['sqs']) as aws:
        response = aws.sqs.create_queue('test-queue')
        queue_url = response['QueueUrl']

        # Send message
        aws.sqs.send_message(queue_url, 'Test message')

        # Receive message
        messages = aws.sqs.receive_messages(queue_url, max_messages=1)
        assert len(messages) == 1
        assert messages[0]['Body'] == 'Test message'


def test_kinesis_create_stream():
    """Test Kinesis stream creation."""
    with AWSTestEnvironment(services=['kinesis']) as aws:
        aws.kinesis.create_stream('test-stream', shard_count=1)

        streams = aws.kinesis.list_streams()
        assert 'test-stream' in streams


def test_kinesis_put_get_record():
    """Test Kinesis record operations."""
    with AWSTestEnvironment(services=['kinesis']) as aws:
        aws.kinesis.create_stream('test-stream', shard_count=1)

        # Put record
        response = aws.kinesis.put_record(
            'test-stream',
            b'test data',
            partition_key='key1'
        )

        assert 'ShardId' in response
        assert 'SequenceNumber' in response


def test_multiple_services_integration():
    """Test integration of multiple services."""
    with AWSTestEnvironment(services=['s3', 'dynamodb', 'sqs']) as aws:
        # Create resources in each service
        aws.s3.create_bucket('data-bucket')
        aws.dynamodb.create_table(
            name='metadata',
            key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            attribute_definitions=[{'AttributeName': 'id', 'AttributeType': 'S'}]
        )
        queue_response = aws.sqs.create_queue('processing')

        # Use them together
        aws.s3.put_object('data-bucket', 'file.json', b'{"data": "test"}')
        aws.dynamodb.put_item('metadata', {'id': {'S': '1'}, 'processed': {'BOOL': False}})
        aws.sqs.send_message(queue_response['QueueUrl'], 'Process file.json')

        # Verify
        s3_objects = aws.get_s3_client().list_objects_v2(Bucket='data-bucket')
        assert s3_objects['KeyCount'] == 1

        dynamodb_items = aws.dynamodb.scan('metadata')
        assert len(dynamodb_items['Items']) == 1

        sqs_messages = aws.sqs.receive_messages(queue_response['QueueUrl'])
        assert len(sqs_messages) == 1

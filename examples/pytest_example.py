"""Example pytest tests using testcontainers-aws fixtures."""

import pytest
from testcontainers_aws.fixtures import aws_environment, s3_bucket, dynamodb_table


def test_s3_with_environment(aws_environment):
    """Test S3 operations using session-scoped environment."""
    # Create bucket
    aws_environment.s3.create_bucket('test-uploads')

    # Upload file
    aws_environment.s3.put_object('test-uploads', 'data.txt', b'test data')

    # Verify
    s3 = aws_environment.get_s3_client()
    response = s3.get_object(Bucket='test-uploads', Key='data.txt')
    assert response['Body'].read() == b'test data'

    # Cleanup
    aws_environment.s3.delete_bucket('test-uploads', force=True)


def test_s3_with_auto_bucket(s3_bucket, aws_environment):
    """Test with auto-created and cleaned-up bucket."""
    # Bucket already exists and will be cleaned up automatically
    aws_environment.s3.put_object(s3_bucket, 'file.txt', b'content')

    s3 = aws_environment.get_s3_client()
    objects = s3.list_objects_v2(Bucket=s3_bucket)
    assert objects['KeyCount'] == 1


def test_dynamodb_with_auto_table(dynamodb_table, aws_environment):
    """Test with auto-created and cleaned-up DynamoDB table."""
    # Table already exists with schema: id (String, HASH)
    aws_environment.dynamodb.put_item(
        dynamodb_table,
        {'id': {'S': 'user-123'}, 'name': {'S': 'Alice'}}
    )

    # Query the item
    response = aws_environment.dynamodb.get_item(
        dynamodb_table,
        {'id': {'S': 'user-123'}}
    )

    assert response['Item']['name']['S'] == 'Alice'


def test_multiple_services(aws_environment):
    """Test orchestration of multiple AWS services."""
    # S3
    aws_environment.s3.create_bucket('data-bucket')
    aws_environment.s3.put_object('data-bucket', 'test.json', b'{"key": "value"}')

    # DynamoDB
    aws_environment.dynamodb.create_table(
        name='records',
        key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        attribute_definitions=[{'AttributeName': 'id', 'AttributeType': 'S'}]
    )
    aws_environment.dynamodb.put_item('records', {'id': {'S': '1'}, 'status': {'S': 'active'}})

    # SQS
    queue_response = aws_environment.sqs.create_queue('processing-queue')
    queue_url = queue_response['QueueUrl']
    aws_environment.sqs.send_message(queue_url, 'Process data')

    # Verify all services are working
    s3 = aws_environment.get_s3_client()
    assert s3.list_buckets()['Buckets']

    dynamodb = aws_environment.get_dynamodb_client()
    assert 'records' in dynamodb.list_tables()['TableNames']

    sqs = aws_environment.get_sqs_client()
    messages = aws_environment.sqs.receive_messages(queue_url)
    assert len(messages) == 1

    # Cleanup
    aws_environment.s3.delete_bucket('data-bucket', force=True)
    aws_environment.dynamodb.delete_table('records')
    aws_environment.sqs.delete_queue(queue_url)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

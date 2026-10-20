"""Example of auto-initialization with testcontainers-aws."""

from testcontainers_aws import AWSTestEnvironment


def main():
    """Demonstrate automatic resource initialization."""
    print("Starting AWS Test Environment with auto-initialization...")

    # Define all resources upfront
    with AWSTestEnvironment(
        services=['s3', 'dynamodb', 'sqs', 'kinesis'],
        init_config={
            's3_buckets': [
                'uploads',
                'archives',
                'backups'
            ],
            'dynamodb_tables': [
                {
                    'name': 'users',
                    'key_schema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
                    'attribute_definitions': [{'AttributeName': 'user_id', 'AttributeType': 'S'}]
                },
                {
                    'name': 'orders',
                    'key_schema': [
                        {'AttributeName': 'order_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'attribute_definitions': [
                        {'AttributeName': 'order_id', 'AttributeType': 'S'},
                        {'AttributeName': 'timestamp', 'AttributeType': 'N'}
                    ]
                }
            ],
            'sqs_queues': [
                'notifications',
                'tasks',
                'dead-letter-queue'
            ],
            'kinesis_streams': [
                {'name': 'events', 'shard_count': 2},
                {'name': 'analytics', 'shard_count': 1}
            ]
        }
    ) as aws:
        print(f"LocalStack running at: {aws.endpoint_url}\n")

        # All resources are already created and ready to use!

        # Verify S3 buckets
        s3 = aws.get_s3_client()
        buckets = [b['Name'] for b in s3.list_buckets()['Buckets']]
        print(f"S3 Buckets created: {buckets}")

        # Verify DynamoDB tables
        dynamodb = aws.get_dynamodb_client()
        tables = dynamodb.list_tables()['TableNames']
        print(f"DynamoDB Tables created: {tables}")

        # Verify SQS queues
        queues = aws.sqs.list_queues()
        queue_names = [q.split('/')[-1] for q in queues]
        print(f"SQS Queues created: {queue_names}")

        # Verify Kinesis streams
        kinesis = aws.get_kinesis_client()
        streams = kinesis.list_streams()['StreamNames']
        print(f"Kinesis Streams created: {streams}")

        # Now use the resources
        print("\nUsing pre-initialized resources...")

        # Upload to S3
        aws.s3.put_object('uploads', 'file1.txt', b'data1')
        aws.s3.put_object('uploads', 'file2.txt', b'data2')

        # Insert into DynamoDB
        aws.dynamodb.put_item('users', {
            'user_id': {'S': '123'},
            'name': {'S': 'Alice'},
            'email': {'S': 'alice@example.com'}
        })

        # Send SQS message
        queue_url = aws.sqs.get_queue_url('notifications')
        aws.sqs.send_message(queue_url, 'Welcome notification')

        # Put Kinesis record
        aws.kinesis.put_record('events', b'{"event": "user_created"}', partition_key='123')

        print("\nAll operations completed successfully!")
        print("Resources will be automatically cleaned up on exit.")


if __name__ == '__main__':
    main()

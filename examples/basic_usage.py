"""Basic usage example of testcontainers-aws."""

from testcontainers_aws import AWSTestEnvironment


def main():
    """Demonstrate basic S3 operations."""
    print("Starting AWS Test Environment...")

    with AWSTestEnvironment(services=['s3']) as aws:
        print(f"LocalStack running at: {aws.endpoint_url}")

        # Create a bucket
        print("\nCreating S3 bucket 'test-bucket'...")
        aws.s3.create_bucket('test-bucket')

        # Upload an object
        print("Uploading object 'hello.txt'...")
        aws.s3.put_object('test-bucket', 'hello.txt', b'Hello from testcontainers-aws!')

        # List buckets
        buckets = aws.s3.list_buckets()
        print(f"\nBuckets: {[b['Name'] for b in buckets['Buckets']]}")

        # Download object
        print("\nDownloading object 'hello.txt'...")
        response = aws.s3.get_object('test-bucket', 'hello.txt')
        content = response['Body'].read()
        print(f"Content: {content.decode()}")

        print("\nExample completed successfully!")


if __name__ == '__main__':
    main()

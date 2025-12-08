"""Example demonstrating Lambda operations with testcontainers-aws."""

import json
from testcontainers_aws import AWSTestEnvironment
from testcontainers_aws.services.lambda_service import create_lambda_zip, create_lambda_zip_from_files


def main():
    """Demonstrate Lambda function creation and invocation."""
    print("Starting AWS Test Environment with Lambda...")

    with AWSTestEnvironment(services=['lambda']) as aws:
        print(f"LocalStack running at: {aws.endpoint_url}\n")

        # Example 1: Simple Lambda function
        print("=" * 60)
        print("Example 1: Creating a simple Lambda function")
        print("=" * 60)

        simple_code = """
def handler(event, context):
    name = event.get('name', 'World')
    return {
        'statusCode': 200,
        'body': f'Hello, {name}!'
    }
"""
        function_code = create_lambda_zip(simple_code)

        aws.lambda_.create_function(
            function_name='hello-function',
            runtime='python3.11',
            handler='index.handler',
            code=function_code
        )
        print("Created function: hello-function")

        # Invoke the function
        response = aws.lambda_.invoke_function(
            'hello-function',
            payload={'name': 'testcontainers-aws'}
        )

        result = json.loads(response['Payload'].read())
        print(f"Invocation result: {result}\n")

        # Example 2: Lambda with environment variables
        print("=" * 60)
        print("Example 2: Lambda with environment variables")
        print("=" * 60)

        env_code = """
import os

def handler(event, context):
    api_key = os.environ.get('API_KEY', 'not-set')
    environment = os.environ.get('ENVIRONMENT', 'unknown')

    return {
        'statusCode': 200,
        'body': {
            'api_key': api_key,
            'environment': environment,
            'message': 'Environment variables loaded!'
        }
    }
"""
        env_function_code = create_lambda_zip(env_code)

        aws.lambda_.create_function(
            function_name='env-function',
            runtime='python3.11',
            handler='index.handler',
            code=env_function_code,
            environment_variables={
                'API_KEY': 'secret-key-12345',
                'ENVIRONMENT': 'test'
            }
        )
        print("Created function with environment variables: env-function")

        response = aws.lambda_.invoke_function('env-function')
        result = json.loads(response['Payload'].read())
        print(f"Result with env vars: {result}\n")

        # Example 3: Lambda with multiple files
        print("=" * 60)
        print("Example 3: Lambda with multiple files")
        print("=" * 60)

        multi_file_code = create_lambda_zip_from_files({
            'index.py': """
from utils import format_response

def handler(event, context):
    message = event.get('message', 'No message provided')
    return format_response(message)
""",
            'utils.py': """
def format_response(message):
    return {
        'statusCode': 200,
        'body': {
            'message': message.upper(),
            'length': len(message)
        }
    }
"""
        })

        aws.lambda_.create_function(
            function_name='multi-file-function',
            runtime='python3.11',
            handler='index.handler',
            code=multi_file_code
        )
        print("Created multi-file function: multi-file-function")

        response = aws.lambda_.invoke_function(
            'multi-file-function',
            payload={'message': 'hello from lambda'}
        )
        result = json.loads(response['Payload'].read())
        print(f"Multi-file result: {result}\n")

        # Example 4: List all functions
        print("=" * 60)
        print("Example 4: Listing all Lambda functions")
        print("=" * 60)

        functions = aws.lambda_.list_functions()
        print(f"Total functions: {len(functions)}")
        for func in functions:
            print(f"  - {func['FunctionName']} (Runtime: {func['Runtime']})")

        print("\nLambda examples completed successfully!")


if __name__ == '__main__':
    main()

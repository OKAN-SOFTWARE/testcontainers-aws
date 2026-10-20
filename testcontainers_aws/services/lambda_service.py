"""Lambda service manager with helper methods."""

import json
import zipfile
from io import BytesIO
from typing import Any, Dict, List, Optional
from testcontainers_aws.services.base import BaseServiceManager


class LambdaServiceManager(BaseServiceManager):
    """Manages AWS Lambda operations and simplifies common testing tasks."""

    @property
    def client(self) -> Any:
        """Get Lambda client."""
        if not self._client:
            self._client = self.environment.get_client('lambda')
        return self._client

    def create_function(
        self,
        function_name: str,
        runtime: str,
        handler: str,
        code: bytes,
        role: str = 'arn:aws:iam::000000000000:role/lambda-role',
        environment_variables: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        memory_size: int = 128,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a Lambda function.

        Args:
            function_name: Name of the Lambda function
            runtime: Runtime (e.g., 'python3.11', 'nodejs18.x')
            handler: Handler name (e.g., 'index.handler')
            code: ZIP file bytes containing the function code
            role: IAM role ARN (default works with LocalStack)
            environment_variables: Environment variables for the function
            timeout: Function timeout in seconds (default: 30)
            memory_size: Memory size in MB (default: 128)
            **kwargs: Additional arguments passed to create_function

        Returns:
            Response from create_function API

        Example:
            ```python
            # Create a simple Python function
            code = create_lambda_zip("def handler(event, context): return {'statusCode': 200}")
            manager.create_function(
                function_name='my-function',
                runtime='python3.11',
                handler='index.handler',
                code=code
            )
            ```
        """
        params = {
            'FunctionName': function_name,
            'Runtime': runtime,
            'Handler': handler,
            'Code': {'ZipFile': code},
            'Role': role,
            'Timeout': timeout,
            'MemorySize': memory_size,
        }

        if environment_variables:
            params['Environment'] = {'Variables': environment_variables}

        params.update(kwargs)
        response = self.client.create_function(**params)

        # Wait for function to be ready (especially important for LocalStack)
        self._wait_for_function_active(function_name)

        return response

    def _wait_for_function_active(self, function_name: str, max_wait: int = 60) -> None:
        """
        Wait for Lambda function to become active.

        Args:
            function_name: Name of the function to wait for
            max_wait: Maximum time to wait in seconds (default: 60)
        """
        waiter = self.client.get_waiter('function_active_v2')
        waiter.wait(FunctionName=function_name, WaiterConfig={'Delay': 1, 'MaxAttempts': max_wait})

    def invoke_function(
        self,
        function_name: str,
        payload: Optional[Dict[str, Any]] = None,
        invocation_type: str = 'RequestResponse',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Invoke a Lambda function.

        Args:
            function_name: Name of the Lambda function
            payload: JSON-serializable payload to send to the function
            invocation_type: 'RequestResponse' (sync) or 'Event' (async)
            **kwargs: Additional arguments passed to invoke

        Returns:
            Response from invoke API with 'Payload' containing function result

        Example:
            ```python
            response = manager.invoke_function(
                'my-function',
                payload={'key': 'value'}
            )
            result = json.loads(response['Payload'].read())
            ```
        """
        params = {
            'FunctionName': function_name,
            'InvocationType': invocation_type,
        }

        if payload is not None:
            params['Payload'] = json.dumps(payload)

        params.update(kwargs)
        return self.client.invoke(**params)

    def update_function_code(
        self,
        function_name: str,
        code: bytes,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update Lambda function code.

        Args:
            function_name: Name of the Lambda function
            code: ZIP file bytes containing the new function code
            **kwargs: Additional arguments passed to update_function_code

        Returns:
            Response from update_function_code API
        """
        return self.client.update_function_code(
            FunctionName=function_name,
            ZipFile=code,
            **kwargs
        )

    def update_function_configuration(
        self,
        function_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update Lambda function configuration.

        Args:
            function_name: Name of the Lambda function
            **kwargs: Configuration parameters (e.g., Timeout, MemorySize, Environment)

        Returns:
            Response from update_function_configuration API
        """
        return self.client.update_function_configuration(
            FunctionName=function_name,
            **kwargs
        )

    def get_function(self, function_name: str) -> Dict[str, Any]:
        """
        Get Lambda function details.

        Args:
            function_name: Name of the Lambda function

        Returns:
            Response from get_function API
        """
        return self.client.get_function(FunctionName=function_name)

    def delete_function(self, function_name: str) -> Dict[str, Any]:
        """
        Delete a Lambda function.

        Args:
            function_name: Name of the Lambda function

        Returns:
            Response from delete_function API
        """
        return self.client.delete_function(FunctionName=function_name)

    def list_functions(self, max_items: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all Lambda functions.

        Args:
            max_items: Maximum number of functions to return

        Returns:
            List of function configurations
        """
        params = {}
        if max_items:
            params['MaxItems'] = max_items

        response = self.client.list_functions(**params)
        return response.get('Functions', [])

    def add_permission(
        self,
        function_name: str,
        statement_id: str,
        action: str,
        principal: str,
        source_arn: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Add permission to a Lambda function.

        Args:
            function_name: Name of the Lambda function
            statement_id: Unique statement ID
            action: Action to allow (e.g., 'lambda:InvokeFunction')
            principal: Principal who is getting permission (e.g., 's3.amazonaws.com')
            source_arn: ARN of the source resource
            **kwargs: Additional arguments passed to add_permission

        Returns:
            Response from add_permission API
        """
        params = {
            'FunctionName': function_name,
            'StatementId': statement_id,
            'Action': action,
            'Principal': principal,
        }

        if source_arn:
            params['SourceArn'] = source_arn

        params.update(kwargs)
        return self.client.add_permission(**params)

    def create_event_source_mapping(
        self,
        function_name: str,
        event_source_arn: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create an event source mapping for a Lambda function.

        Args:
            function_name: Name of the Lambda function
            event_source_arn: ARN of the event source (e.g., Kinesis stream, DynamoDB stream)
            **kwargs: Additional arguments (e.g., BatchSize, StartingPosition)

        Returns:
            Response from create_event_source_mapping API
        """
        return self.client.create_event_source_mapping(
            FunctionName=function_name,
            EventSourceArn=event_source_arn,
            **kwargs
        )


def create_lambda_zip(code: str, filename: str = "index.py") -> bytes:
    """
    Helper function to create a ZIP file from Python code string.

    Args:
        code: Python code as a string
        filename: Name of the file in the ZIP (default: index.py)

    Returns:
        ZIP file as bytes

    Example:
        ```python
        code = '''
def handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }
        '''
        zip_bytes = create_lambda_zip(code)
        ```
    """
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr(filename, code)
    return zip_buffer.getvalue()


def create_lambda_zip_from_files(files: Dict[str, str]) -> bytes:
    """
    Helper function to create a ZIP file from multiple files.

    Args:
        files: Dictionary mapping filenames to their content

    Returns:
        ZIP file as bytes

    Example:
        ```python
        zip_bytes = create_lambda_zip_from_files({
            'index.py': 'def handler(event, context): ...',
            'utils.py': 'def helper(): ...',
            'requirements.txt': 'boto3==1.28.0'
        })
        ```
    """
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filename, content in files.items():
            zipf.writestr(filename, content)
    return zip_buffer.getvalue()

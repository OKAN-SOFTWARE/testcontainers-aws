"""DynamoDB service manager with helper methods."""

from typing import TYPE_CHECKING, Any, Dict, List, cast
from testcontainers_aws.services.base import BaseServiceManager

if TYPE_CHECKING:
    from types_boto3_dynamodb import DynamoDBClient
    from types_boto3_dynamodb.type_defs import (
        CreateTableOutputTypeDef,
        DeleteTableOutputTypeDef,
        GetItemOutputTypeDef,
        PutItemOutputTypeDef,
        QueryOutputTypeDef,
        ScanOutputTypeDef,
    )


class DynamoDBServiceManager(BaseServiceManager):
    """Manages DynamoDB operations and simplifies common testing tasks."""

    @property
    def client(self) -> 'DynamoDBClient':
        """Get DynamoDB client."""
        if not self._client:
            self._client = self.environment.get_client('dynamodb')
        return cast('DynamoDBClient', self._client)

    def create_table(
        self,
        name: str,
        key_schema: List[Dict[str, str]],
        attribute_definitions: List[Dict[str, str]],
        billing_mode: str = 'PAY_PER_REQUEST',
        **kwargs: Any
    ) -> 'CreateTableOutputTypeDef':
        """
        Create a DynamoDB table.

        Args:
            name: Table name
            key_schema: Key schema definition
            attribute_definitions: Attribute definitions
            billing_mode: Billing mode (default: PAY_PER_REQUEST)
            **kwargs: Additional arguments passed to create_table

        Returns:
            Response from create_table API

        Example:
            ```python
            manager.create_table(
                name='users',
                key_schema=[
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                attribute_definitions=[
                    {'AttributeName': 'id', 'AttributeType': 'S'}
                ]
            )
            ```
        """
        params: Dict[str, Any] = {
            'TableName': name,
            'KeySchema': key_schema,
            'AttributeDefinitions': attribute_definitions,
            'BillingMode': billing_mode,
        }

        # Add provisioned throughput if using that billing mode
        if billing_mode == 'PROVISIONED':
            params['ProvisionedThroughput'] = {
                'ReadCapacityUnits': kwargs.pop('read_capacity', 5),
                'WriteCapacityUnits': kwargs.pop('write_capacity', 5),
            }

        params.update(kwargs)
        return self.client.create_table(**params)

    def put_item(
        self, table_name: str, item: Dict[str, Any], **kwargs: Any
    ) -> 'PutItemOutputTypeDef':
        """
        Put an item into a DynamoDB table.

        Args:
            table_name: Target table name
            item: Item data
            **kwargs: Additional arguments passed to put_item

        Returns:
            Response from put_item API
        """
        return self.client.put_item(
            TableName=table_name,
            Item=item,
            **kwargs
        )

    def get_item(
        self,
        table_name: str,
        key: Dict[str, Any],
        **kwargs: Any
    ) -> 'GetItemOutputTypeDef':
        """
        Get an item from a DynamoDB table.

        Args:
            table_name: Source table name
            key: Primary key of the item
            **kwargs: Additional arguments passed to get_item

        Returns:
            Response from get_item API
        """
        return self.client.get_item(
            TableName=table_name,
            Key=key,
            **kwargs
        )

    def query(
        self,
        table_name: str,
        key_condition_expression: str,
        expression_attribute_values: Dict[str, Any],
        **kwargs: Any
    ) -> 'QueryOutputTypeDef':
        """
        Query a DynamoDB table.

        Args:
            table_name: Table to query
            key_condition_expression: Query expression
            expression_attribute_values: Expression values
            **kwargs: Additional arguments passed to query

        Returns:
            Response from query API
        """
        return self.client.query(
            TableName=table_name,
            KeyConditionExpression=key_condition_expression,
            ExpressionAttributeValues=expression_attribute_values,
            **kwargs
        )

    def scan(self, table_name: str, **kwargs: Any) -> 'ScanOutputTypeDef':
        """
        Scan a DynamoDB table.

        Args:
            table_name: Table to scan
            **kwargs: Additional arguments passed to scan

        Returns:
            Response from scan API
        """
        return self.client.scan(TableName=table_name, **kwargs)

    def delete_table(self, table_name: str) -> 'DeleteTableOutputTypeDef':
        """
        Delete a DynamoDB table.

        Args:
            table_name: Table to delete

        Returns:
            Response from delete_table API
        """
        return self.client.delete_table(TableName=table_name)

    def list_tables(self) -> List[str]:
        """
        List all DynamoDB tables.

        Returns:
            List of table names
        """
        response = self.client.list_tables()
        return response.get('TableNames', [])

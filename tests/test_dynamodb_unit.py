"""Docker-free regression tests for DynamoDB service manager delegation."""

from unittest.mock import Mock

from testcontainers_aws.services.dynamodb import DynamoDBServiceManager


def make_manager():
    client = Mock()
    environment = Mock()
    environment.get_client.return_value = client
    return DynamoDBServiceManager(environment), client, environment


def test_dynamodb_client_is_lazily_initialized_and_cached():
    manager, client, environment = make_manager()

    assert manager.client is client
    assert manager.client is client
    environment.get_client.assert_called_once_with('dynamodb')


def test_create_table_passes_on_demand_parameters_and_extra_options():
    manager, client, _ = make_manager()
    response = {'TableDescription': {'TableName': 'users'}}
    client.create_table.return_value = response

    result = manager.create_table(
        name='users',
        key_schema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        attribute_definitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        DeletionProtectionEnabled=True,
    )

    assert result is response
    client.create_table.assert_called_once_with(
        TableName='users',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST',
        DeletionProtectionEnabled=True,
    )


def test_create_table_preserves_provisioned_throughput_defaults_and_overrides():
    manager, client, _ = make_manager()

    manager.create_table('users', [], [], billing_mode='PROVISIONED')
    client.create_table.assert_called_with(
        TableName='users',
        KeySchema=[],
        AttributeDefinitions=[],
        BillingMode='PROVISIONED',
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5},
    )

    manager.create_table(
        'users', [], [], billing_mode='PROVISIONED',
        read_capacity=2, write_capacity=7, Tags=[{'Key': 'env', 'Value': 'test'}],
    )
    client.create_table.assert_called_with(
        TableName='users',
        KeySchema=[],
        AttributeDefinitions=[],
        BillingMode='PROVISIONED',
        ProvisionedThroughput={'ReadCapacityUnits': 2, 'WriteCapacityUnits': 7},
        Tags=[{'Key': 'env', 'Value': 'test'}],
    )


def test_item_operations_forward_all_parameters_unchanged():
    manager, client, _ = make_manager()
    item = {'id': {'S': '123'}}
    key = {'id': {'S': '123'}}

    client.put_item.return_value = {'ResponseMetadata': {}}
    assert manager.put_item('users', item, ReturnValues='ALL_OLD') is client.put_item.return_value
    client.put_item.assert_called_once_with(
        TableName='users', Item=item, ReturnValues='ALL_OLD',
    )

    client.get_item.return_value = {'Item': item}
    assert manager.get_item('users', key, ConsistentRead=True) is client.get_item.return_value
    client.get_item.assert_called_once_with(
        TableName='users', Key=key, ConsistentRead=True,
    )

    client.query.return_value = {'Items': [item]}
    assert manager.query(
        'users', 'id = :id', {':id': {'S': '123'}}, Limit=10,
    ) is client.query.return_value
    client.query.assert_called_once_with(
        TableName='users',
        KeyConditionExpression='id = :id',
        ExpressionAttributeValues={':id': {'S': '123'}},
        Limit=10,
    )

    client.scan.return_value = {'Items': [item]}
    assert manager.scan('users', Limit=2) is client.scan.return_value
    client.scan.assert_called_once_with(TableName='users', Limit=2)


def test_table_operations_preserve_responses():
    manager, client, _ = make_manager()
    response = {'TableDescription': {'TableName': 'users'}}
    client.delete_table.return_value = response

    assert manager.delete_table('users') is response
    client.delete_table.assert_called_once_with(TableName='users')

    client.list_tables.return_value = {'TableNames': ['users', 'logs']}
    assert manager.list_tables() == ['users', 'logs']
    client.list_tables.assert_called_once_with()

    client.list_tables.return_value = {}
    assert manager.list_tables() == []

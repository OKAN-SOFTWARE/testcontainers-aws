"""Docker-free regression tests for SQS service manager delegation."""

from unittest.mock import Mock

from testcontainers_aws.services.sqs import SQSServiceManager


def make_manager():
    client = Mock()
    environment = Mock()
    environment.get_client.return_value = client
    return SQSServiceManager(environment), client, environment


def test_sqs_client_is_lazily_initialized_and_cached():
    manager, client, environment = make_manager()

    assert manager.client is client
    assert manager.client is client
    environment.get_client.assert_called_once_with('sqs')


def test_create_queue_forwards_parameters_and_attributes():
    manager, client, _ = make_manager()
    response = {'QueueUrl': 'http://localhost:4566/000000000000/my-queue'}
    client.create_queue.return_value = response

    result = manager.create_queue('my-queue')
    assert result is response
    client.create_queue.assert_called_once_with(QueueName='my-queue')

    client.create_queue.reset_mock()
    attributes = {'VisibilityTimeout': '30', 'DelaySeconds': '5'}
    result2 = manager.create_queue('my-queue', attributes=attributes, tags={'env': 'test'})
    assert result2 is response
    client.create_queue.assert_called_once_with(
        QueueName='my-queue',
        Attributes=attributes,
        tags={'env': 'test'},
    )


def test_get_queue_url_returns_queue_url_string():
    manager, client, _ = make_manager()
    client.get_queue_url.return_value = {'QueueUrl': 'http://localhost:4566/000000000000/test-queue'}

    url = manager.get_queue_url('test-queue')
    assert url == 'http://localhost:4566/000000000000/test-queue'
    client.get_queue_url.assert_called_once_with(QueueName='test-queue')


def test_send_message_forwards_body_and_attributes():
    manager, client, _ = make_manager()
    response = {'MessageId': 'msg-123', 'MD5OfMessageBody': 'xyz'}
    client.send_message.return_value = response

    result = manager.send_message('http://queue-url', 'hello world')
    assert result is response
    client.send_message.assert_called_once_with(
        QueueUrl='http://queue-url',
        MessageBody='hello world',
    )

    client.send_message.reset_mock()
    msg_attrs = {'Author': {'DataType': 'String', 'StringValue': 'Tester'}}
    result2 = manager.send_message(
        'http://queue-url', 'hello world', message_attributes=msg_attrs, DelaySeconds=10
    )
    assert result2 is response
    client.send_message.assert_called_once_with(
        QueueUrl='http://queue-url',
        MessageBody='hello world',
        MessageAttributes=msg_attrs,
        DelaySeconds=10,
    )


def test_receive_messages_returns_message_list_or_empty():
    manager, client, _ = make_manager()
    messages = [{'MessageId': 'msg-1', 'Body': 'hello'}]
    client.receive_message.return_value = {'Messages': messages}

    result = manager.receive_messages('http://queue-url', max_messages=5, wait_time_seconds=2)
    assert result == messages
    client.receive_message.assert_called_once_with(
        QueueUrl='http://queue-url',
        MaxNumberOfMessages=5,
        WaitTimeSeconds=2,
    )

    client.receive_message.return_value = {}
    assert manager.receive_messages('http://queue-url') == []


def test_delete_and_purge_operations_forward_parameters():
    manager, client, _ = make_manager()
    meta_response = {'ResponseMetadata': {'HTTPStatusCode': 200}}
    client.delete_message.return_value = meta_response
    client.purge_queue.return_value = meta_response
    client.delete_queue.return_value = meta_response

    del_res = manager.delete_message('http://queue-url', 'receipt-123')
    assert del_res is meta_response
    client.delete_message.assert_called_once_with(
        QueueUrl='http://queue-url',
        ReceiptHandle='receipt-123',
    )

    purge_res = manager.purge_queue('http://queue-url')
    assert purge_res is meta_response
    client.purge_queue.assert_called_once_with(QueueUrl='http://queue-url')

    del_queue_res = manager.delete_queue('http://queue-url')
    assert del_queue_res is meta_response
    client.delete_queue.assert_called_once_with(QueueUrl='http://queue-url')


def test_list_queues_returns_urls_with_optional_prefix():
    manager, client, _ = make_manager()
    urls = ['http://queue-url/1', 'http://queue-url/2']
    client.list_queues.return_value = {'QueueUrls': urls}

    assert manager.list_queues() == urls
    client.list_queues.assert_called_once_with()

    client.list_queues.reset_mock()
    assert manager.list_queues(prefix='test-') == urls
    client.list_queues.assert_called_once_with(QueueNamePrefix='test-')

    client.list_queues.return_value = {}
    assert manager.list_queues() == []

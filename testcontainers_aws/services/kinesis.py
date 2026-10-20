"""Kinesis service manager with helper methods."""

from typing import Any, Dict, List, Optional
from testcontainers_aws.services.base import BaseServiceManager


class KinesisServiceManager(BaseServiceManager):
    """Manages Kinesis operations and simplifies common testing tasks."""

    @property
    def client(self) -> Any:
        """Get Kinesis client."""
        if not self._client:
            self._client = self.environment.get_client('kinesis')
        return self._client

    def create_stream(
        self,
        stream_name: str,
        shard_count: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a Kinesis stream.

        Args:
            stream_name: Name of the stream
            shard_count: Number of shards (default: 1)
            **kwargs: Additional arguments passed to create_stream

        Returns:
            Response from create_stream API
        """
        response = self.client.create_stream(
            StreamName=stream_name,
            ShardCount=shard_count,
            **kwargs
        )

        # Streams start in CREATING state and reject writes until ACTIVE
        self.client.get_waiter('stream_exists').wait(StreamName=stream_name)

        return response

    def put_record(
        self,
        stream_name: str,
        data: bytes,
        partition_key: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Put a record into a Kinesis stream.

        Args:
            stream_name: Target stream name
            data: Record data (bytes)
            partition_key: Partition key for the record
            **kwargs: Additional arguments passed to put_record

        Returns:
            Response from put_record API
        """
        return self.client.put_record(
            StreamName=stream_name,
            Data=data,
            PartitionKey=partition_key,
            **kwargs
        )

    def put_records(
        self,
        stream_name: str,
        records: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Put multiple records into a Kinesis stream.

        Args:
            stream_name: Target stream name
            records: List of records, each with 'Data' and 'PartitionKey'
            **kwargs: Additional arguments passed to put_records

        Returns:
            Response from put_records API
        """
        return self.client.put_records(
            StreamName=stream_name,
            Records=records,
            **kwargs
        )

    def get_shard_iterator(
        self,
        stream_name: str,
        shard_id: str,
        iterator_type: str = 'TRIM_HORIZON',
        **kwargs
    ) -> str:
        """
        Get a shard iterator for reading from a stream.

        Args:
            stream_name: Stream name
            shard_id: Shard ID
            iterator_type: Iterator type (default: TRIM_HORIZON)
            **kwargs: Additional arguments passed to get_shard_iterator

        Returns:
            Shard iterator string
        """
        response = self.client.get_shard_iterator(
            StreamName=stream_name,
            ShardId=shard_id,
            ShardIteratorType=iterator_type,
            **kwargs
        )
        return response['ShardIterator']

    def get_records(
        self,
        shard_iterator: str,
        limit: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get records from a Kinesis stream.

        Args:
            shard_iterator: Shard iterator
            limit: Maximum number of records to retrieve
            **kwargs: Additional arguments passed to get_records

        Returns:
            Response from get_records API
        """
        params = {'ShardIterator': shard_iterator}

        if limit:
            params['Limit'] = limit

        params.update(kwargs)
        return self.client.get_records(**params)

    def describe_stream(self, stream_name: str) -> Dict[str, Any]:
        """
        Describe a Kinesis stream.

        Args:
            stream_name: Stream name

        Returns:
            Response from describe_stream API
        """
        return self.client.describe_stream(StreamName=stream_name)

    def delete_stream(self, stream_name: str, **kwargs) -> Dict[str, Any]:
        """
        Delete a Kinesis stream.

        Args:
            stream_name: Stream to delete
            **kwargs: Additional arguments passed to delete_stream

        Returns:
            Response from delete_stream API
        """
        return self.client.delete_stream(StreamName=stream_name, **kwargs)

    def list_streams(self, limit: Optional[int] = None) -> List[str]:
        """
        List all Kinesis streams.

        Args:
            limit: Maximum number of streams to return

        Returns:
            List of stream names
        """
        params = {}
        if limit:
            params['Limit'] = limit

        response = self.client.list_streams(**params)
        return response.get('StreamNames', [])

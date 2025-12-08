"""Base service manager for AWS services."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from testcontainers_aws.core import AWSTestEnvironment


class BaseServiceManager:
    """Base class for AWS service managers."""

    def __init__(self, environment: 'AWSTestEnvironment'):
        """
        Initialize service manager.

        Args:
            environment: Parent AWSTestEnvironment instance
        """
        self.environment = environment
        self._client = None

    @property
    def client(self) -> Any:
        """Get the boto3 client for this service (implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement the client property")

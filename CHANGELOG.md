# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Default LocalStack image is now pinned to `4.14` instead of `latest`. LocalStack `2026.03.0`+
  requires an auth token, which made the previous default hang on startup.

### Added
- GitHub Actions CI running ruff and the integration test suite
- `CONTRIBUTING.md`

## [0.1.0] - 2024-12-03

### Added
- Initial release of testcontainers-aws
- Core `AWSTestEnvironment` class for orchestrating AWS services
- Support for 6 AWS services:
  - S3 - Object storage operations
  - DynamoDB - NoSQL database operations
  - SQS - Queue messaging operations
  - Kinesis - Stream processing operations
  - Lambda - Serverless function operations
  - SNS - Pub/sub messaging operations
- Service manager classes with helper methods for each service
- Auto-initialization of resources via `init_config` parameter
- Pytest fixtures for common testing patterns:
  - Session-scoped environment and clients
  - Function-scoped resources with auto-cleanup
- Comprehensive examples demonstrating:
  - Basic service usage
  - Pytest integration
  - Auto-initialization patterns
  - Lambda function creation and invocation
  - SNS topics and subscriptions
  - Lambda-SNS event-driven architecture
- Full test suite covering all service managers
- Documentation with usage examples and API reference
- Helper utilities:
  - `create_lambda_zip()` - Create Lambda deployment packages from code strings
  - `create_lambda_zip_from_files()` - Create multi-file Lambda packages

### Features
- Single LocalStack container orchestration
- Pre-configured boto3 clients with automatic endpoint/credential setup
- Context manager support for automatic cleanup
- Declarative resource initialization
- Type hints for better IDE support
- Comprehensive error handling

[0.1.0]: https://github.com/yourusername/testcontainers-aws/releases/tag/v0.1.0

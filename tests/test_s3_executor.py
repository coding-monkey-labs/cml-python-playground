"""Tests for the S3 executor using moto mock."""

import pytest
import boto3
from moto import mock_aws

from app.executors.s3_executor import S3Executor, S3ExecutorError


@pytest.fixture
def s3_executor():
    """Create an S3 executor backed by moto mock."""
    with mock_aws():
        executor = S3Executor(
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
            region_name="us-east-1",
        )
        yield executor


def test_list_buckets_empty(s3_executor):
    result = s3_executor.execute("list_buckets", {})
    assert result["buckets"] == []


def test_create_and_list_bucket(s3_executor):
    s3_executor.execute("create_bucket", {"bucket_name": "test-bucket"})
    result = s3_executor.execute("list_buckets", {})
    names = [b["name"] for b in result["buckets"]]
    assert "test-bucket" in names


def test_create_bucket_with_versioning(s3_executor):
    s3_executor.execute(
        "create_bucket",
        {"bucket_name": "versioned-bucket", "versioning": True},
    )
    result = s3_executor.execute(
        "get_bucket_versioning", {"bucket_name": "versioned-bucket"}
    )
    assert result["status"] == "Enabled"


def test_delete_empty_bucket(s3_executor):
    s3_executor.execute("create_bucket", {"bucket_name": "to-delete"})
    result = s3_executor.execute("delete_bucket", {"bucket_name": "to-delete"})
    assert result["deleted"] is True


def test_get_bucket_versioning_disabled(s3_executor):
    s3_executor.execute("create_bucket", {"bucket_name": "no-ver"})
    result = s3_executor.execute("get_bucket_versioning", {"bucket_name": "no-ver"})
    assert result["status"] == "Disabled"


def test_put_bucket_versioning(s3_executor):
    s3_executor.execute("create_bucket", {"bucket_name": "ver-bucket"})
    s3_executor.execute(
        "put_bucket_versioning",
        {"bucket_name": "ver-bucket", "status": "Enabled"},
    )
    result = s3_executor.execute("get_bucket_versioning", {"bucket_name": "ver-bucket"})
    assert result["status"] == "Enabled"


def test_suspend_versioning(s3_executor):
    s3_executor.execute("create_bucket", {"bucket_name": "sus-bucket"})
    s3_executor.execute(
        "put_bucket_versioning",
        {"bucket_name": "sus-bucket", "status": "Enabled"},
    )
    s3_executor.execute(
        "put_bucket_versioning",
        {"bucket_name": "sus-bucket", "status": "Suspended"},
    )
    result = s3_executor.execute("get_bucket_versioning", {"bucket_name": "sus-bucket"})
    assert result["status"] == "Suspended"


def test_get_bucket_details(s3_executor):
    s3_executor.execute("create_bucket", {"bucket_name": "detail-bucket"})
    result = s3_executor.execute("get_bucket_details", {"bucket_name": "detail-bucket"})
    assert result["bucket_name"] == "detail-bucket"
    assert "versioning" in result
    assert "object_count" in result


def test_list_objects_empty_bucket(s3_executor):
    s3_executor.execute("create_bucket", {"bucket_name": "empty-bucket"})
    result = s3_executor.execute("list_objects", {"bucket_name": "empty-bucket"})
    assert result["objects"] == []
    assert result["count"] == 0


def test_list_buckets_with_prefix(s3_executor):
    s3_executor.execute("create_bucket", {"bucket_name": "prod-data"})
    s3_executor.execute("create_bucket", {"bucket_name": "prod-logs"})
    s3_executor.execute("create_bucket", {"bucket_name": "dev-data"})

    result = s3_executor.execute("list_buckets", {"prefix": "prod-"})
    names = [b["name"] for b in result["buckets"]]
    assert "prod-data" in names
    assert "prod-logs" in names
    assert "dev-data" not in names


def test_unknown_operation(s3_executor):
    with pytest.raises(S3ExecutorError, match="Unknown operation"):
        s3_executor.execute("nonexistent_op", {})


def test_execute_bulk(s3_executor):
    s3_executor.execute("create_bucket", {"bucket_name": "bulk-a"})
    s3_executor.execute("create_bucket", {"bucket_name": "bulk-b"})

    results = s3_executor.execute_bulk(
        "put_bucket_versioning",
        {"status": "Enabled"},
        [{"bucket_name": "bulk-a"}, {"bucket_name": "bulk-b"}],
    )

    assert len(results) == 2
    assert all(r["success"] for r in results)


def test_delete_nonempty_bucket_fails(s3_executor):
    s3_executor.execute("create_bucket", {"bucket_name": "nonempty"})
    # Put an object
    s3_executor._client.put_object(
        Bucket="nonempty", Key="test.txt", Body=b"data"
    )

    with pytest.raises(S3ExecutorError, match="not empty"):
        s3_executor.execute("delete_bucket", {"bucket_name": "nonempty"})

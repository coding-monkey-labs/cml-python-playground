"""S3 executor layer wrapping boto3 operations for the state engine."""

from __future__ import annotations

import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3ExecutorError(Exception):
    pass


class S3Executor:
    """Wraps S3/ObjectScale API calls as callable actions for the state engine.

    All S3 interaction is isolated here. The state engine calls execute()
    with an operation name and params; this layer translates to boto3 calls.
    """

    def __init__(
        self,
        endpoint_url: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        region_name: str = "us-east-1",
    ):
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id or "testing",
            aws_secret_access_key=aws_secret_access_key or "testing",
            region_name=region_name,
        )

    OPERATIONS = {
        "list_buckets",
        "create_bucket",
        "delete_bucket",
        "get_bucket_versioning",
        "put_bucket_versioning",
        "get_object_lock_configuration",
        "put_object_lock_configuration",
        "get_bucket_lifecycle",
        "put_bucket_lifecycle",
        "get_bucket_policy",
        "put_bucket_policy",
        "delete_bucket_policy",
        "get_bucket_details",
        "list_objects",
    }

    def execute(self, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a single S3 operation."""
        if operation not in self.OPERATIONS:
            raise S3ExecutorError(f"Unknown operation: {operation}")

        handler = getattr(self, f"_op_{operation}", None)
        if not handler:
            raise S3ExecutorError(f"Operation not implemented: {operation}")

        try:
            return handler(params)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]
            raise S3ExecutorError(f"S3 error [{error_code}]: {error_msg}") from e

    def execute_bulk(
        self,
        operation: str,
        base_params: dict[str, Any],
        items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Execute an operation across multiple items (e.g., bulk update buckets)."""
        results = []
        for item in items:
            merged_params = {**base_params, **item}
            try:
                result = self.execute(operation, merged_params)
                results.append({"success": True, "item": item, "result": result})
            except S3ExecutorError as e:
                results.append({"success": False, "item": item, "error": str(e)})
        return results

    # --- Operation Handlers ---

    def _op_list_buckets(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._client.list_buckets()
        buckets = [
            {
                "name": b["Name"],
                "creation_date": b["CreationDate"].isoformat(),
            }
            for b in response.get("Buckets", [])
        ]
        prefix = params.get("prefix")
        if prefix:
            buckets = [b for b in buckets if b["name"].startswith(prefix)]
        return {"buckets": buckets}

    def _op_create_bucket(self, params: dict[str, Any]) -> dict[str, Any]:
        bucket_name = params["bucket_name"]
        create_params: dict[str, Any] = {"Bucket": bucket_name}

        region = params.get("region")
        if region and region != "us-east-1":
            create_params["CreateBucketConfiguration"] = {
                "LocationConstraint": region,
            }

        self._client.create_bucket(**create_params)

        # Optional: enable versioning
        if params.get("versioning"):
            self._client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={"Status": "Enabled"},
            )

        # Optional: enable object lock
        if params.get("object_lock"):
            try:
                self._client.put_object_lock_configuration(
                    Bucket=bucket_name,
                    ObjectLockConfiguration={
                        "ObjectLockEnabled": "Enabled",
                        "Rule": {
                            "DefaultRetention": {
                                "Mode": params.get("lock_mode", "GOVERNANCE"),
                                "Days": params.get("lock_days", 30),
                            }
                        },
                    },
                )
            except ClientError:
                logger.warning("Object lock not supported or failed for %s", bucket_name)

        return {"bucket_name": bucket_name, "created": True}

    def _op_delete_bucket(self, params: dict[str, Any]) -> dict[str, Any]:
        bucket_name = params["bucket_name"]

        # Check if bucket is empty first
        if params.get("force_check", True):
            response = self._client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
            if response.get("Contents"):
                raise S3ExecutorError(
                    f"Bucket '{bucket_name}' is not empty. Cannot delete."
                )

        self._client.delete_bucket(Bucket=bucket_name)
        return {"bucket_name": bucket_name, "deleted": True}

    def _op_get_bucket_versioning(self, params: dict[str, Any]) -> dict[str, Any]:
        bucket_name = params["bucket_name"]
        response = self._client.get_bucket_versioning(Bucket=bucket_name)
        return {
            "bucket_name": bucket_name,
            "status": response.get("Status", "Disabled"),
            "mfa_delete": response.get("MFADelete", "Disabled"),
        }

    def _op_put_bucket_versioning(self, params: dict[str, Any]) -> dict[str, Any]:
        bucket_name = params["bucket_name"]
        status = params.get("status", "Enabled")
        self._client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={"Status": status},
        )
        return {"bucket_name": bucket_name, "versioning_status": status}

    def _op_get_object_lock_configuration(self, params: dict[str, Any]) -> dict[str, Any]:
        bucket_name = params["bucket_name"]
        try:
            response = self._client.get_object_lock_configuration(Bucket=bucket_name)
            config = response.get("ObjectLockConfiguration", {})
            return {
                "bucket_name": bucket_name,
                "enabled": config.get("ObjectLockEnabled", "Disabled"),
                "rule": config.get("Rule", {}),
            }
        except ClientError as e:
            if e.response["Error"]["Code"] == "ObjectLockConfigurationNotFoundError":
                return {"bucket_name": bucket_name, "enabled": "Disabled", "rule": {}}
            raise

    def _op_put_object_lock_configuration(self, params: dict[str, Any]) -> dict[str, Any]:
        bucket_name = params["bucket_name"]
        mode = params.get("mode", "GOVERNANCE")
        days = params.get("days", 30)

        self._client.put_object_lock_configuration(
            Bucket=bucket_name,
            ObjectLockConfiguration={
                "ObjectLockEnabled": "Enabled",
                "Rule": {
                    "DefaultRetention": {
                        "Mode": mode,
                        "Days": days,
                    }
                },
            },
        )
        return {"bucket_name": bucket_name, "object_lock": "Enabled", "mode": mode, "days": days}

    def _op_get_bucket_lifecycle(self, params: dict[str, Any]) -> dict[str, Any]:
        bucket_name = params["bucket_name"]
        try:
            response = self._client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            return {
                "bucket_name": bucket_name,
                "rules": response.get("Rules", []),
            }
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchLifecycleConfiguration":
                return {"bucket_name": bucket_name, "rules": []}
            raise

    def _op_put_bucket_lifecycle(self, params: dict[str, Any]) -> dict[str, Any]:
        bucket_name = params["bucket_name"]
        rules = params.get("rules", [])
        self._client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration={"Rules": rules},
        )
        return {"bucket_name": bucket_name, "lifecycle_updated": True}

    def _op_get_bucket_policy(self, params: dict[str, Any]) -> dict[str, Any]:
        bucket_name = params["bucket_name"]
        try:
            response = self._client.get_bucket_policy(Bucket=bucket_name)
            return {"bucket_name": bucket_name, "policy": response.get("Policy", "{}")}
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucketPolicy":
                return {"bucket_name": bucket_name, "policy": "{}"}
            raise

    def _op_put_bucket_policy(self, params: dict[str, Any]) -> dict[str, Any]:
        bucket_name = params["bucket_name"]
        policy = params["policy"]
        self._client.put_bucket_policy(Bucket=bucket_name, Policy=policy)
        return {"bucket_name": bucket_name, "policy_updated": True}

    def _op_delete_bucket_policy(self, params: dict[str, Any]) -> dict[str, Any]:
        bucket_name = params["bucket_name"]
        self._client.delete_bucket_policy(Bucket=bucket_name)
        return {"bucket_name": bucket_name, "policy_deleted": True}

    def _op_get_bucket_details(self, params: dict[str, Any]) -> dict[str, Any]:
        bucket_name = params["bucket_name"]
        details: dict[str, Any] = {"bucket_name": bucket_name}

        # Versioning
        ver = self._client.get_bucket_versioning(Bucket=bucket_name)
        details["versioning"] = ver.get("Status", "Disabled")

        # Lifecycle
        try:
            lc = self._client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            details["lifecycle_rules"] = len(lc.get("Rules", []))
        except ClientError:
            details["lifecycle_rules"] = 0

        # Object count (sample)
        try:
            objs = self._client.list_objects_v2(Bucket=bucket_name, MaxKeys=1000)
            details["object_count"] = objs.get("KeyCount", 0)
        except ClientError:
            details["object_count"] = "unknown"

        return details

    def _op_list_objects(self, params: dict[str, Any]) -> dict[str, Any]:
        bucket_name = params["bucket_name"]
        prefix = params.get("prefix", "")
        max_keys = params.get("max_keys", 1000)

        response = self._client.list_objects_v2(
            Bucket=bucket_name, Prefix=prefix, MaxKeys=max_keys
        )
        objects = [
            {
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
            }
            for obj in response.get("Contents", [])
        ]
        return {
            "bucket_name": bucket_name,
            "objects": objects,
            "count": response.get("KeyCount", 0),
            "truncated": response.get("IsTruncated", False),
        }

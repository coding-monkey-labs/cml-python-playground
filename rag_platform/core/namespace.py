"""Namespace isolation and validation utilities."""

import re

from rag_platform.core.exceptions import AuthorizationError, RAGPlatformError


def validate_namespace(namespace: str) -> str:
    """Validate and normalize a namespace string.

    Namespaces must be:
    - 1-255 characters
    - Alphanumeric, hyphens, underscores only
    - No leading/trailing hyphens or underscores
    """
    if not namespace or len(namespace) > 255:
        raise RAGPlatformError(
            "Namespace must be between 1 and 255 characters",
            details={"namespace": namespace},
        )

    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$", namespace):
        raise RAGPlatformError(
            "Namespace must contain only alphanumeric characters, hyphens, and underscores, "
            "and cannot start or end with a hyphen or underscore",
            details={"namespace": namespace},
        )

    return namespace.lower()


def build_collection_name(namespace: str, tenant: str | None = None) -> str:
    """Build a fully qualified collection name with optional tenant prefix.

    Format: {tenant}__{namespace} or just {namespace} if no tenant.
    This ensures namespace-level isolation in shared vector DBs.
    """
    namespace = validate_namespace(namespace)
    if tenant:
        tenant = validate_namespace(tenant)
        return f"{tenant}__{namespace}"
    return namespace


def check_namespace_access(
    user_namespaces: list[str] | None,
    target_namespace: str,
) -> None:
    """Check if a user/service has access to a target namespace.

    Args:
        user_namespaces: List of allowed namespaces (None = unrestricted).
        target_namespace: The namespace being accessed.

    Raises:
        AuthorizationError if access is denied.
    """
    if user_namespaces is None:
        return  # Unrestricted access (admin)

    if target_namespace not in user_namespaces and "*" not in user_namespaces:
        raise AuthorizationError(
            f"Access denied to namespace '{target_namespace}'",
            details={
                "allowed_namespaces": user_namespaces,
                "requested_namespace": target_namespace,
            },
        )

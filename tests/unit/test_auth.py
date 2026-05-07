"""Tests for auth module — JWT tokens and password hashing."""

from datetime import timedelta

import pytest

from engineering_intelligence.auth.jwt import create_access_token, decode_token
from engineering_intelligence.auth.password import hash_password, verify_password


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "secure-password-123"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct-password")
        assert not verify_password("wrong-password", hashed)

    def test_different_hashes_for_same_password(self):
        password = "test-password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # bcrypt uses random salt


class TestJWT:
    def test_create_and_decode_token(self):
        data = {"sub": "user@example.com", "role": "developer"}
        token = create_access_token(data)
        payload = decode_token(token)
        assert payload["sub"] == "user@example.com"
        assert payload["role"] == "developer"
        assert "exp" in payload

    def test_custom_expiry(self):
        data = {"sub": "admin@example.com"}
        token = create_access_token(data, expires_delta=timedelta(hours=2))
        payload = decode_token(token)
        assert payload["sub"] == "admin@example.com"

    def test_invalid_token_raises(self):
        with pytest.raises(ValueError, match="Invalid token"):
            decode_token("invalid.token.here")

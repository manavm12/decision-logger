"""Tests for secret redactor"""

import pytest
from decision_logger.processing.redactor import SecretRedactor


def test_api_key_redaction():
    """Test that API keys are redacted"""
    redactor = SecretRedactor()

    text = "API_KEY=FAKE_API_KEY_FOR_TESTING_ONLY_abcdef123456"
    redacted, types = redactor.redact(text)

    assert "FAKE_API_KEY_FOR_TESTING_ONLY_abcdef123456" not in redacted
    assert "[REDACTED" in redacted
    assert len(types) > 0


def test_bearer_token_redaction():
    """Test that bearer tokens are redacted"""
    redactor = SecretRedactor()

    text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"
    redacted, types = redactor.redact(text)

    assert "Bearer [REDACTED_TOKEN]" in redacted or "Bearer [REDACTED" in redacted
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0" not in redacted


def test_jwt_redaction():
    """Test that JWTs are redacted"""
    redactor = SecretRedactor()

    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    text = f"Token: {jwt}"
    redacted, types = redactor.redact(text)

    assert jwt not in redacted
    assert "[REDACTED_JWT]" in redacted


def test_github_token_redaction():
    """Test that GitHub tokens are redacted"""
    redactor = SecretRedactor()

    text = "GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyzAB"
    redacted, types = redactor.redact(text)

    assert "ghp_1234567890abcdefghijklmnopqrstuvwxyzAB" not in redacted
    assert "[REDACTED_GITHUB_TOKEN]" in redacted


def test_no_false_positives():
    """Test that normal code is not redacted"""
    redactor = SecretRedactor()

    text = "const apiKey = process.env.API_KEY"
    redacted, types = redactor.redact(text)

    # Should keep the reference but not treat it as a secret value
    assert "apiKey" in redacted
    assert "process.env" in redacted


def test_url_with_credentials_redaction():
    """Test that URLs with embedded credentials are redacted"""
    redactor = SecretRedactor()

    text = "https://user:password@example.com/path"
    redacted, types = redactor.redact(text)

    assert "user:password" not in redacted
    assert "[REDACTED]:[REDACTED]" in redacted
    assert "example.com" in redacted

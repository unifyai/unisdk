"""Tests for storage utilities."""

import base64
from unittest.mock import MagicMock, patch

import unisdk
from unisdk.utils import storage


class TestGetSignedUrl:
    """Tests for unisdk.get_signed_url function."""

    def test_returns_signed_url(self):
        """Test that get_signed_url returns the signed URL from the response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "signed_url": "https://storage.googleapis.com/bucket/object?signature=abc123",
            "expires_in_minutes": 60,
        }

        with patch.object(
            storage.http,
            "post",
            return_value=mock_response,
        ) as mock_post:
            result = unisdk.get_signed_url("gs://test-bucket/path/to/object.jpg")

            assert (
                result
                == "https://storage.googleapis.com/bucket/object?signature=abc123"
            )
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "/storage/signed-url" in call_args[0][0]
            assert (
                call_args[1]["json"]["gcs_uri"] == "gs://test-bucket/path/to/object.jpg"
            )
            assert call_args[1]["json"]["expiration_minutes"] == 60

    def test_custom_expiration(self):
        """Test that custom expiration is passed correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "signed_url": "https://storage.googleapis.com/bucket/object?signature=abc123",
            "expires_in_minutes": 120,
        }

        with patch.object(
            storage.http,
            "post",
            return_value=mock_response,
        ) as mock_post:
            result = unisdk.get_signed_url(
                "gs://bucket/object",
                expiration_minutes=120,
            )

            assert result is not None
            call_args = mock_post.call_args
            assert call_args[1]["json"]["expiration_minutes"] == 120

    def test_uses_api_key(self):
        """Test that API key is included in headers."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "signed_url": "https://example.com/signed",
            "expires_in_minutes": 60,
        }

        with patch.object(
            storage.http,
            "post",
            return_value=mock_response,
        ) as mock_post:
            unisdk.get_signed_url("gs://bucket/object", api_key="test-key")

            call_args = mock_post.call_args
            assert "headers" in call_args[1]
            assert "Authorization" in call_args[1]["headers"]


class TestDownloadObject:
    """Tests for unisdk.download_object function."""

    def test_returns_decoded_bytes(self):
        """Test that download_object returns decoded bytes from base64 response."""
        test_content = b"Hello, World!"
        encoded_content = base64.b64encode(test_content).decode("utf-8")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content_base64": encoded_content,
            "content_type": "text/plain",
            "size_bytes": len(test_content),
        }

        with patch.object(
            storage.http,
            "post",
            return_value=mock_response,
        ) as mock_post:
            result = unisdk.download_object("gs://test-bucket/hello.txt")

            assert result == test_content
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "/storage/download" in call_args[0][0]
            assert call_args[1]["json"]["gcs_uri"] == "gs://test-bucket/hello.txt"

    def test_handles_binary_content(self):
        """Test that binary content (e.g., images) is decoded correctly."""
        # Simulate PNG header bytes
        test_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        encoded_content = base64.b64encode(test_content).decode("utf-8")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content_base64": encoded_content,
            "content_type": "image/png",
            "size_bytes": len(test_content),
        }

        with patch.object(storage.http, "post", return_value=mock_response):
            result = unisdk.download_object("gs://bucket/image.png")

            assert result == test_content
            assert result.startswith(b"\x89PNG")

    def test_uses_api_key(self):
        """Test that API key is included in headers."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content_base64": base64.b64encode(b"data").decode(),
            "content_type": None,
            "size_bytes": 4,
        }

        with patch.object(
            storage.http,
            "post",
            return_value=mock_response,
        ) as mock_post:
            unisdk.download_object("gs://bucket/object", api_key="test-key")

            call_args = mock_post.call_args
            assert "headers" in call_args[1]
            assert "Authorization" in call_args[1]["headers"]


class TestModuleExports:
    """Test that functions are properly exported from the unify module."""

    def test_get_signed_url_exported(self):
        """Test that get_signed_url is accessible from unisdk module."""
        assert hasattr(unify, "get_signed_url")
        assert callable(unisdk.get_signed_url)

    def test_download_object_exported(self):
        """Test that download_object is accessible from unisdk module."""
        assert hasattr(unify, "download_object")
        assert callable(unisdk.download_object)

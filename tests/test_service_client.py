import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.service_client import ServiceClient


class TestServiceClientInit:
    def test_init_with_basic_config(self):
        config = {
            "name": "test_platform",
            "api_url": "https://api.test.com/generate",
            "request_method": "POST",
            "auth_type": "none",
            "response_type": "binary",
        }
        client = ServiceClient(config)
        assert client.name == "test_platform"
        assert client.api_url == "https://api.test.com/generate"
        assert client.request_method == "POST"

    def test_init_with_retry_config(self):
        config = {"name": "test", "api_url": "https://test.com"}
        retry_config = {"max_retries": 5, "retry_interval": 2, "timeout": 60}
        client = ServiceClient(config, retry_config)
        assert client.max_retries == 5
        assert client.retry_interval == 2
        assert client.timeout == 60

    def test_init_default_retry_config(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        assert client.max_retries == 3
        assert client.retry_interval == 1
        assert client.timeout == 15

    def test_init_with_request_params(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "request_params": {"width": 512, "height": 512},
            "request_headers": {"Content-Type": "application/json"},
            "request_body": {"prompt": "{prompt}"},
        }
        client = ServiceClient(config)
        assert client.request_params == {"width": 512, "height": 512}
        assert client.request_headers == {"Content-Type": "application/json"}


class TestReplaceTemplates:
    def test_replace_templates_string(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        template = "Hello {name}, your id is {id}"
        variables = {"name": "Alice", "id": "123"}
        result = client._replace_templates(template, variables)
        assert result == "Hello Alice, your id is 123"

    def test_replace_templates_dict(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        template = {"url": "{base_url}/api", "key": "{api_key}"}
        variables = {"base_url": "https://test.com", "api_key": "secret123"}
        result = client._replace_templates(template, variables)
        assert result == {"url": "https://test.com/api", "key": "secret123"}

    def test_replace_templates_list(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        template = ["{item1}", "{item2}", "static"]
        variables = {"item1": "first", "item2": "second"}
        result = client._replace_templates(template, variables)
        assert result == ["first", "second", "static"]

    def test_replace_templates_nested(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        template = {"outer": {"inner": "{value}"}}
        variables = {"value": "nested_value"}
        result = client._replace_templates(template, variables)
        assert result == {"outer": {"inner": "nested_value"}}

    def test_replace_templates_no_placeholders(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        template = "static text"
        variables = {"unused": "value"}
        result = client._replace_templates(template, variables)
        assert result == "static text"

    def test_replace_templates_non_string_value(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        template = 123
        variables = {"key": "value"}
        result = client._replace_templates(template, variables)
        assert result == 123


class TestApplyAuth:
    def test_apply_auth_none(self):
        config = {"name": "test", "api_url": "https://test.com", "auth_type": "none"}
        client = ServiceClient(config)
        headers = {"Content-Type": "application/json"}
        params = {"key": "value"}
        new_headers, new_params = client._apply_auth(headers, params)
        assert new_headers == headers
        assert new_params == params

    def test_apply_auth_api_key_header(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "auth_type": "api_key",
            "api_key_env": "TEST_API_KEY",
            "auth_location": "header",
            "auth_key": "X-API-Key",
        }
        client = ServiceClient(config)
        with patch.dict(os.environ, {"TEST_API_KEY": "test_key_123"}):
            headers = {}
            params = {}
            new_headers, new_params = client._apply_auth(headers, params)
            assert new_headers["X-API-Key"] == "test_key_123"

    def test_apply_auth_api_key_params(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "auth_type": "api_key",
            "api_key_env": "TEST_API_KEY",
            "auth_location": "params",
            "auth_key": "api_key",
        }
        client = ServiceClient(config)
        with patch.dict(os.environ, {"TEST_API_KEY": "test_key_123"}):
            headers = {}
            params = {}
            new_headers, new_params = client._apply_auth(headers, params)
            assert new_params["api_key"] == "test_key_123"

    def test_apply_auth_bearer(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "auth_type": "bearer",
            "api_key_env": "TEST_TOKEN",
        }
        client = ServiceClient(config)
        with patch.dict(os.environ, {"TEST_TOKEN": "bearer_token_123"}):
            headers = {}
            params = {}
            new_headers, new_params = client._apply_auth(headers, params)
            assert new_headers["Authorization"] == "Bearer bearer_token_123"

    def test_apply_auth_missing_api_key(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "auth_type": "bearer",
            "api_key_env": "NON_EXISTING_KEY",
        }
        client = ServiceClient(config)
        headers = {}
        params = {}
        new_headers, new_params = client._apply_auth(headers, params)
        assert "Authorization" not in new_headers


class TestBuildRequest:
    def test_build_request_basic(self):
        config = {
            "name": "test",
            "api_url": "https://api.test.com/prompt/{prompt}",
            "request_method": "GET",
            "request_params": {"width": "{width}", "height": "{height}"},
            "auth_type": "none",
        }
        client = ServiceClient(config)
        url, headers, params, body = client.build_request(
            prompt="a cat", width=512, height=512
        )
        assert "a%20cat" in url or "a cat" in url
        assert params["width"] == "512"
        assert params["height"] == "512"
        assert body is None

    def test_build_request_with_model(self):
        config = {
            "name": "test",
            "api_url": "https://api.test.com",
            "request_method": "POST",
            "request_body": {"prompt": "{prompt}", "model": "{model}"},
            "auth_type": "none",
        }
        client = ServiceClient(config)
        url, headers, params, body = client.build_request(
            prompt="test", model="dall-e"
        )
        assert body["prompt"] == "test"
        assert body["model"] == "dall-e"

    def test_build_request_with_kwargs(self):
        config = {
            "name": "test",
            "api_url": "https://api.test.com/{custom}",
            "request_method": "GET",
            "auth_type": "none",
        }
        client = ServiceClient(config)
        url, headers, params, body = client.build_request(
            prompt="test", custom="custom_value"
        )
        assert "custom_value" in url


class TestProcessResponse:
    def test_process_response_binary(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "response_type": "binary",
        }
        client = ServiceClient(config)
        mock_response = MagicMock()
        mock_response.content = b"fake_image_data"
        success, data, error = client._process_response(mock_response)
        assert success is True
        assert data == b"fake_image_data"
        assert error == ""

    def test_process_response_image_url(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "response_type": "image_url",
        }
        client = ServiceClient(config)
        mock_response = MagicMock()
        mock_response.text = "https://example.com/image.png"
        with patch.object(client, "_download_image") as mock_download:
            mock_download.return_value = (True, b"image_data", "")
            success, data, error = client._process_response(mock_response)
            assert success is True

    def test_process_response_json(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "response_type": "json",
            "image_url_path": "data.url",
        }
        client = ServiceClient(config)
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"url": "https://example.com/image.png"}}
        with patch.object(client, "_download_image") as mock_download:
            mock_download.return_value = (True, b"image_data", "")
            success, data, error = client._process_response(mock_response)
            assert success is True

    def test_process_response_invalid_image_url(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "response_type": "image_url",
        }
        client = ServiceClient(config)
        mock_response = MagicMock()
        mock_response.text = "not_a_url"
        success, data, error = client._process_response(mock_response)
        assert success is False
        assert "无效" in error or "invalid" in error.lower()


class TestExtractImageUrl:
    def test_extract_image_url_simple(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "image_url_path": "url",
        }
        client = ServiceClient(config)
        mock_response = MagicMock()
        mock_response.json.return_value = {"url": "https://example.com/image.png"}
        result = client._extract_image_url(mock_response)
        assert result == "https://example.com/image.png"

    def test_extract_image_url_nested(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "image_url_path": "data.image.url",
        }
        client = ServiceClient(config)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {"image": {"url": "https://example.com/nested.png"}}
        }
        result = client._extract_image_url(mock_response)
        assert result == "https://example.com/nested.png"

    def test_extract_image_url_array_index(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "image_url_path": "data.0.url",
        }
        client = ServiceClient(config)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"url": "https://example.com/array.png"}]
        }
        result = client._extract_image_url(mock_response)
        assert result == "https://example.com/array.png"

    def test_extract_image_url_not_found(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "image_url_path": "missing.path",
        }
        client = ServiceClient(config)
        mock_response = MagicMock()
        mock_response.json.return_value = {"other": "data"}
        result = client._extract_image_url(mock_response)
        assert result == ""

    def test_extract_image_url_no_path(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "image_url_path": None,
        }
        client = ServiceClient(config)
        mock_response = MagicMock()
        result = client._extract_image_url(mock_response)
        assert result == ""


class TestDownloadImage:
    def test_download_image_success(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        mock_response = MagicMock()
        mock_response.content = b"image_data"
        mock_response.raise_for_status = MagicMock()
        with patch("requests.get", return_value=mock_response):
            success, data, error = client._download_image("https://example.com/image.png")
            assert success is True
            assert data == b"image_data"

    def test_download_image_failure(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        with patch(
            "requests.get", side_effect=requests.exceptions.RequestException("Network error")
        ):
            success, data, error = client._download_image("https://example.com/image.png")
            assert success is False
            assert data == b""
            assert "失败" in error or "error" in error.lower()


class TestHandleError:
    def test_handle_error_timeout(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        error = requests.exceptions.Timeout()
        message = client._handle_error(error, 1)
        assert "超时" in message or "timeout" in message.lower()

    def test_handle_error_connection(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        error = requests.exceptions.ConnectionError()
        message = client._handle_error(error, 1)
        assert "连接" in message or "connection" in message.lower()

    def test_handle_error_http(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        mock_response = MagicMock()
        mock_response.status_code = 404
        error = requests.exceptions.HTTPError()
        error.response = mock_response
        message = client._handle_error(error, 1)
        assert "404" in message or "HTTP" in message

    def test_handle_error_unknown(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        error = Exception("Unknown error")
        message = client._handle_error(error, 1)
        assert "未知" in message or "Unknown" in message or "失败" in message


class TestRequest:
    def test_request_get_success(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "request_method": "GET",
            "response_type": "binary",
            "auth_type": "none",
        }
        client = ServiceClient(config)
        mock_response = MagicMock()
        mock_response.content = b"image_data"
        mock_response.raise_for_status = MagicMock()
        with patch("requests.get", return_value=mock_response):
            success, data, error = client.request(prompt="test")
            assert success is True
            assert data == b"image_data"

    def test_request_post_success(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "request_method": "POST",
            "request_body": {"prompt": "{prompt}"},
            "response_type": "binary",
            "auth_type": "none",
        }
        client = ServiceClient(config)
        mock_response = MagicMock()
        mock_response.content = b"image_data"
        mock_response.raise_for_status = MagicMock()
        with patch("requests.post", return_value=mock_response):
            success, data, error = client.request(prompt="test")
            assert success is True

    def test_request_retry_on_failure(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "request_method": "GET",
            "response_type": "binary",
            "auth_type": "none",
        }
        retry_config = {"max_retries": 2, "retry_interval": 0.1, "timeout": 10}
        client = ServiceClient(config, retry_config)
        with patch(
            "requests.get", side_effect=requests.exceptions.Timeout()
        ):
            success, data, error = client.request(prompt="test")
            assert success is False
            assert error is not None

    def test_request_all_retries_fail(self):
        config = {
            "name": "test",
            "api_url": "https://test.com",
            "request_method": "GET",
            "response_type": "binary",
            "auth_type": "none",
        }
        retry_config = {"max_retries": 2, "retry_interval": 0.1, "timeout": 10}
        client = ServiceClient(config, retry_config)
        with patch(
            "requests.get", side_effect=requests.exceptions.ConnectionError()
        ):
            success, data, error = client.request(prompt="test")
            assert success is False
            assert data == b""

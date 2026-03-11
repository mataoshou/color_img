import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.service_client import ServiceClient


class TestAsyncConfigLoading:
    def test_async_config_loading_basic(self):
        config = {
            "name": "async_platform",
            "api_url": "https://api.async.com/submit",
            "is_async": True,
            "async_config": {
                "task_id_path": "data.task_id",
                "status_url": "https://api.async.com/status/{task_id}",
                "status_path": "status",
                "status_complete_value": "completed",
                "result_url_path": "result.url",
                "poll_interval": 5,
                "max_poll_time": 300,
            },
        }
        client = ServiceClient(config)
        
        assert client.is_async is True
        assert client.task_id_path == "data.task_id"
        assert client.status_url == "https://api.async.com/status/{task_id}"
        assert client.status_path == "status"
        assert client.status_complete_value == "completed"
        assert client.result_url_path == "result.url"
        assert client.poll_interval == 5
        assert client.max_poll_time == 300

    def test_async_config_loading_defaults(self):
        config = {
            "name": "async_platform",
            "api_url": "https://api.async.com/submit",
            "is_async": True,
            "async_config": {
                "task_id_path": "task_id",
                "status_url": "https://api.async.com/status/{task_id}",
                "status_path": "status",
                "status_complete_value": "done",
            },
        }
        client = ServiceClient(config)
        
        assert client.poll_interval == 10
        assert client.max_poll_time == 600

    def test_async_config_loading_not_async(self):
        config = {
            "name": "sync_platform",
            "api_url": "https://api.sync.com/generate",
            "is_async": False,
        }
        client = ServiceClient(config)
        
        assert client.is_async is False
        assert not hasattr(client, "task_id_path") or client.task_id_path == ""

    def test_async_config_loading_missing_async_config(self):
        config = {
            "name": "async_platform",
            "api_url": "https://api.async.com/submit",
            "is_async": True,
        }
        client = ServiceClient(config)
        
        assert client.is_async is True

    def test_async_config_with_image_url_path(self):
        config = {
            "name": "async_platform",
            "api_url": "https://api.async.com/submit",
            "is_async": True,
            "image_url_path": "data.image_url",
            "async_config": {
                "task_id_path": "task_id",
                "status_url": "https://api.async.com/status/{task_id}",
                "status_path": "status",
                "status_complete_value": "completed",
            },
        }
        client = ServiceClient(config)
        
        assert client.image_url_path == "data.image_url"


class TestResultUrlPathBackwardCompatibility:
    def test_result_url_path_backward_compatibility_with_result_url_path(self):
        config = {
            "name": "test_platform",
            "api_url": "https://api.test.com",
            "result_url_path": "data.result_url",
        }
        client = ServiceClient(config)
        
        assert client.result_url_path == "data.result_url"

    def test_result_url_path_backward_compatibility_with_image_url_path(self):
        config = {
            "name": "test_platform",
            "api_url": "https://api.test.com",
            "image_url_path": "data.image_url",
        }
        client = ServiceClient(config)
        
        assert client.result_url_path == "data.image_url"

    def test_result_url_path_backward_compatibility_both_specified(self):
        config = {
            "name": "test_platform",
            "api_url": "https://api.test.com",
            "image_url_path": "data.image_url",
            "result_url_path": "data.result_url",
        }
        client = ServiceClient(config)
        
        assert client.result_url_path == "data.result_url"

    def test_result_url_path_backward_compatibility_neither_specified(self):
        config = {
            "name": "test_platform",
            "api_url": "https://api.test.com",
        }
        client = ServiceClient(config)
        
        assert client.result_url_path == ""

    def test_result_url_path_backward_compatibility_empty_result_url_path(self):
        config = {
            "name": "test_platform",
            "api_url": "https://api.test.com",
            "image_url_path": "data.image_url",
            "result_url_path": "",
        }
        client = ServiceClient(config)
        
        assert client.result_url_path == "data.image_url"

    def test_result_url_path_backward_compatibility_none_result_url_path(self):
        config = {
            "name": "test_platform",
            "api_url": "https://api.test.com",
            "image_url_path": "data.image_url",
            "result_url_path": None,
        }
        client = ServiceClient(config)
        
        assert client.result_url_path == "data.image_url"


class TestExtractPathValue:
    def test_extract_path_value_simple(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        
        data = {"url": "https://example.com/result.mp4"}
        result = client._extract_path_value(data, "url")
        
        assert result == "https://example.com/result.mp4"

    def test_extract_path_value_nested(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        
        data = {"data": {"result": {"url": "https://example.com/nested.mp4"}}}
        result = client._extract_path_value(data, "data.result.url")
        
        assert result == "https://example.com/nested.mp4"

    def test_extract_path_value_array_index(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        
        data = {"results": [{"url": "https://example.com/first.mp4"}, {"url": "https://example.com/second.mp4"}]}
        result = client._extract_path_value(data, "results.0.url")
        
        assert result == "https://example.com/first.mp4"

    def test_extract_path_value_array_last_index(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        
        data = {"results": [{"url": "https://example.com/first.mp4"}, {"url": "https://example.com/second.mp4"}]}
        result = client._extract_path_value(data, "results.1.url")
        
        assert result == "https://example.com/second.mp4"

    def test_extract_path_value_not_found(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        
        data = {"other": "data"}
        result = client._extract_path_value(data, "missing.path")
        
        assert result is None

    def test_extract_path_value_empty_path(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        
        data = {"url": "https://example.com/result.mp4"}
        result = client._extract_path_value(data, "")
        
        assert result is None

    def test_extract_path_value_none_path(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        
        data = {"url": "https://example.com/result.mp4"}
        result = client._extract_path_value(data, None)
        
        assert result is None

    def test_extract_path_value_invalid_array_index(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        
        data = {"results": [{"url": "https://example.com/first.mp4"}]}
        try:
            result = client._extract_path_value(data, "results.5.url")
            assert result is None
        except IndexError:
            pass

    def test_extract_path_value_mixed_types(self):
        config = {"name": "test", "api_url": "https://test.com"}
        client = ServiceClient(config)
        
        data = {"items": [{"nested": {"value": 42}}]}
        result = client._extract_path_value(data, "items.0.nested.value")
        
        assert result == 42


class TestAsyncRequest:
    def test_async_request_success(self):
        config = {
            "name": "async_platform",
            "api_url": "https://api.async.com/submit",
            "request_method": "POST",
            "request_body": {"prompt": "{prompt}"},
            "response_type": "json",
            "auth_type": "none",
            "is_async": True,
            "async_config": {
                "task_id_path": "task_id",
                "status_url": "https://api.async.com/status/{task_id}",
                "status_path": "status",
                "status_complete_value": "completed",
                "result_url_path": "result.url",
                "poll_interval": 0.1,
                "max_poll_time": 5,
            },
        }
        client = ServiceClient(config)
        
        submit_response = MagicMock()
        submit_response.json.return_value = {"task_id": "task123"}
        submit_response.raise_for_status = MagicMock()
        
        poll_response_pending = MagicMock()
        poll_response_pending.json.return_value = {"status": "pending"}
        poll_response_pending.raise_for_status = MagicMock()
        
        poll_response_completed = MagicMock()
        poll_response_completed.json.return_value = {
            "status": "completed",
            "result": {"url": "https://example.com/video.mp4"},
        }
        poll_response_completed.raise_for_status = MagicMock()
        
        download_response = MagicMock()
        download_response.content = b"video_data"
        download_response.raise_for_status = MagicMock()
        
        with patch("requests.post", return_value=submit_response):
            with patch("requests.get", side_effect=[poll_response_pending, poll_response_completed, download_response]):
                success, data, error = client.request(prompt="test video")
                
                assert success is True
                assert data == b"video_data"
                assert error == "" or error is None

    def test_async_request_no_task_id(self):
        config = {
            "name": "async_platform",
            "api_url": "https://api.async.com/submit",
            "request_method": "POST",
            "auth_type": "none",
            "is_async": True,
            "async_config": {
                "task_id_path": "task_id",
                "status_url": "https://api.async.com/status/{task_id}",
                "status_path": "status",
                "status_complete_value": "completed",
                "result_url_path": "result.url",
            },
        }
        client = ServiceClient(config)
        
        submit_response = MagicMock()
        submit_response.json.return_value = {"no_task_id": "value"}
        submit_response.raise_for_status = MagicMock()
        
        with patch("requests.post", return_value=submit_response):
            success, data, error = client.request(prompt="test")
            
            assert success is False
            assert "task_id" in error

    def test_async_request_poll_timeout(self):
        config = {
            "name": "async_platform",
            "api_url": "https://api.async.com/submit",
            "request_method": "POST",
            "auth_type": "none",
            "is_async": True,
            "async_config": {
                "task_id_path": "task_id",
                "status_url": "https://api.async.com/status/{task_id}",
                "status_path": "status",
                "status_complete_value": "completed",
                "result_url_path": "result.url",
                "poll_interval": 0.1,
                "max_poll_time": 0.5,
            },
        }
        client = ServiceClient(config)
        
        submit_response = MagicMock()
        submit_response.json.return_value = {"task_id": "task123"}
        submit_response.raise_for_status = MagicMock()
        
        poll_response = MagicMock()
        poll_response.json.return_value = {"status": "pending"}
        poll_response.raise_for_status = MagicMock()
        
        with patch("requests.post", return_value=submit_response):
            with patch("requests.get", return_value=poll_response):
                success, data, error = client.request(prompt="test")
                
                assert success is False
                assert "timeout" in error.lower() or "超时" in error

    def test_async_request_no_result_url(self):
        config = {
            "name": "async_platform",
            "api_url": "https://api.async.com/submit",
            "request_method": "POST",
            "auth_type": "none",
            "is_async": True,
            "async_config": {
                "task_id_path": "task_id",
                "status_url": "https://api.async.com/status/{task_id}",
                "status_path": "status",
                "status_complete_value": "completed",
                "result_url_path": "result.url",
                "poll_interval": 0.1,
            },
        }
        client = ServiceClient(config)
        
        submit_response = MagicMock()
        submit_response.json.return_value = {"task_id": "task123"}
        submit_response.raise_for_status = MagicMock()
        
        poll_response = MagicMock()
        poll_response.json.return_value = {
            "status": "completed",
            "result": {},
        }
        poll_response.raise_for_status = MagicMock()
        
        with patch("requests.post", return_value=submit_response):
            with patch("requests.get", return_value=poll_response):
                success, data, error = client.request(prompt="test")
                
                assert success is False
                assert "结果" in error or "result" in error.lower() or "URL" in error

    def test_async_request_invalid_json_response(self):
        config = {
            "name": "async_platform",
            "api_url": "https://api.async.com/submit",
            "request_method": "POST",
            "auth_type": "none",
            "is_async": True,
            "async_config": {
                "task_id_path": "task_id",
                "status_url": "https://api.async.com/status/{task_id}",
                "status_path": "status",
                "status_complete_value": "completed",
                "result_url_path": "result.url",
            },
        }
        client = ServiceClient(config)
        
        submit_response = MagicMock()
        submit_response.json.side_effect = ValueError("Invalid JSON")
        submit_response.raise_for_status = MagicMock()
        
        with patch("requests.post", return_value=submit_response):
            success, data, error = client.request(prompt="test")
            
            assert success is False
            assert "JSON" in error or "json" in error.lower()

    def test_async_request_invalid_poll_json_response(self):
        config = {
            "name": "async_platform",
            "api_url": "https://api.async.com/submit",
            "request_method": "POST",
            "auth_type": "none",
            "is_async": True,
            "async_config": {
                "task_id_path": "task_id",
                "status_url": "https://api.async.com/status/{task_id}",
                "status_path": "status",
                "status_complete_value": "completed",
                "result_url_path": "result.url",
                "poll_interval": 0.1,
            },
        }
        client = ServiceClient(config)
        
        submit_response = MagicMock()
        submit_response.json.return_value = {"task_id": "task123"}
        submit_response.raise_for_status = MagicMock()
        
        poll_response = MagicMock()
        poll_response.json.side_effect = ValueError("Invalid JSON")
        poll_response.raise_for_status = MagicMock()
        
        with patch("requests.post", return_value=submit_response):
            with patch("requests.get", return_value=poll_response):
                success, data, error = client.request(prompt="test")
                
                assert success is False
                assert "JSON" in error or "json" in error.lower()

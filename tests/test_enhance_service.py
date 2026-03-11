import os
import pytest
from unittest.mock import patch, MagicMock

from src.enhance_service import (
    EnhanceService,
    get_enhance_service,
    enhance_prompt,
    DEFAULT_SYSTEM_PROMPT
)


class TestEnhanceServiceInit:
    def test_init_default_values(self):
        service = EnhanceService()
        assert service.enabled == True
        assert service.model == "glm-4-flash"
        assert service.api_url == "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        assert service.api_key_env == "GLM_API_KEY"
        assert service.max_tokens == 1000
        assert service.temperature == 0.7
        assert service.system_prompt == DEFAULT_SYSTEM_PROMPT
        assert service.timeout == 30

    def test_init_with_config(self):
        config = {
            "enabled": False,
            "model": "custom-model",
            "api_url": "https://custom.api.com",
            "api_key_env": "CUSTOM_API_KEY",
            "max_tokens": 500,
            "temperature": 0.5,
            "system_prompt": "Custom prompt",
            "timeout": 60
        }
        service = EnhanceService(config)
        assert service.enabled == False
        assert service.model == "custom-model"
        assert service.api_url == "https://custom.api.com"
        assert service.api_key_env == "CUSTOM_API_KEY"
        assert service.max_tokens == 500
        assert service.temperature == 0.5
        assert service.system_prompt == "Custom prompt"
        assert service.timeout == 60

    def test_init_partial_config(self):
        config = {"model": "test-model"}
        service = EnhanceService(config)
        assert service.model == "test-model"
        assert service.enabled == True
        assert service.api_key_env == "GLM_API_KEY"


class TestGetApiKey:
    def test_get_api_key_from_env(self):
        with patch.dict(os.environ, {"GLM_API_KEY": "test_key_123"}):
            service = EnhanceService()
            key = service._get_api_key()
            assert key == "test_key_123"

    def test_get_api_key_cached(self):
        with patch.dict(os.environ, {"GLM_API_KEY": "test_key_456"}):
            service = EnhanceService()
            key1 = service._get_api_key()
            key2 = service._get_api_key()
            assert key1 == key2 == "test_key_456"

    def test_get_api_key_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            if "GLM_API_KEY" in os.environ:
                del os.environ["GLM_API_KEY"]
            service = EnhanceService()
            key = service._get_api_key()
            assert key is None

    def test_get_api_key_custom_env_name(self):
        with patch.dict(os.environ, {"CUSTOM_KEY": "custom_value"}):
            service = EnhanceService({"api_key_env": "CUSTOM_KEY"})
            key = service._get_api_key()
            assert key == "custom_value"


class TestBuildRequestBody:
    def test_build_request_body_basic(self):
        service = EnhanceService()
        body = service._build_request_body("test prompt")
        assert body["model"] == "glm-4-flash"
        assert len(body["messages"]) == 2
        assert body["messages"][0]["role"] == "system"
        assert body["messages"][1]["role"] == "user"
        assert body["messages"][1]["content"] == "test prompt"
        assert body["max_tokens"] == 1000
        assert body["temperature"] == 0.7

    def test_build_request_body_custom_system_prompt(self):
        service = EnhanceService({"system_prompt": "Custom system prompt"})
        body = service._build_request_body("user input")
        assert body["messages"][0]["content"] == "Custom system prompt"


class TestBuildHeaders:
    def test_build_headers_with_api_key(self):
        with patch.dict(os.environ, {"GLM_API_KEY": "test_key"}):
            service = EnhanceService()
            headers = service._build_headers()
            assert headers["Content-Type"] == "application/json"
            assert headers["Authorization"] == "Bearer test_key"

    def test_build_headers_without_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            if "GLM_API_KEY" in os.environ:
                del os.environ["GLM_API_KEY"]
            service = EnhanceService()
            headers = service._build_headers()
            assert headers["Content-Type"] == "application/json"
            assert "Authorization" not in headers


class TestCallApi:
    @patch('src.enhance_service.requests.post')
    def test_call_api_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Enhanced prompt result"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"GLM_API_KEY": "test_key"}):
            service = EnhanceService()
            success, result, error = service._call_api("test input")
            assert success == True
            assert result == "Enhanced prompt result"
            assert error is None

    @patch('src.enhance_service.requests.post')
    def test_call_api_no_api_key(self, mock_post):
        with patch.dict(os.environ, {}, clear=True):
            if "GLM_API_KEY" in os.environ:
                del os.environ["GLM_API_KEY"]
            service = EnhanceService()
            success, result, error = service._call_api("test input")
            assert success == False
            assert result == ""
            assert "API key not found" in error

    @patch('src.enhance_service.requests.post')
    def test_call_api_auth_failed(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"GLM_API_KEY": "invalid_key"}):
            service = EnhanceService()
            success, result, error = service._call_api("test input")
            assert success == False
            assert "authentication failed" in error.lower()

    @patch('src.enhance_service.requests.post')
    def test_call_api_rate_limit(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"GLM_API_KEY": "test_key"}):
            service = EnhanceService()
            success, result, error = service._call_api("test input")
            assert success == False
            assert "rate limit" in error.lower()

    @patch('src.enhance_service.requests.post')
    def test_call_api_server_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"GLM_API_KEY": "test_key"}):
            service = EnhanceService()
            success, result, error = service._call_api("test input")
            assert success == False
            assert "server error" in error.lower()

    @patch('src.enhance_service.requests.post')
    def test_call_api_timeout(self, mock_post):
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()

        with patch.dict(os.environ, {"GLM_API_KEY": "test_key"}):
            service = EnhanceService()
            success, result, error = service._call_api("test input")
            assert success == False
            assert "timeout" in error.lower()

    @patch('src.enhance_service.requests.post')
    def test_call_api_connection_error(self, mock_post):
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()

        with patch.dict(os.environ, {"GLM_API_KEY": "test_key"}):
            service = EnhanceService()
            success, result, error = service._call_api("test input")
            assert success == False
            assert "connection" in error.lower()

    @patch('src.enhance_service.requests.post')
    def test_call_api_missing_choices(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"GLM_API_KEY": "test_key"}):
            service = EnhanceService()
            success, result, error = service._call_api("test input")
            assert success == False
            assert "missing choices" in error

    @patch('src.enhance_service.requests.post')
    def test_call_api_empty_content(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": ""}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"GLM_API_KEY": "test_key"}):
            service = EnhanceService()
            success, result, error = service._call_api("test input")
            assert success == False
            assert "missing content" in error


class TestEnhance:
    @patch('src.enhance_service.requests.post')
    def test_enhance_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Enhanced: a cute cat"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"GLM_API_KEY": "test_key"}):
            service = EnhanceService()
            result = service.enhance("一只猫")
            assert result == "Enhanced: a cute cat"

    def test_enhance_disabled(self):
        service = EnhanceService({"enabled": False})
        result = service.enhance("test input")
        assert result == "test input"

    def test_enhance_empty_input(self):
        service = EnhanceService()
        result = service.enhance("")
        assert result == ""

    def test_enhance_whitespace_input(self):
        service = EnhanceService()
        result = service.enhance("   ")
        assert result == "   "

    @patch('src.enhance_service.requests.post')
    def test_enhance_fallback_on_error(self, mock_post):
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()

        with patch.dict(os.environ, {"GLM_API_KEY": "test_key"}):
            service = EnhanceService()
            result = service.enhance("original input")
            assert result == "original input"

    @patch('src.enhance_service.requests.post')
    def test_enhance_strips_result(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "  trimmed result  "}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"GLM_API_KEY": "test_key"}):
            service = EnhanceService()
            result = service.enhance("input")
            assert result == "trimmed result"


class TestIsAvailable:
    def test_is_available_with_key(self):
        with patch.dict(os.environ, {"GLM_API_KEY": "test_key"}):
            service = EnhanceService()
            assert service.is_available() == True

    def test_is_available_without_key(self):
        with patch.dict(os.environ, {}, clear=True):
            if "GLM_API_KEY" in os.environ:
                del os.environ["GLM_API_KEY"]
            service = EnhanceService()
            assert service.is_available() == False

    def test_is_available_disabled(self):
        with patch.dict(os.environ, {"GLM_API_KEY": "test_key"}):
            service = EnhanceService({"enabled": False})
            assert service.is_available() == False

    def test_is_available_empty_key(self):
        with patch.dict(os.environ, {"GLM_API_KEY": ""}):
            service = EnhanceService()
            assert service.is_available() == False

    def test_is_available_whitespace_key(self):
        with patch.dict(os.environ, {"GLM_API_KEY": "   "}):
            service = EnhanceService()
            assert service.is_available() == False


class TestModuleFunctions:
    def test_get_enhance_service_singleton(self):
        service1 = get_enhance_service()
        service2 = get_enhance_service()
        assert service1 is service2

    @patch('src.enhance_service.requests.post')
    def test_enhance_prompt_function(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "enhanced result"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"GLM_API_KEY": "test_key"}):
            result = enhance_prompt("test input")
            assert result == "enhanced result"


class TestDefaultSystemPrompt:
    def test_default_prompt_exists(self):
        assert DEFAULT_SYSTEM_PROMPT is not None
        assert len(DEFAULT_SYSTEM_PROMPT) > 0

    def test_default_prompt_contains_guidelines(self):
        assert "translate" in DEFAULT_SYSTEM_PROMPT.lower()
        assert "english" in DEFAULT_SYSTEM_PROMPT.lower()

    def test_default_prompt_has_examples(self):
        assert "一只猫" in DEFAULT_SYSTEM_PROMPT
        assert "cat" in DEFAULT_SYSTEM_PROMPT.lower()

import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.route_service import RouteService


class TestRouteServiceInit:
    def test_init_with_config(self):
        config = {
            "enhance_service": {
                "enabled": True,
                "model": "glm-4",
                "api_url": "https://api.test.com",
                "api_key_env": "TEST_API_KEY",
                "max_tokens": 2000,
                "temperature": 0.5,
                "timeout": 60,
            }
        }
        service = RouteService(config)
        assert service.enabled is True
        assert service.model == "glm-4"
        assert service.api_url == "https://api.test.com"
        assert service.api_key_env == "TEST_API_KEY"
        assert service.max_tokens == 2000
        assert service.temperature == 0.5
        assert service.timeout == 60

    def test_init_default_values(self):
        service = RouteService({})
        assert service.enabled is True
        assert service.model == "glm-4-flash"
        assert service.api_url == "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        assert service.api_key_env == "GLM_API_KEY"
        assert service.max_tokens == 1000
        assert service.temperature == 0.7
        assert service.timeout == 30

    def test_init_disabled(self):
        config = {"enhance_service": {"enabled": False}}
        service = RouteService(config)
        assert service.enabled is False


class TestSelectPlatformStaticScene:
    def test_select_platform_static_scene(self):
        config = {"enhance_service": {"enabled": True}}
        service = RouteService(config)
        
        platforms = [
            {"name": "ImagePlatform", "description": "Generate static images"},
            {"name": "VideoPlatform", "description": "Generate videos"},
        ]
        
        mock_response_content = '{"platform_index": 0, "save_type": "image", "next_step": null, "reason": "Static scene"}'
        
        with patch.object(service, "_call_api", return_value=(True, mock_response_content, None)):
            result = service.select_platform("a photo of a cat", platforms)
            
            assert result["platform"]["name"] == "ImagePlatform"
            assert result["save_type"] == "image"
            assert result["next_step"] is None

    def test_select_platform_static_scene_portrait(self):
        config = {"enhance_service": {"enabled": True}}
        service = RouteService(config)
        
        platforms = [
            {"name": "ImagePlatform", "description": "Generate static images"},
            {"name": "VideoPlatform", "description": "Generate videos"},
        ]
        
        mock_response_content = '{"platform_index": 0, "save_type": "image", "next_step": null, "reason": "Portrait request"}'
        
        with patch.object(service, "_call_api", return_value=(True, mock_response_content, None)):
            result = service.select_platform("a portrait of a woman", platforms)
            
            assert result["save_type"] == "image"
            assert result["next_step"] is None


class TestSelectPlatformDynamicScene:
    def test_select_platform_dynamic_scene(self):
        config = {"enhance_service": {"enabled": True}}
        service = RouteService(config)
        
        platforms = [
            {"name": "ImagePlatform", "description": "Generate static images"},
            {"name": "VideoPlatform", "description": "Generate videos with motion"},
        ]
        
        mock_response_content = '{"platform_index": 1, "save_type": "video", "next_step": null, "reason": "Dynamic scene with motion"}'
        
        with patch.object(service, "_call_api", return_value=(True, mock_response_content, None)):
            result = service.select_platform("a cat running in the park", platforms)
            
            assert result["platform"]["name"] == "VideoPlatform"
            assert result["save_type"] == "video"
            assert result["next_step"] is None

    def test_select_platform_dynamic_scene_flying(self):
        config = {"enhance_service": {"enabled": True}}
        service = RouteService(config)
        
        platforms = [
            {"name": "ImagePlatform", "description": "Generate static images"},
            {"name": "VideoPlatform", "description": "Generate videos with motion"},
        ]
        
        mock_response_content = '{"platform_index": 1, "save_type": "video", "next_step": null, "reason": "Flying action"}'
        
        with patch.object(service, "_call_api", return_value=(True, mock_response_content, None)):
            result = service.select_platform("a bird flying in the sky", platforms)
            
            assert result["save_type"] == "video"


class TestSelectPlatformI2VFlow:
    def test_select_platform_i2v_flow(self):
        config = {"enhance_service": {"enabled": True}}
        service = RouteService(config)
        
        platforms = [
            {"name": "ImagePlatform", "description": "Generate static images"},
            {"name": "VideoPlatform", "description": "Generate videos"},
        ]
        
        mock_response_content = '{"platform_index": 0, "save_type": "image", "next_step": "image-to-video", "reason": "User wants image first then video"}'
        
        with patch.object(service, "_call_api", return_value=(True, mock_response_content, None)):
            result = service.select_platform("generate an image of a cat and make it move", platforms)
            
            assert result["save_type"] == "image"
            assert result["next_step"] == "image-to-video"

    def test_select_platform_i2v_flow_explicit(self):
        config = {"enhance_service": {"enabled": True}}
        service = RouteService(config)
        
        platforms = [
            {"name": "ImagePlatform", "description": "Generate static images"},
            {"name": "VideoPlatform", "description": "Generate videos"},
        ]
        
        mock_response_content = '{"platform_index": 0, "save_type": "image", "next_step": "image-to-video", "reason": "Two-step process requested"}'
        
        with patch.object(service, "_call_api", return_value=(True, mock_response_content, None)):
            result = service.select_platform("create a picture first, then animate it", platforms)
            
            assert result["save_type"] == "image"
            assert result["next_step"] == "image-to-video"


class TestSelectI2VPlatform:
    def test_select_i2v_platform(self):
        config = {"enhance_service": {"enabled": True}}
        service = RouteService(config)
        
        i2v_platforms = [
            {"name": "I2VPlatform1", "description": "Image to video converter 1"},
            {"name": "I2VPlatform2", "description": "Image to video converter 2"},
        ]
        
        mock_response_content = '{"platform_index": 1, "reason": "Better quality for this prompt"}'
        
        with patch.object(service, "_call_api", return_value=(True, mock_response_content, None)):
            result = service.select_i2v_platform("make the cat run", "/path/to/image.png", i2v_platforms)
            
            assert result["platform"]["name"] == "I2VPlatform2"
            assert result["save_type"] == "video"

    def test_select_i2v_platform_single(self):
        config = {"enhance_service": {"enabled": True}}
        service = RouteService(config)
        
        i2v_platforms = [
            {"name": "OnlyI2VPlatform", "description": "The only i2v platform"},
        ]
        
        result = service.select_i2v_platform("animate this", "/path/to/image.png", i2v_platforms)
        
        assert result["platform"]["name"] == "OnlyI2VPlatform"
        assert result["save_type"] == "video"

    def test_select_i2v_platform_disabled(self):
        config = {"enhance_service": {"enabled": False}}
        service = RouteService(config)
        
        i2v_platforms = [
            {"name": "I2VPlatform1", "description": "First i2v platform"},
            {"name": "I2VPlatform2", "description": "Second i2v platform"},
        ]
        
        result = service.select_i2v_platform("animate this", "/path/to/image.png", i2v_platforms)
        
        assert result["platform"]["name"] == "I2VPlatform1"
        assert result["save_type"] == "video"


class TestApiUnavailableFallback:
    def test_api_unavailable_fallback_disabled(self):
        config = {"enhance_service": {"enabled": False}}
        service = RouteService(config)
        
        platforms = [
            {"name": "Platform1", "description": "First platform"},
            {"name": "Platform2", "description": "Second platform"},
        ]
        
        result = service.select_platform("test prompt", platforms)
        
        assert result["platform"]["name"] == "Platform1"
        assert result["save_type"] == "image"
        assert result["next_step"] is None

    def test_api_unavailable_fallback_no_platforms(self):
        config = {"enhance_service": {"enabled": True}}
        service = RouteService(config)
        
        result = service.select_platform("test prompt", [])
        
        assert result["platform"] == {}
        assert result["save_type"] == "image"
        assert result["next_step"] is None

    def test_api_unavailable_fallback_single_platform(self):
        config = {"enhance_service": {"enabled": True}}
        service = RouteService(config)
        
        platforms = [
            {"name": "OnlyPlatform", "description": "The only platform"},
        ]
        
        result = service.select_platform("test prompt", platforms)
        
        assert result["platform"]["name"] == "OnlyPlatform"
        assert result["save_type"] == "image"

    def test_api_unavailable_fallback_api_error(self):
        config = {"enhance_service": {"enabled": True}}
        service = RouteService(config)
        
        platforms = [
            {"name": "Platform1", "description": "First platform"},
            {"name": "Platform2", "description": "Second platform"},
        ]
        
        with patch.object(service, "_call_api", return_value=(False, "", "API error")):
            result = service.select_platform("test prompt", platforms)
            
            assert result["platform"]["name"] == "Platform1"
            assert result["save_type"] == "image"

    def test_api_unavailable_fallback_parse_error(self):
        config = {"enhance_service": {"enabled": True}}
        service = RouteService(config)
        
        platforms = [
            {"name": "Platform1", "description": "First platform"},
            {"name": "Platform2", "description": "Second platform"},
        ]
        
        with patch.object(service, "_call_api", return_value=(True, "invalid json", None)):
            result = service.select_platform("test prompt", platforms)
            
            assert result["platform"]["name"] == "Platform1"

    def test_api_unavailable_fallback_invalid_platform_index(self):
        config = {"enhance_service": {"enabled": True}}
        service = RouteService(config)
        
        platforms = [
            {"name": "Platform1", "description": "First platform"},
        ]
        
        mock_response_content = '{"platform_index": 99, "save_type": "image", "next_step": null}'
        
        with patch.object(service, "_call_api", return_value=(True, mock_response_content, None)):
            result = service.select_platform("test prompt", platforms)
            
            assert result["platform"]["name"] == "Platform1"

    def test_api_unavailable_fallback_invalid_save_type(self):
        config = {"enhance_service": {"enabled": True}}
        service = RouteService(config)
        
        platforms = [
            {"name": "Platform1", "description": "First platform"},
        ]
        
        mock_response_content = '{"platform_index": 0, "save_type": "invalid", "next_step": null}'
        
        with patch.object(service, "_call_api", return_value=(True, mock_response_content, None)):
            result = service.select_platform("test prompt", platforms)
            
            assert result["save_type"] == "image"

    def test_api_unavailable_fallback_invalid_next_step(self):
        config = {"enhance_service": {"enabled": True}}
        service = RouteService(config)
        
        platforms = [
            {"name": "Platform1", "description": "First platform"},
        ]
        
        mock_response_content = '{"platform_index": 0, "save_type": "image", "next_step": "invalid_step"}'
        
        with patch.object(service, "_call_api", return_value=(True, mock_response_content, None)):
            result = service.select_platform("test prompt", platforms)
            
            assert result["next_step"] is None


class TestIsAvailable:
    def test_is_available_with_api_key(self):
        config = {"enhance_service": {"enabled": True, "api_key_env": "TEST_API_KEY"}}
        service = RouteService(config)
        
        with patch.dict(os.environ, {"TEST_API_KEY": "test_key"}):
            assert service.is_available() is True

    def test_is_available_without_api_key(self):
        config = {"enhance_service": {"enabled": True, "api_key_env": "NON_EXISTING_KEY"}}
        service = RouteService(config)
        
        assert service.is_available() is False

    def test_is_available_disabled(self):
        config = {"enhance_service": {"enabled": False}}
        service = RouteService(config)
        
        with patch.dict(os.environ, {"GLM_API_KEY": "test_key"}):
            assert service.is_available() is False

    def test_is_available_empty_api_key(self):
        config = {"enhance_service": {"enabled": True, "api_key_env": "EMPTY_KEY"}}
        service = RouteService(config)
        
        with patch.dict(os.environ, {"EMPTY_KEY": ""}):
            assert service.is_available() is False


class TestBuildPlatformsInfo:
    def test_build_platforms_info(self):
        service = RouteService({})
        
        platforms = [
            {"name": "Platform1", "description": "First platform"},
            {"name": "Platform2", "description": "Second platform"},
        ]
        
        result = service._build_platforms_info(platforms)
        
        assert "[0] Platform1: First platform" in result
        assert "[1] Platform2: Second platform" in result

    def test_build_platforms_info_missing_name(self):
        service = RouteService({})
        
        platforms = [
            {"description": "No name platform"},
        ]
        
        result = service._build_platforms_info(platforms)
        
        assert "Unknown" in result

    def test_build_platforms_info_missing_description(self):
        service = RouteService({})
        
        platforms = [
            {"name": "NoDesc"},
        ]
        
        result = service._build_platforms_info(platforms)
        
        assert "No description" in result


class TestParseJsonResponse:
    def test_parse_json_response_valid(self):
        service = RouteService({})
        
        content = 'Some text {"platform_index": 1, "save_type": "video"} more text'
        result = service._parse_json_response(content)
        
        assert result["platform_index"] == 1
        assert result["save_type"] == "video"

    def test_parse_json_response_no_json(self):
        service = RouteService({})
        
        content = "No JSON here"
        result = service._parse_json_response(content)
        
        assert result is None

    def test_parse_json_response_invalid_json(self):
        service = RouteService({})
        
        content = "{invalid json}"
        result = service._parse_json_response(content)
        
        assert result is None


class TestCallApi:
    def test_call_api_no_api_key(self):
        config = {"enhance_service": {"api_key_env": "NON_EXISTING_KEY"}}
        service = RouteService(config)
        
        success, content, error = service._call_api("system prompt", "user input")
        
        assert success is False
        assert content == ""
        assert "API key not found" in error

    def test_call_api_success(self):
        config = {"enhance_service": {"api_key_env": "TEST_API_KEY"}}
        service = RouteService(config)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "response content"}}]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch.dict(os.environ, {"TEST_API_KEY": "test_key"}):
            with patch("requests.post", return_value=mock_response):
                success, content, error = service._call_api("system prompt", "user input")
                
                assert success is True
                assert content == "response content"
                assert error is None

    def test_call_api_auth_failure(self):
        config = {"enhance_service": {"api_key_env": "TEST_API_KEY"}}
        service = RouteService(config)
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        with patch.dict(os.environ, {"TEST_API_KEY": "test_key"}):
            with patch("requests.post", return_value=mock_response):
                success, content, error = service._call_api("system prompt", "user input")
                
                assert success is False
                assert "authentication failed" in error

    def test_call_api_rate_limit(self):
        config = {"enhance_service": {"api_key_env": "TEST_API_KEY"}}
        service = RouteService(config)
        
        mock_response = MagicMock()
        mock_response.status_code = 429
        
        with patch.dict(os.environ, {"TEST_API_KEY": "test_key"}):
            with patch("requests.post", return_value=mock_response):
                success, content, error = service._call_api("system prompt", "user input")
                
                assert success is False
                assert "rate limit" in error

    def test_call_api_server_error(self):
        config = {"enhance_service": {"api_key_env": "TEST_API_KEY"}}
        service = RouteService(config)
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        
        with patch.dict(os.environ, {"TEST_API_KEY": "test_key"}):
            with patch("requests.post", return_value=mock_response):
                success, content, error = service._call_api("system prompt", "user input")
                
                assert success is False
                assert "server error" in error

    def test_call_api_timeout(self):
        config = {"enhance_service": {"api_key_env": "TEST_API_KEY"}}
        service = RouteService(config)
        
        with patch.dict(os.environ, {"TEST_API_KEY": "test_key"}):
            with patch("requests.post", side_effect=requests.exceptions.Timeout("Timeout")):
                success, content, error = service._call_api("system prompt", "user input")
                
                assert success is False
                assert "timeout" in error.lower() or "超时" in error

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config import ConfigManager, get_default_config
from src.image_saver import ImageSaver
from src.platform_manager import PlatformManager
from src.service_client import ServiceClient


class TestConfigToIntegration:
    def test_config_to_platform_manager(self):
        config = get_default_config()
        manager = PlatformManager(config)
        assert len(manager.platforms) > 0
        assert manager.retry_config is not None

    def test_config_to_image_saver(self):
        config = get_default_config()
        saver = ImageSaver(config)
        assert saver.directory == config["output"]["directory"]

    def test_config_to_service_client(self):
        config = get_default_config()
        platform_config = config["platforms"][0]
        retry_config = config["retry"]
        client = ServiceClient(platform_config, {
            "max_retries": retry_config.get("max_attempts", 3),
            "retry_interval": retry_config.get("delay_seconds", 2),
            "timeout": 60,
        })
        assert client.name == platform_config["name"]


class TestFullWorkflowMocked:
    def test_full_workflow_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = get_default_config()
            config["output"]["directory"] = tmpdir
            config["retry"]["max_attempts"] = 1
            config["retry"]["delay_seconds"] = 0.1
            manager = PlatformManager(config)
            mock_response = MagicMock()
            mock_response.content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
            mock_response.raise_for_status = MagicMock()
            with patch("requests.get", return_value=mock_response):
                success, image_data, error = manager.generate(
                    prompt="test prompt",
                    width=512,
                    height=512
                )
            assert success is True
            assert image_data is not None
            saver = ImageSaver(config)
            saved_path = saver.save_image(image_data, prompt="test prompt")
            assert os.path.exists(saved_path)

    def test_full_workflow_with_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = get_default_config()
            config["output"]["directory"] = tmpdir
            config["retry"]["max_attempts"] = 1
            config["retry"]["delay_seconds"] = 0.1
            config["platforms"] = [
                {
                    "name": "failing_platform",
                    "api_url": "https://fail.com/{prompt}",
                    "request_method": "GET",
                    "auth_type": "none",
                    "response_type": "binary",
                },
                {
                    "name": "success_platform",
                    "api_url": "https://success.com/{prompt}",
                    "request_method": "GET",
                    "auth_type": "none",
                    "response_type": "binary",
                },
            ]
            manager = PlatformManager(config)
            call_count = [0]

            def mock_get_side_effect(*args, **kwargs):
                call_count[0] += 1
                if "fail.com" in str(args[0]):
                    raise Exception("Simulated failure")
                mock_resp = MagicMock()
                mock_resp.content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
                mock_resp.raise_for_status = MagicMock()
                return mock_resp

            with patch("requests.get", side_effect=mock_get_side_effect):
                with patch("time.sleep"):
                    success, image_data, error = manager.generate(prompt="test")
            assert success is True
            assert manager.current_platform_name == "success_platform"

    def test_full_workflow_all_fail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = get_default_config()
            config["output"]["directory"] = tmpdir
            config["retry"]["max_attempts"] = 1
            config["retry"]["delay_seconds"] = 0.1
            config["platforms"] = [
                {
                    "name": "platform1",
                    "api_url": "https://fail1.com",
                    "request_method": "GET",
                    "auth_type": "none",
                    "response_type": "binary",
                },
                {
                    "name": "platform2",
                    "api_url": "https://fail2.com",
                    "request_method": "GET",
                    "auth_type": "none",
                    "response_type": "binary",
                },
            ]
            manager = PlatformManager(config)
            with patch("requests.get", side_effect=Exception("Network error")):
                with patch("time.sleep"):
                    success, image_data, error = manager.generate(prompt="test")
            assert success is False
            assert "所有平台均失败" in error


class TestConfigPersistenceIntegration:
    def test_config_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ConfigManager._instance = None
            ConfigManager._config = None
            ConfigManager._config_path = None
            config_path = os.path.join(tmpdir, "test_config.json")
            manager = ConfigManager()
            config = manager.load_config(config_path)
            config["output"]["directory"] = "custom_output"
            manager.save_config()
            ConfigManager._instance = None
            ConfigManager._config = None
            ConfigManager._config_path = None
            new_manager = ConfigManager()
            loaded_config = new_manager.load_config(config_path)
            assert loaded_config["output"]["directory"] == "custom_output"


class TestImageSaverIntegration:
    def test_image_saver_with_real_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = os.path.join(tmpdir, "images", "2024", "01")
            config = {
                "output": {
                    "directory": nested_dir,
                    "naming": "sequential",
                }
            }
            saver = ImageSaver(config)
            png_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
            path1 = saver.save_image(png_data)
            path2 = saver.save_image(png_data)
            path3 = saver.save_image(png_data)
            assert os.path.exists(path1)
            assert os.path.exists(path2)
            assert os.path.exists(path3)
            assert path1 != path2
            assert path2 != path3

    def test_image_saver_with_prompt_naming(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "output": {
                    "directory": tmpdir,
                    "naming": "prompt",
                }
            }
            saver = ImageSaver(config)
            image_data = b"fake_image"
            path = saver.save_image(image_data, prompt="a beautiful sunset", format="png")
            assert os.path.exists(path)


class TestServiceClientIntegration:
    def test_service_client_build_request_integration(self):
        config = {
            "name": "test_integration",
            "api_url": "https://api.example.com/v1/generate",
            "request_method": "POST",
            "request_params": {"size": "{width}x{height}"},
            "request_headers": {"Content-Type": "application/json"},
            "request_body": {
                "prompt": "{prompt}",
                "model": "{model}",
                "size": "{width}x{height}",
            },
            "auth_type": "bearer",
            "api_key_env": "TEST_API_KEY",
            "response_type": "json",
            "image_url_path": "data.url",
        }
        retry_config = {"max_retries": 3, "retry_interval": 1, "timeout": 30}
        with patch.dict(os.environ, {"TEST_API_KEY": "test_key_123"}):
            client = ServiceClient(config, retry_config)
            url, headers, params, body = client.build_request(
                prompt="a cat",
                model="dall-e-3",
                width=1024,
                height=1024,
            )
            assert url == "https://api.example.com/v1/generate"
            assert headers["Content-Type"] == "application/json"
            assert headers["Authorization"] == "Bearer test_key_123"
            assert body["prompt"] == "a cat"
            assert body["model"] == "dall-e-3"
            assert body["size"] == "1024x1024"


class TestPlatformManagerIntegration:
    def test_platform_manager_switch_platforms(self):
        config = {
            "platforms": [
                {"name": "platform_a", "api_url": "https://a.com"},
                {"name": "platform_b", "api_url": "https://b.com"},
                {"name": "platform_c", "api_url": "https://c.com"},
            ],
            "retry": {"max_attempts": 1, "delay_seconds": 0.1},
            "image": {},
        }
        manager = PlatformManager(config)
        assert manager.set_platform("platform_b")
        assert manager.get_current_platform() == "platform_b"
        assert manager.get_platform_index() == 1
        assert manager.set_platform("platform_c")
        assert manager.get_platform_index() == 2

    def test_platform_manager_dynamic_platform_management(self):
        config = {
            "platforms": [
                {"name": "initial", "api_url": "https://initial.com"},
            ],
            "retry": {"max_attempts": 1, "delay_seconds": 0.1},
        }
        manager = PlatformManager(config)
        assert len(manager.get_available_platforms()) == 1
        manager.add_platform({
            "name": "added_platform",
            "api_url": "https://added.com",
        })
        assert len(manager.get_available_platforms()) == 2
        assert "added_platform" in manager.get_available_platforms()
        manager.remove_platform("initial")
        assert len(manager.get_available_platforms()) == 1
        assert "initial" not in manager.get_available_platforms()


class TestEndToEndMocked:
    def test_end_to_end_workflow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ConfigManager._instance = None
            ConfigManager._config = None
            ConfigManager._config_path = None
            config_path = os.path.join(tmpdir, "config.json")
            config_manager = ConfigManager()
            config = config_manager.load_config(config_path)
            config["output"]["directory"] = os.path.join(tmpdir, "output")
            config["retry"]["max_attempts"] = 1
            config["retry"]["delay_seconds"] = 0.1
            config_manager.save_config()
            manager = PlatformManager(config)
            mock_response = MagicMock()
            mock_response.content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
            mock_response.raise_for_status = MagicMock()
            with patch("requests.get", return_value=mock_response):
                success, image_data, error = manager.generate(
                    prompt="a beautiful landscape",
                    width=1024,
                    height=768,
                )
            assert success is True
            saver = ImageSaver(config)
            saved_path = saver.save_image(
                image_data,
                prompt="a beautiful landscape",
                format="png",
            )
            assert os.path.exists(saved_path)
            assert saved_path.endswith(".png")
            with open(saved_path, "rb") as f:
                saved_data = f.read()
            assert saved_data == image_data

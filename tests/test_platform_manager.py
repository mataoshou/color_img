from unittest.mock import MagicMock, patch

import pytest

from src.platform_manager import PlatformManager


class TestPlatformManagerInit:
    def test_init_with_config(self):
        config = {
            "platforms": [{"name": "test_platform", "api_url": "https://test.com"}],
            "retry": {"max_attempts": 3, "delay_seconds": 2},
        }
        manager = PlatformManager(config)
        assert len(manager.platforms) == 1
        assert manager.platforms[0]["name"] == "test_platform"

    def test_init_empty_platforms(self):
        config = {"platforms": [], "retry": {}}
        manager = PlatformManager(config)
        assert manager.platforms == []

    def test_init_clients_created(self):
        config = {
            "platforms": [
                {"name": "platform1", "api_url": "https://test1.com"},
                {"name": "platform2", "api_url": "https://test2.com"},
            ],
            "retry": {},
        }
        manager = PlatformManager(config)
        assert "platform1" in manager._clients
        assert "platform2" in manager._clients

    def test_init_with_retry_config(self):
        config = {
            "platforms": [{"name": "test", "api_url": "https://test.com"}],
            "retry": {
                "max_attempts": 5,
                "delay_seconds": 3,
                "exponential_backoff": True,
                "max_delay_seconds": 60,
            },
        }
        manager = PlatformManager(config)
        assert manager.retry_config["max_attempts"] == 5
        assert manager.retry_config["delay_seconds"] == 3


class TestGetRetryDelay:
    def test_get_retry_delay_fixed(self):
        config = {
            "platforms": [],
            "retry": {"delay_seconds": 2, "exponential_backoff": False},
        }
        manager = PlatformManager(config)
        delay = manager._get_retry_delay(1)
        assert delay == 2
        delay = manager._get_retry_delay(2)
        assert delay == 2

    def test_get_retry_delay_exponential(self):
        config = {
            "platforms": [],
            "retry": {
                "delay_seconds": 2,
                "exponential_backoff": True,
                "max_delay_seconds": 30,
            },
        }
        manager = PlatformManager(config)
        delay1 = manager._get_retry_delay(1)
        delay2 = manager._get_retry_delay(2)
        delay3 = manager._get_retry_delay(3)
        assert delay1 == 2
        assert delay2 == 4
        assert delay3 == 8

    def test_get_retry_delay_max_cap(self):
        config = {
            "platforms": [],
            "retry": {
                "delay_seconds": 10,
                "exponential_backoff": True,
                "max_delay_seconds": 30,
            },
        }
        manager = PlatformManager(config)
        delay = manager._get_retry_delay(5)
        assert delay <= 30


class TestTryPlatform:
    def test_try_platform_success(self):
        config = {
            "platforms": [
                {
                    "name": "test_platform",
                    "api_url": "https://test.com",
                    "response_type": "binary",
                    "auth_type": "none",
                }
            ],
            "retry": {"max_attempts": 1},
        }
        manager = PlatformManager(config)
        mock_client = MagicMock()
        mock_client.request.return_value = (True, b"image_data", None)
        manager._clients["test_platform"] = mock_client
        success, data, error = manager._try_platform("test_platform", "test prompt")
        assert success is True
        assert data == b"image_data"

    def test_try_platform_not_found(self):
        config = {"platforms": [], "retry": {}}
        manager = PlatformManager(config)
        success, data, error = manager._try_platform("non_existing", "test")
        assert success is False
        assert "不存在" in error

    def test_try_platform_retry_success(self):
        config = {
            "platforms": [{"name": "test", "api_url": "https://test.com"}],
            "retry": {"max_attempts": 3, "delay_seconds": 0.1},
        }
        manager = PlatformManager(config)
        mock_client = MagicMock()
        mock_client.request.side_effect = [
            (False, b"", "error1"),
            (False, b"", "error2"),
            (True, b"image_data", None),
        ]
        manager._clients["test"] = mock_client
        with patch("time.sleep"):
            success, data, error = manager._try_platform("test", "prompt")
        assert success is True
        assert mock_client.request.call_count == 3

    def test_try_platform_all_retries_fail(self):
        config = {
            "platforms": [{"name": "test", "api_url": "https://test.com"}],
            "retry": {"max_attempts": 2, "delay_seconds": 0.1},
        }
        manager = PlatformManager(config)
        mock_client = MagicMock()
        mock_client.request.return_value = (False, b"", "error")
        manager._clients["test"] = mock_client
        with patch("time.sleep"):
            success, data, error = manager._try_platform("test", "prompt")
        assert success is False
        assert error == "error"


class TestGenerate:
    def test_generate_no_platforms(self):
        config = {"platforms": [], "retry": {}}
        manager = PlatformManager(config)
        success, data, error = manager.generate("test prompt")
        assert success is False
        assert "没有配置" in error

    def test_generate_first_platform_success(self):
        config = {
            "platforms": [
                {"name": "platform1", "api_url": "https://test1.com"},
                {"name": "platform2", "api_url": "https://test2.com"},
            ],
            "retry": {"max_attempts": 1},
            "image": {"default_width": 512, "default_height": 512},
        }
        manager = PlatformManager(config)
        mock_client = MagicMock()
        mock_client.request.return_value = (True, b"image_data", None)
        manager._clients["platform1"] = mock_client
        manager._clients["platform2"] = MagicMock()
        success, data, error = manager.generate("test prompt")
        assert success is True
        assert manager.current_platform_name == "platform1"

    def test_generate_fallback_to_second_platform(self):
        config = {
            "platforms": [
                {"name": "platform1", "api_url": "https://test1.com"},
                {"name": "platform2", "api_url": "https://test2.com"},
            ],
            "retry": {"max_attempts": 1, "delay_seconds": 0.1},
            "image": {"default_width": 512, "default_height": 512},
        }
        manager = PlatformManager(config)
        mock_client1 = MagicMock()
        mock_client1.request.return_value = (False, b"", "error")
        mock_client2 = MagicMock()
        mock_client2.request.return_value = (True, b"image_data", None)
        manager._clients["platform1"] = mock_client1
        manager._clients["platform2"] = mock_client2
        with patch("time.sleep"):
            success, data, error = manager.generate("test prompt")
        assert success is True
        assert manager.current_platform_name == "platform2"

    def test_generate_all_platforms_fail(self):
        config = {
            "platforms": [
                {"name": "platform1", "api_url": "https://test1.com"},
                {"name": "platform2", "api_url": "https://test2.com"},
            ],
            "retry": {"max_attempts": 1, "delay_seconds": 0.1},
            "image": {},
        }
        manager = PlatformManager(config)
        mock_client = MagicMock()
        mock_client.request.return_value = (False, b"", "error")
        manager._clients["platform1"] = mock_client
        manager._clients["platform2"] = mock_client
        with patch("time.sleep"):
            success, data, error = manager.generate("test prompt")
        assert success is False
        assert "所有平台均失败" in error

    def test_generate_with_custom_dimensions(self):
        config = {
            "platforms": [{"name": "test", "api_url": "https://test.com"}],
            "retry": {"max_attempts": 1},
            "image": {"default_width": 512, "default_height": 512},
        }
        manager = PlatformManager(config)
        mock_client = MagicMock()
        mock_client.request.return_value = (True, b"image_data", None)
        manager._clients["test"] = mock_client
        manager.generate("test", width=1024, height=768)
        call_args = mock_client.request.call_args
        assert call_args.kwargs["width"] == 1024
        assert call_args.kwargs["height"] == 768


class TestSetPlatform:
    def test_set_platform_existing(self):
        config = {
            "platforms": [
                {"name": "platform1", "api_url": "https://test1.com"},
                {"name": "platform2", "api_url": "https://test2.com"},
            ],
            "retry": {},
        }
        manager = PlatformManager(config)
        result = manager.set_platform("platform2")
        assert result is True
        assert manager.current_platform_name == "platform2"
        assert manager.current_platform_index == 1

    def test_set_platform_non_existing(self):
        config = {
            "platforms": [{"name": "platform1", "api_url": "https://test1.com"}],
            "retry": {},
        }
        manager = PlatformManager(config)
        result = manager.set_platform("non_existing")
        assert result is False


class TestGetAvailablePlatforms:
    def test_get_available_platforms(self):
        config = {
            "platforms": [
                {"name": "platform1", "api_url": "https://test1.com"},
                {"name": "platform2", "api_url": "https://test2.com"},
            ],
            "retry": {},
        }
        manager = PlatformManager(config)
        platforms = manager.get_available_platforms()
        assert platforms == ["platform1", "platform2"]

    def test_get_available_platforms_empty(self):
        config = {"platforms": [], "retry": {}}
        manager = PlatformManager(config)
        platforms = manager.get_available_platforms()
        assert platforms == []


class TestAddPlatform:
    def test_add_platform(self):
        config = {"platforms": [], "retry": {"max_attempts": 3, "delay_seconds": 2}}
        manager = PlatformManager(config)
        new_platform = {"name": "new_platform", "api_url": "https://new.com"}
        manager.add_platform(new_platform)
        assert len(manager.platforms) == 1
        assert "new_platform" in manager._clients


class TestRemovePlatform:
    def test_remove_platform_existing(self):
        config = {
            "platforms": [
                {"name": "platform1", "api_url": "https://test1.com"},
                {"name": "platform2", "api_url": "https://test2.com"},
            ],
            "retry": {},
        }
        manager = PlatformManager(config)
        result = manager.remove_platform("platform1")
        assert result is True
        assert len(manager.platforms) == 1
        assert "platform1" not in manager._clients

    def test_remove_platform_non_existing(self):
        config = {"platforms": [], "retry": {}}
        manager = PlatformManager(config)
        result = manager.remove_platform("non_existing")
        assert result is False


class TestGetPlatformStatus:
    def test_get_platform_status(self):
        config = {
            "platforms": [
                {"name": "platform1", "api_url": "https://test1.com"},
                {"name": "platform2", "api_url": "https://test2.com"},
            ],
            "retry": {},
        }
        manager = PlatformManager(config)
        manager.set_platform("platform2")
        status = manager.get_platform_status()
        assert status["current_platform"] == "platform2"
        assert status["current_index"] == 1
        assert status["total_platforms"] == 2
        assert "platform1" in status["available_platforms"]
        assert "platform2" in status["available_platforms"]


class TestGetCurrentPlatform:
    def test_get_current_platform(self):
        config = {
            "platforms": [{"name": "test_platform", "api_url": "https://test.com"}],
            "retry": {},
        }
        manager = PlatformManager(config)
        manager.set_platform("test_platform")
        assert manager.get_current_platform() == "test_platform"

    def test_get_current_platform_none(self):
        config = {"platforms": [], "retry": {}}
        manager = PlatformManager(config)
        assert manager.get_current_platform() is None


class TestGetPlatformIndex:
    def test_get_platform_index(self):
        config = {
            "platforms": [
                {"name": "platform1", "api_url": "https://test1.com"},
                {"name": "platform2", "api_url": "https://test2.com"},
            ],
            "retry": {},
        }
        manager = PlatformManager(config)
        manager.set_platform("platform2")
        assert manager.get_platform_index() == 1

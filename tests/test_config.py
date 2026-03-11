import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config import (
    ConfigManager,
    get_default_config,
    get_env,
    get_config_manager,
    load_config,
    save_config,
    ensure_config_exists,
)


class TestGetDefaultConfig:
    def test_get_default_config_returns_dict(self):
        config = get_default_config()
        assert isinstance(config, dict)

    def test_get_default_config_has_required_keys(self):
        config = get_default_config()
        required_keys = ["platforms", "enhance_service", "output", "image", "retry", "logging"]
        for key in required_keys:
            assert key in config

    def test_get_default_config_has_platforms(self):
        config = get_default_config()
        platforms = config.get("platforms", [])
        assert isinstance(platforms, list)
        assert len(platforms) > 0

    def test_get_default_config_platform_has_required_fields(self):
        config = get_default_config()
        platform = config["platforms"][0]
        required_fields = ["name", "api_url", "request_method", "auth_type", "response_type"]
        for field in required_fields:
            assert field in platform

    def test_get_default_config_enhance_service(self):
        config = get_default_config()
        enhance = config.get("enhance_service", {})
        assert "enabled" in enhance
        assert "provider" in enhance
        assert "api_url" in enhance

    def test_get_default_config_output(self):
        config = get_default_config()
        output = config.get("output", {})
        assert "directory" in output
        assert "naming_rule" in output

    def test_get_default_config_image(self):
        config = get_default_config()
        image = config.get("image", {})
        assert "default_width" in image
        assert "default_height" in image
        assert "default_format" in image

    def test_get_default_config_retry(self):
        config = get_default_config()
        retry = config.get("retry", {})
        assert "max_attempts" in retry
        assert "delay_seconds" in retry

    def test_get_default_config_logging(self):
        config = get_default_config()
        logging_config = config.get("logging", {})
        assert "level" in logging_config
        assert "console_output" in logging_config


class TestGetEnv:
    def test_get_env_existing_key(self):
        with patch.dict(os.environ, {"TEST_KEY": "test_value"}):
            result = get_env("TEST_KEY")
            assert result == "test_value"

    def test_get_env_non_existing_key(self):
        result = get_env("NON_EXISTING_KEY_12345")
        assert result is None

    def test_get_env_with_default(self):
        result = get_env("NON_EXISTING_KEY_12345", "default_value")
        assert result == "default_value"

    def test_get_env_empty_value(self):
        with patch.dict(os.environ, {"EMPTY_KEY": ""}):
            result = get_env("EMPTY_KEY", "default")
            assert result == ""


class TestConfigManager:
    def setup_method(self):
        ConfigManager._instance = None
        ConfigManager._config = None
        ConfigManager._config_path = None

    def test_singleton_pattern(self):
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        assert manager1 is manager2

    def test_load_config_default(self):
        manager = ConfigManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test_config.json")
            config = manager.load_config(config_path)
            assert isinstance(config, dict)
            assert "platforms" in config

    def test_load_config_from_file(self):
        manager = ConfigManager()
        test_config = {"platforms": [{"name": "test"}], "output": {}}
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test_config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(test_config, f)
            config = manager.load_config(config_path)
            assert config["platforms"][0]["name"] == "test"

    def test_save_config(self):
        manager = ConfigManager()
        test_config = {"platforms": [], "output": {}}
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test_config.json")
            manager._config_path = Path(config_path)
            manager.save_config(test_config)
            assert os.path.exists(config_path)
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            assert loaded == test_config

    def test_ensure_config_exists_creates_file(self):
        manager = ConfigManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "new_config.json")
            result = manager.ensure_config_exists(config_path)
            assert os.path.exists(config_path)
            assert result == Path(config_path)

    def test_ensure_config_exists_existing_file(self):
        manager = ConfigManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "existing_config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump({"test": "data"}, f)
            result = manager.ensure_config_exists(config_path)
            assert os.path.exists(config_path)

    def test_get_enhance_service_config(self):
        manager = ConfigManager()
        manager._config = {"enhance_service": {"provider": "glm"}}
        config = manager.get_enhance_service_config()
        assert config["provider"] == "glm"

    def test_get_output_config(self):
        manager = ConfigManager()
        manager._config = {"output": {"directory": "test_output"}}
        config = manager.get_output_config()
        assert config["directory"] == "test_output"

    def test_get_image_config(self):
        manager = ConfigManager()
        manager._config = {"image": {"default_width": 1024}}
        config = manager.get_image_config()
        assert config["default_width"] == 1024

    def test_get_logging_config(self):
        manager = ConfigManager()
        manager._config = {"logging": {"level": "DEBUG"}}
        config = manager.get_logging_config()
        assert config["level"] == "DEBUG"

    def test_load_config_invalid_json(self):
        manager = ConfigManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "invalid.json")
            with open(config_path, "w", encoding="utf-8") as f:
                f.write("invalid json content {")
            config = manager.load_config(config_path)
            assert config is not None
            assert "platforms" in config


class TestModuleFunctions:
    def setup_method(self):
        ConfigManager._instance = None
        ConfigManager._config = None
        ConfigManager._config_path = None

    def test_get_config_manager(self):
        manager = get_config_manager()
        assert isinstance(manager, ConfigManager)

    def test_load_config_function(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.json")
            config = load_config(config_path)
            assert isinstance(config, dict)

    def test_save_config_function(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.json")
            manager = get_config_manager()
            manager._config_path = Path(config_path)
            save_config({"test": "data"})
            assert os.path.exists(config_path)

    def test_ensure_config_exists_function(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.json")
            result = ensure_config_exists(config_path)
            assert os.path.exists(config_path)

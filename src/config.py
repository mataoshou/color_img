import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv


load_dotenv()


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(key, default)


def get_default_config() -> Dict[str, Any]:
    return {
        "platforms": [
            {
                "name": "siliconflow-flux",
                "api_url": "https://api.siliconflow.cn/v1/images/generations",
                "request_method": "POST",
                "request_params": {},
                "request_headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {api_key}"
                },
                "request_body": {
                    "model": "black-forest-labs/FLUX.1-schnell",
                    "prompt": "{prompt}",
                    "image_size": "1024x1024"
                },
                "auth_type": "bearer",
                "api_key_env": "SILICONFLOW_API_KEY",
                "response_type": "json",
                "image_url_path": "images.0.url",
                "description": "硅基流动Flux图片生成，新用户免费额度，国内访问稳定"
            },
            {
                "name": "zhipu-cogview",
                "api_url": "https://open.bigmodel.cn/api/paas/v4/images/generations",
                "request_method": "POST",
                "request_params": {},
                "request_headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {api_key}"
                },
                "request_body": {
                    "model": "cogview-3",
                    "prompt": "{prompt}"
                },
                "auth_type": "bearer",
                "api_key_env": "GLM_API_KEY",
                "response_type": "json",
                "image_url_path": "data.0.url",
                "description": "智谱AI CogView图片生成，支持中文，新用户有免费额度"
            },
            {
                "name": "pollinations",
                "api_url": "https://image.pollinations.ai/prompt/{prompt}",
                "request_method": "GET",
                "request_params": {
                    "width": "{width}",
                    "height": "{height}",
                    "nologo": "true",
                    "enhance": "true"
                },
                "request_headers": {},
                "request_body": {},
                "auth_type": "none",
                "response_type": "binary",
                "image_url_path": None,
                "description": "免费无需API密钥，由Pollinations.AI提供"
            },
            {
                "name": "pollinations-turbo",
                "api_url": "https://image.pollinations.ai/prompt/{prompt}",
                "request_method": "GET",
                "request_params": {
                    "width": "{width}",
                    "height": "{height}",
                    "nologo": "true",
                    "model": "turbo"
                },
                "request_headers": {},
                "request_body": {},
                "auth_type": "none",
                "response_type": "binary",
                "image_url_path": None,
                "description": "Pollinations快速模式，速度更快"
            },
            {
                "name": "pollinations-flux",
                "api_url": "https://image.pollinations.ai/prompt/{prompt}",
                "request_method": "GET",
                "request_params": {
                    "width": "{width}",
                    "height": "{height}",
                    "nologo": "true",
                    "model": "flux"
                },
                "request_headers": {},
                "request_body": {},
                "auth_type": "none",
                "response_type": "binary",
                "image_url_path": None,
                "description": "Pollinations Flux模型，高质量"
            },
            {
                "name": "stability-ai",
                "api_url": "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                "request_method": "POST",
                "request_params": {},
                "request_headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {api_key}"
                },
                "request_body": {
                    "text_prompts": [{"text": "{prompt}"}],
                    "cfg_scale": 7,
                    "height": "{height}",
                    "width": "{width}",
                    "samples": 1,
                    "steps": 30
                },
                "auth_type": "bearer",
                "api_key_env": "STABILITY_API_KEY",
                "response_type": "json",
                "image_url_path": "artifacts.0.base64",
                "is_base64": True,
                "description": "Stability AI，需要API密钥，新用户有免费额度"
            },
            {
                "name": "replicate-sdxl",
                "api_url": "https://api.replicate.com/v1/predictions",
                "request_method": "POST",
                "request_params": {},
                "request_headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Token {api_key}"
                },
                "request_body": {
                    "version": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                    "input": {
                        "prompt": "{prompt}",
                        "width": "{width}",
                        "height": "{height}"
                    }
                },
                "auth_type": "api_key",
                "api_key_env": "REPLICATE_API_TOKEN",
                "response_type": "json",
                "image_url_path": "output",
                "is_async": True,
                "description": "Replicate SDXL，需要API密钥，新用户有免费额度"
            }
        ],
        "enhance_service": {
            "enabled": True,
            "provider": "glm",
            "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            "model": "glm-4-flash",
            "api_key_env": "GLM_API_KEY",
            "max_tokens": 1000,
            "temperature": 0.7
        },
        "output": {
            "directory": "output",
            "naming_rule": "{platform}_{timestamp}_{index}",
            "create_subdirs": False,
            "subdir_rule": "{date}"
        },
        "image": {
            "default_width": 1024,
            "default_height": 1024,
            "formats": ["png", "jpg", "webp"],
            "default_format": "png"
        },
        "retry": {
            "max_attempts": 3,
            "delay_seconds": 2,
            "exponential_backoff": True,
            "max_delay_seconds": 30
        },
        "logging": {
            "level": "INFO",
            "console_output": True,
            "file_output": False,
            "log_file": "logs/color_img.log",
            "log_format": "%(asctime)s | %(levelname)-8s | %(message)s"
        }
    }


class ConfigManager:
    _instance: Optional['ConfigManager'] = None
    _config: Optional[Dict[str, Any]] = None
    _config_path: Optional[Path] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is not None:
            return
        self._config = None
        self._config_path = None

    def ensure_config_exists(self, config_path: Optional[str] = None) -> Path:
        if config_path is None:
            config_path = "config.json"
        
        self._config_path = Path(config_path)
        
        if not self._config_path.exists():
            default_config = get_default_config()
            self.save_config(default_config)
            return self._config_path
        
        return self._config_path

    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        if config_path is not None:
            self._config_path = Path(config_path)
        
        if self._config_path is None:
            self.ensure_config_exists(config_path)
        
        if not self._config_path.exists():
            self._config = get_default_config()
            return self._config
        
        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            return self._config
        except (json.JSONDecodeError, IOError):
            self._config = get_default_config()
            return self._config

    def save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        if config is not None:
            self._config = config
        
        if self._config is None:
            self._config = get_default_config()
        
        if self._config_path is None:
            self._config_path = Path("config.json")
        
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self._config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=4, ensure_ascii=False)

    def get_config(self) -> Dict[str, Any]:
        if self._config is None:
            self.load_config()
        return self._config

    def get_enhance_service_config(self) -> Dict[str, Any]:
        config = self.get_config()
        return config.get("enhance_service", {})

    def get_output_config(self) -> Dict[str, Any]:
        config = self.get_config()
        return config.get("output", {})

    def get_image_config(self) -> Dict[str, Any]:
        config = self.get_config()
        return config.get("image", {})

    def get_logging_config(self) -> Dict[str, Any]:
        config = self.get_config()
        return config.get("logging", {})

    def get_config_path(self) -> Optional[Path]:
        return self._config_path


_config_manager_instance: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager()
    return _config_manager_instance


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    return get_config_manager().load_config(config_path)


def save_config(config: Optional[Dict[str, Any]] = None) -> None:
    get_config_manager().save_config(config)


def ensure_config_exists(config_path: Optional[str] = None) -> Path:
    return get_config_manager().ensure_config_exists(config_path)

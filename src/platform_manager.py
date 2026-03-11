import time
from typing import Any, Dict, List, Optional, Tuple

from src.logger import get_logger
from src.service_client import ServiceClient


class PlatformManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.platforms: List[Dict[str, Any]] = config.get("platforms", [])
        self.retry_config: Dict[str, Any] = config.get("retry", {})
        self.current_platform_index: int = 0
        self.current_platform_name: Optional[str] = None
        self.logger = get_logger()
        self._clients: Dict[str, ServiceClient] = {}
        self._init_clients()

    def _init_clients(self) -> None:
        for platform in self.platforms:
            name = platform.get("name", "unknown")
            client_retry_config = {
                "max_retries": self.retry_config.get("max_attempts", 3),
                "retry_interval": self.retry_config.get("delay_seconds", 2),
                "timeout": 60,
            }
            self._clients[name] = ServiceClient(platform, client_retry_config)

    def _get_retry_delay(self, attempt: int) -> float:
        delay = self.retry_config.get("delay_seconds", 2)
        exponential_backoff = self.retry_config.get("exponential_backoff", True)
        max_delay = self.retry_config.get("max_delay_seconds", 30)

        if exponential_backoff:
            delay = min(delay * (2 ** (attempt - 1)), max_delay)

        return delay

    def _try_platform(
        self,
        platform_name: str,
        prompt: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        **kwargs
    ) -> Tuple[bool, bytes, Optional[str]]:
        client = self._clients.get(platform_name)
        if not client:
            return False, b"", f"平台 {platform_name} 不存在"

        if not client.is_available():
            return False, b"", f"平台 {platform_name} 未配置API密钥，跳过"

        self.current_platform_name = platform_name
        self.logger.info(f"使用平台: {platform_name}")

        max_attempts = self.retry_config.get("max_attempts", 3)
        last_error = None

        for attempt in range(1, max_attempts + 1):
            self.logger.info(f"平台 {platform_name} 第 {attempt}/{max_attempts} 次尝试")

            success, data, error = client.request(
                prompt=prompt,
                width=width,
                height=height,
                **kwargs
            )

            if success:
                if isinstance(data, bytes):
                    return True, data, None
                else:
                    return False, b"", f"返回数据类型错误: {type(data)}"

            last_error = error

            if attempt < max_attempts:
                delay = self._get_retry_delay(attempt)
                self.logger.warning(
                    f"平台 {platform_name} 尝试 {attempt}/{max_attempts} 失败: {error}, "
                    f"{delay:.1f}秒后重试..."
                )
                time.sleep(delay)

        return False, b"", last_error

    def generate_with_platform(
        self,
        platform_config: dict,
        prompt: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        **kwargs
    ) -> Tuple[bool, bytes, Optional[str]]:
        platform_name = platform_config.get("name", "unknown")
        
        if platform_name not in self._clients:
            client_retry_config = {
                "max_retries": self.retry_config.get("max_attempts", 3),
                "retry_interval": self.retry_config.get("delay_seconds", 2),
                "timeout": 60,
            }
            self._clients[platform_name] = ServiceClient(platform_config, client_retry_config)
        
        image_config = self.config.get("image", {})
        width = width or image_config.get("default_width", 512)
        height = height or image_config.get("default_height", 512)
        
        return self._try_platform(
            platform_name=platform_name,
            prompt=prompt,
            width=width,
            height=height,
            **kwargs
        )

    def generate(
        self,
        prompt: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        image_url: Optional[str] = None,
        **kwargs
    ) -> Tuple[bool, bytes, Optional[str]]:
        if not self.platforms:
            return False, b"", "没有配置任何平台"

        image_config = self.config.get("image", {})
        width = width or image_config.get("default_width", 512)
        height = height or image_config.get("default_height", 512)

        if image_url:
            kwargs["image_url"] = image_url

        last_error = None
        attempted_platforms = []

        for platform_index in range(len(self.platforms)):
            self.current_platform_index = platform_index
            platform = self.platforms[platform_index]
            platform_name = platform.get("name", "unknown")

            attempted_platforms.append(platform_name)

            success, data, error = self._try_platform(
                platform_name=platform_name,
                prompt=prompt,
                width=width,
                height=height,
                **kwargs
            )

            if success:
                self.logger.info(f"平台 {platform_name} 生成成功")
                return True, data, None

            last_error = error
            self.logger.error(f"平台 {platform_name} 生成失败: {error}")

            if platform_index < len(self.platforms) - 1:
                next_platform = self.platforms[platform_index + 1].get("name", "unknown")
                self.logger.warning(f"切换到下一个平台: {next_platform}")

        return False, b"", f"所有平台均失败。尝试的平台: {', '.join(attempted_platforms)}。最后错误: {last_error}"

    def get_current_platform(self) -> Optional[str]:
        return self.current_platform_name

    def get_platform_index(self) -> int:
        return self.current_platform_index

    def get_available_platforms(self) -> List[str]:
        return [p.get("name", "unknown") for p in self.platforms]

    def set_platform(self, platform_name: str) -> bool:
        for i, platform in enumerate(self.platforms):
            if platform.get("name") == platform_name:
                self.current_platform_index = i
                self.current_platform_name = platform_name
                self.logger.info(f"已切换到平台: {platform_name}")
                return True
        self.logger.warning(f"平台 {platform_name} 不存在")
        return False

    def add_platform(self, platform_config: Dict[str, Any]) -> None:
        name = platform_config.get("name", "unknown")
        self.platforms.append(platform_config)

        client_retry_config = {
            "max_retries": self.retry_config.get("max_attempts", 3),
            "retry_interval": self.retry_config.get("delay_seconds", 2),
            "timeout": 60,
        }
        self._clients[name] = ServiceClient(platform_config, client_retry_config)
        self.logger.info(f"已添加平台: {name}")

    def remove_platform(self, platform_name: str) -> bool:
        for i, platform in enumerate(self.platforms):
            if platform.get("name") == platform_name:
                self.platforms.pop(i)
                if platform_name in self._clients:
                    del self._clients[platform_name]
                self.logger.info(f"已移除平台: {platform_name}")
                return True
        return False

    def get_platform_status(self) -> Dict[str, Any]:
        return {
            "current_platform": self.current_platform_name,
            "current_index": self.current_platform_index,
            "available_platforms": self.get_available_platforms(),
            "total_platforms": len(self.platforms),
        }

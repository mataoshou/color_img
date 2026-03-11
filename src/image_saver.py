import os
import re
import time
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse

import requests

from src.logger import get_logger


class ImageSaver:
    def __init__(self, config: dict):
        self.output_config = config.get("output", {})
        self.directory = self.output_config.get("directory", "./output")
        self.naming = self.output_config.get("naming", "timestamp")
        self._sequential_counter = 0
        self.logger = get_logger()

    def _ensure_directory(self) -> None:
        Path(self.directory).mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
        sanitized = re.sub(r'\s+', '_', sanitized)
        sanitized = sanitized.strip('._')
        return sanitized[:100] if sanitized else "image"

    def _generate_filename_timestamp(self) -> str:
        return time.strftime("%Y%m%d_%H%M%S")

    def _generate_filename_sequential(self) -> str:
        self._sequential_counter += 1
        return f"image_{self._sequential_counter:04d}"

    def _generate_filename_prompt(self, prompt: str) -> str:
        if not prompt:
            return self._generate_filename_timestamp()
        return self._sanitize_filename(prompt)

    def _generate_filename(self, prompt: Optional[str] = None) -> str:
        if self.naming == "sequential":
            return self._generate_filename_sequential()
        elif self.naming == "prompt":
            return self._generate_filename_prompt(prompt or "")
        else:
            return self._generate_filename_timestamp()

    def _resolve_conflict(self, filepath: Path) -> Path:
        if not filepath.exists():
            return filepath

        stem = filepath.stem
        suffix = filepath.suffix
        parent = filepath.parent
        counter = 1

        while True:
            new_filepath = parent / f"{stem}_{counter}{suffix}"
            if not new_filepath.exists():
                return new_filepath
            counter += 1

    def _detect_format(self, image_data: bytes) -> str:
        if image_data[:8] == b'\x89PNG\r\n\x1a\n':
            return ".png"
        elif image_data[:2] == b'\xff\xd8':
            return ".jpg"
        else:
            return ".png"

    def download_image(self, url: str, timeout: int = 30) -> bytes:
        self.logger.debug(f"正在下载图片: {url}")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        self.logger.debug(f"图片下载成功，大小: {len(response.content)} bytes")
        return response.content

    def save_image(
        self,
        image_data: Union[bytes, str],
        prompt: Optional[str] = None,
        format: Optional[str] = None
    ) -> str:
        self._ensure_directory()

        if isinstance(image_data, str):
            if image_data.startswith(("http://", "https://")):
                self.logger.info(f"从URL下载图片: {image_data[:50]}...")
                image_data = self.download_image(image_data)
            else:
                image_data = image_data.encode("utf-8")

        if format:
            ext = f".{format.lower().lstrip('.')}"
        else:
            ext = self._detect_format(image_data)
            self.logger.debug(f"检测到图片格式: {ext}")

        filename = self._generate_filename(prompt)
        filepath = Path(self.directory) / f"{filename}{ext}"
        filepath = self._resolve_conflict(filepath)

        with open(filepath, "wb") as f:
            f.write(image_data)

        self.logger.info(f"图片已保存: {filepath} ({len(image_data)} bytes)")
        return str(filepath.resolve())

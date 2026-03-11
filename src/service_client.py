import os
import re
import time
from typing import Any, Dict, Optional, Tuple, Union

import requests

from src.logger import get_logger


class ServiceClient:
    def __init__(self, platform_config: dict, retry_config: Optional[dict] = None):
        self.config = platform_config
        self.name = platform_config.get("name", "unknown")
        self.api_url = platform_config.get("api_url", "")
        self.request_method = platform_config.get("request_method", "POST").upper()
        self.request_params = platform_config.get("request_params", {})
        self.request_headers = platform_config.get("request_headers", {})
        self.request_body = platform_config.get("request_body", {})
        self.auth_type = platform_config.get("auth_type", "none")
        self.response_type = platform_config.get("response_type", "binary")
        self.image_url_path = platform_config.get("image_url_path", "")
        self.result_url_path = platform_config.get("result_url_path") or platform_config.get("image_url_path", "")
        self.api_key_env = platform_config.get("api_key_env", "")
        self.is_base64 = platform_config.get("is_base64", False)
        self.is_async = platform_config.get("is_async", False)

        if self.is_async:
            async_config = platform_config.get("async_config", {})
            self.task_id_path = async_config.get("task_id_path", "")
            self.status_url = async_config.get("status_url", "")
            self.status_path = async_config.get("status_path", "")
            self.status_complete_value = async_config.get("status_complete_value", "")
            self.result_url_path = async_config.get("result_url_path", self.result_url_path)
            self.poll_interval = async_config.get("poll_interval", 10)
            self.max_poll_time = async_config.get("max_poll_time", 600)

        if retry_config:
            self.max_retries = retry_config.get("max_retries", 3)
            self.retry_interval = retry_config.get("retry_interval", 1)
            self.timeout = retry_config.get("timeout", 15)
        else:
            self.max_retries = 3
            self.retry_interval = 1
            self.timeout = 15

        self.logger = get_logger()

    def _get_api_key(self) -> str:
        if not self.api_key_env:
            return ""
        return os.environ.get(self.api_key_env, "")

    def is_available(self) -> bool:
        if self.auth_type == "none":
            return True
        api_key = self._get_api_key()
        return bool(api_key)

    def _replace_templates(self, template: Any, variables: Dict[str, Any]) -> Any:
        if isinstance(template, str):
            result = template
            for key, value in variables.items():
                placeholder = "{" + key + "}"
                result = result.replace(placeholder, str(value))
            return result
        elif isinstance(template, dict):
            return {k: self._replace_templates(v, variables) for k, v in template.items()}
        elif isinstance(template, list):
            return [self._replace_templates(item, variables) for item in template]
        else:
            return template

    def _apply_auth(self, headers: Dict[str, str], params: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, Any]]:
        headers = headers.copy()
        params = params.copy()

        if self.auth_type == "none":
            pass
        elif self.auth_type == "api_key":
            api_key = self._get_api_key()
            if not api_key:
                self.logger.warning(f"API key not found for platform {self.name}")
                return headers, params

            auth_location = self.config.get("auth_location", "header")
            auth_key = self.config.get("auth_key", "Authorization")

            if auth_location == "params":
                params[auth_key] = api_key
            else:
                if auth_key.lower() == "authorization":
                    headers[auth_key] = api_key
                else:
                    headers[auth_key] = api_key

        elif self.auth_type == "bearer":
            api_key = self._get_api_key()
            if not api_key:
                self.logger.warning(f"Bearer token not found for platform {self.name}")
                return headers, params
            headers["Authorization"] = f"Bearer {api_key}"

        return headers, params

    def build_request(
        self,
        prompt: str,
        model: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        **kwargs
    ) -> Tuple[str, Dict[str, str], Dict[str, Any], Optional[Dict[str, Any]]]:
        variables = {
            "prompt": prompt,
            "model": model or self.config.get("model", ""),
            "api_key": self._get_api_key(),
            "width": width or self.config.get("width", 512),
            "height": height or self.config.get("height", 512),
        }
        variables.update(kwargs)

        url = self._replace_templates(self.api_url, variables)
        headers = self._replace_templates(self.request_headers, variables)
        params = self._replace_templates(self.request_params, variables)
        body = self._replace_templates(self.request_body, variables) if self.request_body else None

        if isinstance(headers, dict):
            headers = {k: str(v) for k, v in headers.items()}

        headers, params = self._apply_auth(headers, params)

        return url, headers, params, body

    def _extract_path_value(self, data: Any, path: str) -> Any:
        if not path:
            return None
        keys = path.split(".")
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key)
            elif isinstance(data, list) and key.isdigit():
                data = data[int(key)]
            else:
                return None
        return data

    def _extract_image_url(self, response: requests.Response) -> str:
        if not self.image_url_path:
            return ""

        try:
            data = response.json()
            result = self._extract_path_value(data, self.image_url_path)
            return str(result) if result else ""
        except (ValueError, KeyError, IndexError, TypeError):
            return ""

    def _download_image(self, url: str) -> Tuple[bool, bytes, str]:
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return True, response.content, ""
        except requests.exceptions.RequestException as e:
            return False, b"", f"下载图片失败: {str(e)}"

    def _process_response(self, response: requests.Response) -> Tuple[bool, Union[bytes, str], str]:
        if self.response_type == "binary":
            return True, response.content, ""

        elif self.response_type == "image_url":
            image_url = response.text.strip()
            if image_url.startswith(("http://", "https://")):
                return self._download_image(image_url)
            else:
                return False, "", f"无效的图片URL: {image_url[:100]}"

        elif self.response_type == "json":
            if self.is_base64:
                try:
                    data = response.json()
                    keys = self.image_url_path.split(".")
                    base64_data = data
                    for key in keys:
                        if isinstance(base64_data, dict):
                            base64_data = base64_data.get(key)
                        elif isinstance(base64_data, list) and key.isdigit():
                            base64_data = base64_data[int(key)]
                        else:
                            return False, "", "无法提取base64数据"
                    
                    if base64_data:
                        import base64
                        image_data = base64.b64decode(base64_data)
                        return True, image_data, ""
                    else:
                        return False, "", "base64数据为空"
                except Exception as e:
                    return False, "", f"解析base64数据失败: {str(e)}"
            
            image_url = self._extract_image_url(response)
            if not image_url:
                return False, "", "无法从响应中提取图片URL"
            return self._download_image(image_url)

        else:
            return False, "", f"不支持的响应类型: {self.response_type}"

    def _handle_error(self, error: Exception, attempt: int) -> str:
        if isinstance(error, requests.exceptions.Timeout):
            return f"请求超时 (尝试 {attempt}/{self.max_retries})"
        elif isinstance(error, requests.exceptions.ConnectionError):
            return f"网络连接错误 (尝试 {attempt}/{self.max_retries})"
        elif isinstance(error, requests.exceptions.HTTPError):
            status_code = error.response.status_code if hasattr(error, 'response') else "unknown"
            return f"HTTP错误: {status_code} (尝试 {attempt}/{self.max_retries})"
        else:
            return f"请求失败: {str(error)} (尝试 {attempt}/{self.max_retries})"

    def request(
        self,
        prompt: str,
        model: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        **kwargs
    ) -> Tuple[bool, Union[bytes, str], Optional[str]]:
        if self.is_async:
            return self._request_async(prompt, model, width, height, **kwargs)

        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                url, headers, params, body = self.build_request(
                    prompt=prompt,
                    model=model,
                    width=width,
                    height=height,
                    **kwargs
                )

                self.logger.debug(f"平台 {self.name} 请求: {self.request_method} {url}")

                if self.request_method == "GET":
                    response = requests.get(
                        url,
                        headers=headers,
                        params=params,
                        timeout=self.timeout
                    )
                else:
                    response = requests.post(
                        url,
                        headers=headers,
                        params=params,
                        json=body,
                        timeout=self.timeout
                    )

                response.raise_for_status()

                success, data, error = self._process_response(response)
                if success:
                    return True, data, None
                else:
                    last_error = error
                    self.logger.warning(f"平台 {self.name} 响应处理失败: {error}")

            except requests.exceptions.RequestException as e:
                last_error = self._handle_error(e, attempt)
                self.logger.warning(f"平台 {self.name} 请求失败: {last_error}")

            except Exception as e:
                last_error = f"未知错误: {str(e)}"
                self.logger.error(f"平台 {self.name} 发生未知错误: {last_error}")

            if attempt < self.max_retries:
                time.sleep(self.retry_interval)

        return False, b"", last_error or "请求失败"

    def _request_async(
        self,
        prompt: str,
        model: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        **kwargs
    ) -> Tuple[bool, Union[bytes, str], Optional[str]]:
        try:
            url, headers, params, body = self.build_request(
                prompt=prompt,
                model=model,
                width=width,
                height=height,
                **kwargs
            )

            self.logger.debug(f"平台 {self.name} 提交异步任务: {self.request_method} {url}")

            if self.request_method == "GET":
                response = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=self.timeout
                )
            else:
                response = requests.post(
                    url,
                    headers=headers,
                    params=params,
                    json=body,
                    timeout=self.timeout
                )

            response.raise_for_status()

            try:
                data = response.json()
            except ValueError:
                return False, b"", "异步任务提交响应不是有效的JSON"

            task_id = self._extract_path_value(data, self.task_id_path)
            if not task_id:
                return False, b"", "无法从响应中提取task_id"

            self.logger.debug(f"平台 {self.name} 获取到task_id: {task_id}")

            start_time = time.time()
            while True:
                elapsed = time.time() - start_time
                if elapsed > self.max_poll_time:
                    return False, b"", f"异步任务轮询超时 ({self.max_poll_time}秒)"

                status_url = self._replace_templates(self.status_url, {"task_id": task_id})
                self.logger.debug(f"平台 {self.name} 轮询状态: {status_url}")

                poll_response = requests.get(
                    status_url,
                    headers=headers,
                    timeout=self.timeout
                )
                poll_response.raise_for_status()

                try:
                    poll_data = poll_response.json()
                except ValueError:
                    return False, b"", "状态轮询响应不是有效的JSON"

                status = self._extract_path_value(poll_data, self.status_path)
                self.logger.debug(f"平台 {self.name} 当前状态: {status}")

                if status == self.status_complete_value:
                    result_url = self._extract_path_value(poll_data, self.result_url_path)
                    if not result_url:
                        return False, b"", "无法从轮询响应中提取结果URL"

                    self.logger.debug(f"平台 {self.name} 获取到结果URL: {result_url}")
                    return self._download_image(str(result_url))

                time.sleep(self.poll_interval)

        except requests.exceptions.RequestException as e:
            return False, b"", f"异步请求失败: {str(e)}"
        except Exception as e:
            return False, b"", f"异步请求未知错误: {str(e)}"

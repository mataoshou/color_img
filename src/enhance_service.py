import os
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from src.logger import get_logger


load_dotenv()


DEFAULT_SYSTEM_PROMPT = """You are an expert image prompt enhancer. Your task is to translate the user's input into English (if not already in English) and expand it into a detailed, high-quality image generation prompt.

Guidelines:
1. Translate non-English input to English first
2. Add descriptive details about style, lighting, composition, and quality
3. Include relevant artistic terms and technical specifications
4. Keep the enhanced prompt concise but detailed (2-4 sentences)
5. Focus on visual elements that will improve image generation

Example:
Input: "一只猫"
Output: "A cute fluffy cat sitting on a soft cushion, warm natural lighting, highly detailed fur texture, 4k quality, professional pet photography style"

Input: "sunset"
Output: "A breathtaking sunset over a calm ocean, vibrant orange and pink sky colors reflecting on the water, silhouetted palm trees, golden hour lighting, cinematic composition, ultra high definition"

Only output the enhanced prompt, nothing else."""


class EnhanceService:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            config = {}
        
        self.enabled = config.get("enabled", True)
        self.model = config.get("model", "glm-4-flash")
        self.api_url = config.get("api_url", "https://open.bigmodel.cn/api/paas/v4/chat/completions")
        self.api_key_env = config.get("api_key_env", "GLM_API_KEY")
        self.max_tokens = config.get("max_tokens", 1000)
        self.temperature = config.get("temperature", 0.7)
        self.system_prompt = config.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
        self.timeout = config.get("timeout", 30)
        
        self._api_key: Optional[str] = None
        self.logger = get_logger()

    def _get_api_key(self) -> Optional[str]:
        if self._api_key is not None:
            return self._api_key
        
        self._api_key = os.environ.get(self.api_key_env)
        return self._api_key

    def _build_request_body(self, user_input: str) -> Dict[str, Any]:
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input}
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

    def _build_headers(self) -> Dict[str, str]:
        api_key = self._get_api_key()
        headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _call_api(self, user_input: str) -> tuple[bool, str, Optional[str]]:
        api_key = self._get_api_key()
        if not api_key:
            return False, "", f"API key not found in environment variable: {self.api_key_env}"
        
        try:
            headers = self._build_headers()
            body = self._build_request_body(user_input)
            
            self.logger.debug(f"Calling enhance API: {self.api_url}")
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=body,
                timeout=self.timeout
            )
            
            if response.status_code == 401:
                return False, "", "API authentication failed: invalid API key"
            
            if response.status_code == 429:
                return False, "", "API rate limit exceeded, please try again later"
            
            if response.status_code >= 500:
                return False, "", f"API server error: HTTP {response.status_code}"
            
            response.raise_for_status()
            
            data = response.json()
            
            self.logger.debug(f"增强服务API响应: {data}")
            
            if "choices" not in data or len(data["choices"]) == 0:
                return False, "", "API response missing choices"
            
            message = data["choices"][0].get("message", {})
            content = message.get("content", "")
            
            if not content:
                return False, "", "API response missing content"
            
            self.logger.debug(f"增强服务返回内容: {content[:200]}...")
            
            return True, content.strip(), None
            
        except requests.exceptions.Timeout:
            return False, "", "API request timeout"
        except requests.exceptions.ConnectionError:
            return False, "", "API connection error"
        except requests.exceptions.RequestException as e:
            return False, "", f"API request failed: {str(e)}"
        except (KeyError, ValueError, TypeError) as e:
            return False, "", f"API response parse error: {str(e)}"

    def enhance(self, user_input: str) -> str:
        if not self.enabled:
            self.logger.debug("Enhance service is disabled, returning original input")
            return user_input
        
        if not user_input or not user_input.strip():
            return user_input
        
        success, result, error = self._call_api(user_input)
        
        if success:
            self.logger.debug(f"Prompt enhanced: '{user_input}' -> '{result}'")
            return result
        else:
            self.logger.warning(f"Enhance service unavailable: {error}, returning original input")
            return user_input

    def is_available(self) -> bool:
        if not self.enabled:
            return False
        
        api_key = self._get_api_key()
        return api_key is not None and api_key.strip() != ""


_enhance_service_instance: Optional[EnhanceService] = None


def get_enhance_service(config: Optional[Dict[str, Any]] = None) -> EnhanceService:
    global _enhance_service_instance
    if _enhance_service_instance is None:
        _enhance_service_instance = EnhanceService(config)
    return _enhance_service_instance


def enhance_prompt(user_input: str, config: Optional[Dict[str, Any]] = None) -> str:
    service = get_enhance_service(config)
    return service.enhance(user_input)

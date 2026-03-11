import json
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

from src.logger import get_logger


load_dotenv()


PLATFORM_SELECTION_PROMPT = """You are an intelligent routing assistant. Your task is to analyze the user's prompt and select the most suitable platform for content generation.

You need to:
1. Analyze the user's prompt to understand their intent
2. Determine if the request is for a static scene (image) or dynamic scene (video)
3. Check if the user explicitly wants a two-step process (generate image first, then convert to video)
4. Select the most appropriate platform based on the platform descriptions

Available platforms:
{platforms_info}

Respond in JSON format only:
{{
    "platform_index": <index of selected platform in the list, 0-based>,
    "save_type": "image" or "video",
    "next_step": null or "image-to-video",
    "reason": "brief explanation of your choice"
}}

Rules:
- If the prompt describes motion, action, or dynamic scene (like "running", "flying", "dancing"), set save_type to "video" and next_step to null
- If the prompt explicitly mentions generating image first then making it move (like "生成图片然后动起来", "先图片再视频"), set save_type to "image" and next_step to "image-to-video". In this case, you MUST select an IMAGE generation platform, NOT a video platform.
- If the prompt is for a static scene (like "a photo of", "a picture of", "portrait"), set save_type to "image" and next_step to null
- When next_step is "image-to-video", you MUST select an image platform (platform with description about generating images)
- Select the platform that best matches the user's intent based on platform descriptions
- Only output the JSON, nothing else"""

I2V_SELECTION_PROMPT = """You are an intelligent routing assistant for image-to-video conversion. Your task is to select the most suitable platform for converting an image to video.

User prompt: {prompt}
Image path: {image_path}

Available image-to-video platforms:
{platforms_info}

Respond in JSON format only:
{{
    "platform_index": <index of selected platform in the list, 0-based>,
    "reason": "brief explanation of your choice"
}}

Rules:
- Select the platform that best matches the user's prompt and available features
- Consider the platform's description and capabilities
- Only output the JSON, nothing else"""


class RouteService:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            config = {}
        
        enhance_config = config.get("enhance_service", {})
        
        self.enabled = enhance_config.get("enabled", True)
        self.model = enhance_config.get("model", "glm-4-flash")
        self.api_url = enhance_config.get("api_url", "https://open.bigmodel.cn/api/paas/v4/chat/completions")
        self.api_key_env = enhance_config.get("api_key_env", "GLM_API_KEY")
        self.max_tokens = enhance_config.get("max_tokens", 1000)
        self.temperature = enhance_config.get("temperature", 0.7)
        self.timeout = enhance_config.get("timeout", 30)
        
        self._api_key: Optional[str] = None
        self.logger = get_logger()

    def _get_api_key(self) -> Optional[str]:
        if self._api_key is not None:
            return self._api_key
        
        import os
        self._api_key = os.environ.get(self.api_key_env)
        return self._api_key

    def _build_headers(self) -> Dict[str, str]:
        api_key = self._get_api_key()
        headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _call_api(self, system_prompt: str, user_input: str) -> tuple:
        import os
        api_key = self._get_api_key()
        if not api_key:
            return False, "", f"API key not found in environment variable: {self.api_key_env}"
        
        try:
            headers = self._build_headers()
            body = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            self.logger.debug(f"Calling route API: {self.api_url}")
            
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
            
            self.logger.debug(f"路由服务API响应: {data}")
            
            if "choices" not in data or len(data["choices"]) == 0:
                return False, "", "API response missing choices"
            
            message = data["choices"][0].get("message", {})
            content = message.get("content", "")
            
            if not content:
                return False, "", "API response missing content"
            
            self.logger.debug(f"路由服务返回内容: {content[:500]}...")
            
            return True, content.strip(), None
            
        except requests.exceptions.Timeout:
            return False, "", "API request timeout"
        except requests.exceptions.ConnectionError:
            return False, "", "API connection error"
        except requests.exceptions.RequestException as e:
            return False, "", f"API request failed: {str(e)}"
        except (KeyError, ValueError, TypeError) as e:
            return False, "", f"API response parse error: {str(e)}"

    def _parse_json_response(self, content: str) -> Optional[Dict[str, Any]]:
        try:
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
            return None
        except json.JSONDecodeError:
            return None

    def _build_platforms_info(self, platforms: List[Dict[str, Any]]) -> str:
        info_lines = []
        for i, platform in enumerate(platforms):
            name = platform.get("name", "Unknown")
            description = platform.get("description", "No description")
            info_lines.append(f"[{i}] {name}: {description}")
        return "\n".join(info_lines)

    def select_platform(self, prompt: str, platforms: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.enabled:
            self.logger.debug("Route service is disabled, returning first platform")
            return {
                "platform": platforms[0] if platforms else {},
                "save_type": "image",
                "next_step": None
            }
        
        if not platforms:
            self.logger.warning("No platforms available for selection")
            return {
                "platform": {},
                "save_type": "image",
                "next_step": None
            }
        
        if len(platforms) == 1:
            self.logger.debug("Only one platform available, returning it directly")
            return {
                "platform": platforms[0],
                "save_type": "image",
                "next_step": None
            }
        
        platforms_info = self._build_platforms_info(platforms)
        system_prompt = PLATFORM_SELECTION_PROMPT.format(platforms_info=platforms_info)
        
        success, content, error = self._call_api(system_prompt, prompt)
        
        if not success:
            self.logger.warning(f"Route service API call failed: {error}, returning first platform")
            return {
                "platform": platforms[0],
                "save_type": "image",
                "next_step": None
            }
        
        self.logger.debug(f"模型返回内容: {content}")
        
        result = self._parse_json_response(content)
        
        if not result:
            self.logger.warning(f"Failed to parse route response: {content}")
            return {
                "platform": platforms[0],
                "save_type": "image",
                "next_step": None
            }
        
        self.logger.debug(f"解析后的JSON: {result}")
        
        platform_index = result.get("platform_index", 0)
        save_type = result.get("save_type", "image")
        next_step = result.get("next_step")
        
        if not isinstance(platform_index, int) or platform_index < 0 or platform_index >= len(platforms):
            self.logger.warning(f"Invalid platform_index: {platform_index}")
            platform_index = 0
        
        if save_type not in ["image", "video"]:
            save_type = "image"
        
        if next_step not in [None, "image-to-video"]:
            next_step = None
        
        selected_platform = platforms[platform_index]
        reason = result.get("reason", "")
        
        self.logger.info(f"Selected platform: {selected_platform.get('name')} (save_type={save_type}, next_step={next_step}), reason: {reason}")
        
        return {
            "platform": selected_platform,
            "save_type": save_type,
            "next_step": next_step
        }

    def select_i2v_platform(self, prompt: str, image_path: str, i2v_platforms: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.enabled:
            self.logger.debug("Route service is disabled, returning first i2v platform")
            return {
                "platform": i2v_platforms[0] if i2v_platforms else {},
                "save_type": "video"
            }
        
        if not i2v_platforms:
            self.logger.warning("No i2v platforms available for selection")
            return {
                "platform": {},
                "save_type": "video"
            }
        
        if len(i2v_platforms) == 1:
            self.logger.debug("Only one i2v platform available, returning it directly")
            return {
                "platform": i2v_platforms[0],
                "save_type": "video"
            }
        
        platforms_info = self._build_platforms_info(i2v_platforms)
        system_prompt = I2V_SELECTION_PROMPT.format(
            prompt=prompt,
            image_path=image_path,
            platforms_info=platforms_info
        )
        
        success, content, error = self._call_api(system_prompt, prompt)
        
        if not success:
            self.logger.warning(f"Route service API call failed: {error}, returning first i2v platform")
            return {
                "platform": i2v_platforms[0],
                "save_type": "video"
            }
        
        self.logger.debug(f"图生视频模型返回内容: {content}")
        
        result = self._parse_json_response(content)
        
        if not result:
            self.logger.warning(f"Failed to parse i2v route response: {content}")
            return {
                "platform": i2v_platforms[0],
                "save_type": "video"
            }
        
        self.logger.debug(f"图生视频解析后的JSON: {result}")
        
        platform_index = result.get("platform_index", 0)
        
        if not isinstance(platform_index, int) or platform_index < 0 or platform_index >= len(i2v_platforms):
            self.logger.warning(f"Invalid platform_index: {platform_index}")
            platform_index = 0
        
        selected_platform = i2v_platforms[platform_index]
        reason = result.get("reason", "")
        
        self.logger.info(f"Selected i2v platform: {selected_platform.get('name')}, reason: {reason}")
        
        return {
            "platform": selected_platform,
            "save_type": "video"
        }

    def is_available(self) -> bool:
        if not self.enabled:
            return False
        
        api_key = self._get_api_key()
        return api_key is not None and api_key.strip() != ""


_route_service_instance: Optional[RouteService] = None


def get_route_service(config: Optional[Dict[str, Any]] = None) -> RouteService:
    global _route_service_instance
    if _route_service_instance is None:
        _route_service_instance = RouteService(config)
    return _route_service_instance

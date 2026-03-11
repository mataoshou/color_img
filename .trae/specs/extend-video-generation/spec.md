# AI视频生成系统扩展 Spec

## Why

用户需要将现有的AI图片生成系统扩展为完整的AI内容生成系统，支持从文本生成视频的能力。基于现有代码分析，只需最小改动即可支持视频生成。

## 平台调研结果

### 完全免费且有API的平台

| 平台                       | 类型        | 免费情况     | API支持         | 中文支持 |
| ------------------------ | --------- | -------- | ------------- | ---- |
| **智谱AI CogVideoX-Flash** | 文生视频、图生视频 | **完全免费** | ✅ 有API        | ✅ 优秀 |
| **阿里通义万相**               | 文生视频、图生视频 | **完全免费** | ✅ 有API（阿里云百炼） | ✅ 优秀 |

### 推荐：智谱AI CogVideoX-Flash

* **完全免费**，无需付费

* 支持文生视频、图生视频

* API已上线，可直接调用

* 国内首个视频生成API

### 推荐：阿里通义万相

* **完全免费**，官网和API均可免费使用

* 支持文生视频、图生视频、首尾帧生视频

* 可在阿里云百炼平台调用API

* 支持音画同步视频生成

### 结论

系统支持以上两个完全免费且有API的视频生成平台。

### 智能路由

系统支持**大模型自动判断**生成类型，无需手动配置 mode：

* 分析提示词语义，自动判断生成图片还是视频

* 例如："一只猫" → 图片，"一只猫在奔跑" → 视频

* 复用现有的 EnhanceService 进行判断

## 现有代码分析

### ServiceClient 已有基础

* `is_async` 属性已存在（第25行），但未实现异步轮询逻辑

* `_process_response` 已支持 `binary`、`image_url`、`json`、`is_base64` 多种响应类型

* `_download_image` 已实现URL下载，**不区分图片和视频**（都返回 bytes）

* **格式检测在 Saver 层进行**，ServiceClient 只负责获取数据

### PlatformManager 可完全复用

* 初始化所有平台的 ServiceClient

* 循环尝试每个平台

* 每个平台内部重试

* 只需传入不同的平台列表即可

### ImageSaver 可复用模式

* 目录创建、文件命名、冲突解决逻辑相同

* 只需修改格式检测（MP4/WebM）

## What Changes

* **扩展 ServiceClient**：实现 `is_async=True` 时的轮询逻辑

* **创建 VideoSaver**：复用 ImageSaver 模式

* **扩展 main.py**：根据智能路由结果选择平台列表

* **更新配置**：添加视频平台配置

## Impact

* 修改 `src/service_client.py` - 实现异步轮询

* 新增 `src/video_saver.py` - 视频保存

* 修改 `main.py` - 支持智能路由

* 修改 `config.json` - 添加视频平台

## ADDED Requirements

### Requirement: 智能路由

系统SHALL通过大模型自动判断生成类型，无需手动配置 mode。

#### Scenario: 自动判断生成图片

* **GIVEN** 用户输入提示词 "一只猫"

* **WHEN** 系统分析提示词语义

* **THEN** 大模型判断为静态场景，生成图片

#### Scenario: 自动判断生成视频

* **GIVEN** 用户输入提示词 "一只猫在奔跑"

* **WHEN** 系统分析提示词语义

* **THEN** 大模型判断为动态场景，生成视频

#### Scenario: 复用现有增强服务

* **GIVEN** 现有的 EnhanceService

* **WHEN** 需要判断生成类型

* **THEN** 复用 EnhanceService 的 LLM 调用能力

### Requirement: 异步API轮询

系统SHALL支持异步视频API的轮询机制。

#### Scenario: 异步轮询模式

* **GIVEN** 平台配置中 `is_async` 为 `true`

* **WHEN** 调用 ServiceClient.request()

* **THEN** 系统提交任务后轮询状态，直到完成或超时

## 配置结构

所有平台统一配置，**完全由大模型控制**：

```json
{
  "platforms": [
    {
      "name": "siliconflow-flux",
      "description": "生成高质量图片，适合静态场景、人物、风景、物体",
      "api_url": "https://api.siliconflow.cn/v1/images/generations",
      "request_method": "POST",
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
      "result_url_path": "images.0.url"
    },
    {
      "name": "zhipu-cogvideox-flash",
      "description": "文生视频，适合动态场景、运动、变化过程",
      "api_url": "https://open.bigmodel.cn/api/paas/v4/videos/generations",
      "request_method": "POST",
      "request_headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer {api_key}"
      },
      "request_body": {
        "model": "cogvideox-flash",
        "prompt": "{prompt}"
      },
      "auth_type": "bearer",
      "api_key_env": "GLM_API_KEY",
      "is_async": true,
      "async_config": {
        "task_id_path": "id",
        "status_url": "https://open.bigmodel.cn/api/paas/v4/async-result/{task_id}",
        "status_path": "task_status",
        "status_complete_value": "SUCCESS",
        "result_url_path": "video_result.0.url",
        "poll_interval": 10,
        "max_poll_time": 600
      }
    },
    {
      "name": "zhipu-viduq1-image",
      "description": "图生视频，将静态图片转为动态视频",
      "api_url": "https://open.bigmodel.cn/api/paas/v4/videos/generations",
      "request_method": "POST",
      "request_headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer {api_key}"
      },
      "request_body": {
        "model": "viduq1-image",
        "image_url": "{image_url}",
        "prompt": "{prompt}",
        "duration": 5
      },
      "auth_type": "bearer",
      "api_key_env": "GLM_API_KEY",
      "is_async": true,
      "async_config": {
        "task_id_path": "id",
        "status_url": "https://open.bigmodel.cn/api/paas/v4/async-result/{task_id}",
        "status_path": "task_status",
        "status_complete_value": "SUCCESS",
        "result_url_path": "video_result.0.url",
        "poll_interval": 10,
        "max_poll_time": 600
      }
    },
    {
      "name": "aliyun-wan-text",
      "description": "文生视频，适合动态场景，支持音画同步",
      "api_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis",
      "request_method": "POST",
      "request_headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer {api_key}",
        "X-DashScope-Async": "enable"
      },
      "request_body": {
        "model": "wanx2.1-t2v-turbo",
        "input": {
          "prompt": "{prompt}"
        }
      },
      "auth_type": "bearer",
      "api_key_env": "ALIYUN_API_KEY",
      "is_async": true,
      "async_config": {
        "task_id_path": "output.task_id",
        "status_url": "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}",
        "status_path": "output.task_status",
        "status_complete_value": "SUCCEEDED",
        "result_url_path": "output.video_url",
        "poll_interval": 15,
        "max_poll_time": 600
      }
    }
  ]
}
```

### 设计原则

* **大模型完全控制**：选择平台 + 返回保存类型 + 决定是否需要后续流程

* **一次大模型调用**：返回所有决策信息

* **系统只执行**：根据大模型返回执行，不做判断

* **支持多步流程**：文本→图片→视频

## 接口定义

### RouteService

```python
class RouteService:
    def __init__(self, config: dict):
        """复用 enhance_service 配置进行 LLM 调用"""
    
    def select_platform(self, prompt: str) -> dict:
        """
        返回: {"platform": 平台配置dict, "save_type": "image或video", "next_step": "image-to-video或None"}
        """
    
    def select_i2v_platform(self, prompt: str, image_path: str, i2v_platforms: list) -> dict:
        """
        返回: {"platform": 平台配置dict, "save_type": "video"}
        """
```

### ServiceClient 扩展

```python
# 新增属性（在 __init__ 中读取）
self.result_url_path = platform_config.get("result_url_path") or platform_config.get("image_url_path", "")

# 异步配置（仅当 is_async=True 时读取）
async_config = platform_config.get("async_config", {})
self.task_id_path = async_config.get("task_id_path", "")
self.status_url = async_config.get("status_url", "")
self.status_path = async_config.get("status_path", "")
self.status_complete_value = async_config.get("status_complete_value", "")
self.result_url_path = async_config.get("result_url_path", self.result_url_path)  # 异步结果路径优先
self.poll_interval = async_config.get("poll_interval", 10)
self.max_poll_time = async_config.get("max_poll_time", 600)

# request() 方法已支持 **kwargs，无需修改签名
# 图生视频平台的 {image_url} 模板会通过 kwargs 自动替换
def request(self, prompt, **kwargs) -> Tuple[bool, bytes, Optional[str]]:
    """根据 is_async 选择同步或异步模式，kwargs 支持任意模板变量"""

def _request_async(self, prompt, **kwargs) -> Tuple[bool, bytes, Optional[str]]:
    """
    异步轮询实现：
    1. 提交任务 → 从响应提取 task_id（使用 task_id_path）
    2. 轮询状态 → 检查 status_path 是否等于 status_complete_value
    3. 获取结果 → 从轮询响应提取 result_url_path，下载内容
    """
```

### VideoSaver

```python
class VideoSaver:
    def __init__(self, config: dict):
        """复用 ImageSaver 的配置结构"""
    
    def save_video(self, video_data: bytes, prompt: str = None) -> str:
        """返回保存的文件路径"""
    
    def _detect_video_format(self, data: bytes) -> str:
        """返回 .mp4 或 .webm"""
```

### PlatformManager 扩展

```python
def generate(self, prompt: str, **kwargs) -> Tuple[bool, bytes, Optional[str]]:
    """支持任意 kwargs 参数传递给 ServiceClient（如 image_url）"""
```


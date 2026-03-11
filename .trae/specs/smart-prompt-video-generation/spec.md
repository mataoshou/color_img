# 智能提示词与场景规划内容生成 Spec

## Why

现有系统已支持图片和视频生成，但用户需要手动提供提示词。用户希望系统能够：
1. 自动从网络获取高质量的**图片/视频生成提示词最佳实践**
2. 使用大模型（LLM）智能分析主题，自动进行**场景分片和时间规划**
3. 基于规划自动生成**连贯的系列图片或长视频**

**核心价值**：从"用户提供提示词"升级为"用户提供主题，系统自动完成全流程"，同时支持图片和视频两种输出形式。

## What Changes

- 新增 `PromptKnowledgeService` 提示词知识服务，从网络获取图片/视频提示词最佳实践
- 新增 `ScenePlanner` 场景规划器，使用 LLM 进行智能分片和时间规划
- 新增 `ImageSeriesGenerator` 系列图片生成器，支持主题驱动的系列图片生成
- 扩展 `LongVideoGenerator`，支持基于场景规划自动生成长视频
- 扩展 `EnhanceService`，支持图片和视频两种提示词增强模式
- 扩展命令行参数，支持主题输入模式和输出类型选择

## Impact

- Affected specs: generate-long-video（依赖其视频生成能力）, extend-video-generation（依赖其图片生成能力）
- Affected code:
  - 新增 `src/prompt_knowledge_service.py`
  - 新增 `src/scene_planner.py`
  - 新增 `src/image_series_generator.py`
  - 修改 `src/long_video_generator.py`
  - 修改 `src/enhance_service.py`
  - 修改 `main.py`
  - 修改 `config.json`

## ADDED Requirements

### Requirement: 提示词知识获取

系统SHALL支持从网络获取图片/视频生成提示词的最佳实践。

#### Scenario: 获取图片提示词最佳实践
- **GIVEN** 系统初始化或用户请求图片生成
- **WHEN** 系统调用提示词知识服务
- **THEN** 系统获取并缓存图片提示词的结构化知识（摄影分层结构、构图术语、光影描述等）

#### Scenario: 获取视频提示词最佳实践
- **GIVEN** 系统初始化或用户请求视频生成
- **WHEN** 系统调用提示词知识服务
- **THEN** 系统获取并缓存视频提示词的结构化知识（七层结构、运镜术语、光影描述等）

#### Scenario: 提示词模板库
- **GIVEN** 获取的提示词知识
- **WHEN** 系统需要生成提示词
- **THEN** 系统基于模板库生成符合最佳实践的提示词（区分图片/视频模板）

#### Scenario: 知识缓存
- **GIVEN** 已获取的提示词知识
- **WHEN** 后续请求相同知识
- **THEN** 从缓存读取，避免重复网络请求

### Requirement: 智能场景分片

系统SHALL使用大模型将主题分解为多个连贯的场景片段。

#### Scenario: 图片场景分片
- **GIVEN** 用户输入主题（如"四季变化"）并选择图片输出
- **WHEN** 系统调用场景规划器
- **THEN** LLM 将主题分解为多个场景（如"春日花开"、"夏日骄阳"、"秋叶飘落"、"冬雪皑皑"），每个场景对应一张图片

#### Scenario: 视频场景分片
- **GIVEN** 用户输入主题（如"一只猫的一天"）并选择视频输出
- **WHEN** 系统调用场景规划器
- **THEN** LLM 将主题分解为多个场景（如"清晨醒来"、"伸懒腰"、"吃早餐"、"玩耍"、"午睡"等），每个场景包含多个视频片段

#### Scenario: 场景连贯性保证
- **GIVEN** 分解的场景列表
- **WHEN** 生成场景提示词
- **THEN** 相邻场景之间保持视觉和叙事连贯性

#### Scenario: 场景数量自适应
- **GIVEN** 目标时长（视频）或目标数量（图片）
- **WHEN** 规划场景数量
- **THEN** 根据目标自动计算合适的场景数量

### Requirement: 时间规划（视频专用）

系统SHALL为视频的每个场景分配合适的时长。

#### Scenario: 均匀时间分配
- **GIVEN** 目标时长5分钟，10个场景
- **WHEN** 进行时间规划
- **THEN** 每个场景分配30秒（约6个片段）

#### Scenario: 场景时长调整
- **GIVEN** 特定场景需要更长展示时间
- **WHEN** LLM 分析场景重要性
- **THEN** 重要场景分配更多片段，过渡场景分配较少片段

#### Scenario: 总时长控制
- **GIVEN** 所有场景的时长规划
- **WHEN** 汇总计算
- **THEN** 总时长接近用户指定的目标时长

### Requirement: 图片提示词增强

系统SHALL支持图片专用的提示词增强，包含构图、光影、风格等元素。

#### Scenario: 图片提示词分层结构
- **GIVEN** 基础场景描述
- **WHEN** 进行图片提示词增强
- **THEN** 输出包含分层结构：主体、环境、构图、光影、风格、质量参数

#### Scenario: 摄影术语应用
- **GIVEN** 场景需要特定构图
- **WHEN** 生成提示词
- **THEN** 自动添加摄影术语（Rule of Thirds、Golden Ratio、Leading Lines等）

#### Scenario: 风格词添加
- **GIVEN** 场景风格需求
- **WHEN** 生成提示词
- **THEN** 自动添加艺术风格、画质描述词

### Requirement: 视频提示词增强

系统SHALL支持视频专用的提示词增强，包含运镜、光影、物理属性等元素。

#### Scenario: 视频提示词七层结构
- **GIVEN** 基础场景描述
- **WHEN** 进行视频提示词增强
- **THEN** 输出包含七层结构：主体、动作、环境、运镜、光影、情绪、负向约束

#### Scenario: 运镜术语应用
- **GIVEN** 场景需要镜头运动
- **WHEN** 生成提示词
- **THEN** 自动添加标准运镜术语（Dolly In、Pan、Tracking、Crane等）

#### Scenario: 感觉词添加
- **GIVEN** 场景氛围需求
- **WHEN** 生成提示词
- **THEN** 自动添加速度感、氛围感、视角感词汇

### Requirement: 主题驱动的系列图片生成

系统SHALL支持用户只提供主题，自动生成系列图片。

#### Scenario: 主题输入模式（图片）
- **GIVEN** 用户输入主题"四季变化"和数量4
- **WHEN** 执行生成
- **THEN** 系统自动：获取知识 → 场景分片 → 提示词增强 → 图片生成 → 输出系列图片

#### Scenario: 系列图片命名
- **GIVEN** 生成的系列图片
- **WHEN** 保存文件
- **THEN** 文件名包含主题和场景序号（如"四季变化_01_春.jpg"）

#### Scenario: 与现有模式兼容
- **GIVEN** 用户不使用 `--topic` 参数
- **WHEN** 提供普通提示词
- **THEN** 使用现有的单张图片生成模式

### Requirement: 主题驱动的长视频生成

系统SHALL支持用户只提供主题，自动完成全流程生成。

#### Scenario: 主题输入模式（视频）
- **GIVEN** 用户输入主题"海边日落"和目标时长3分钟
- **WHEN** 执行生成
- **THEN** 系统自动：获取知识 → 场景分片 → 时间规划 → 提示词增强 → 视频生成 → 拼接输出

#### Scenario: 与现有模式兼容
- **GIVEN** 用户使用 `--duration` 参数
- **WHEN** 不提供 `--topic` 参数
- **THEN** 使用现有的统一提示词或提示词文件模式

#### Scenario: 进度显示
- **GIVEN** 正在执行主题驱动的生成
- **WHEN** 用户查看控制台
- **THEN** 显示当前阶段（场景规划/提示词生成/内容生成/拼接）

### Requirement: 智能输出类型判断

系统SHALL在主题模式下根据主题内容和参数自动判断输出类型（图片或视频）。

#### Scenario: 自动判断输出类型
- **GIVEN** 用户输入主题"一只猫在奔跑"并使用 `--topic`
- **WHEN** 系统分析主题语义
- **THEN** 自动判断为视频输出（动态场景）

#### Scenario: 参数明确指定类型
- **GIVEN** 用户使用 `--topic --count 4` 参数
- **WHEN** 执行生成
- **THEN** 自动切换为系列图片模式（因为有 `--count` 参数）

#### Scenario: 参数明确指定视频
- **GIVEN** 用户使用 `--topic --duration 2` 参数
- **WHEN** 执行生成
- **THEN** 自动切换为长视频模式（因为有 `--duration` 参数）

#### Scenario: 无明确参数时的判断
- **GIVEN** 用户只使用 `--topic` 参数
- **WHEN** 系统分析主题语义
- **THEN** 根据主题内容判断输出类型（动态→视频，静态→图片）

#### Scenario: 复用现有RouteService
- **GIVEN** 主题模式生成的提示词
- **WHEN** 需要选择生成平台
- **THEN** 复用现有的 `RouteService.select_platform()` 方法

## MODIFIED Requirements

### Requirement: 命令行参数扩展

main.py 命令行参数SHALL支持主题输入模式。

**设计原则**：
- `prompt` 参数语义保持不变，始终是必需的位置参数
- `--topic` 作为模式开关，改变 `prompt` 的处理方式
- 复用现有的 `RouteService` 智能路由能力
- 保持向后兼容，不影响现有使用方式

**新增参数**：
- `--topic` - 主题模式开关，启用智能场景规划（此时 `prompt` 被解释为主题）
- `--count` - 图片数量（图片模式），可选，默认由LLM决定
- `--style` - 内容风格（电影感、纪录片、Vlog等），可选

**参数组合规则**：
- `prompt`（无其他参数）：现有模式，单张图片/视频（RouteService智能判断）
- `prompt` + `--duration`：现有模式，统一提示词的长视频生成
- `prompt` + `--prompts-file`：现有模式，提示词序列的长视频生成
- `prompt` + `--topic`：主题模式，LLM自动判断输出类型并生成
- `prompt` + `--topic` + `--count`：主题模式，系列图片生成
- `prompt` + `--topic` + `--duration`：主题模式，长视频生成

**与现有智能路由的关系**：
- 主题模式下，`ScenePlanner` 负责场景分片和提示词生成
- 生成的提示词仍通过 `RouteService` 进行平台选择
- 复用现有的平台选择逻辑，避免重复实现

## 配置结构

```json
{
  "scene_planner": {
    "enabled": true,
    "model": "glm-4-flash",
    "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    "api_key_env": "GLM_API_KEY",
    "max_scenes": 20,
    "min_scene_duration_seconds": 5,
    "max_scene_duration_seconds": 30,
    "default_style": "cinematic"
  },
  "prompt_knowledge": {
    "enabled": true,
    "cache_enabled": true,
    "cache_file": "cache/prompt_knowledge.json",
    "cache_expire_hours": 24,
    "sources": [
      {
        "type": "web_search",
        "query": "AI image video generation prompt best practices 2025",
        "enabled": true
      }
    ]
  },
  "image_prompt_templates": {
    "photography": {
      "structure": ["subject", "environment", "composition", "lighting", "style", "quality"],
      "composition_terms": ["Rule of Thirds", "Golden Ratio", "Leading Lines", "Symmetry"],
      "lighting_terms": ["Golden Hour", "Blue Hour", "Studio Lighting", "Natural Light"],
      "style_words": ["professional photography", "editorial", "fine art"]
    },
    "digital_art": {
      "structure": ["subject", "style", "details", "colors", "mood", "quality"],
      "style_words": ["digital painting", "concept art", "illustration", "3D render"]
    }
  },
  "video_prompt_templates": {
    "cinematic": {
      "structure": ["subject", "action", "environment", "camera", "lighting", "mood", "negative"],
      "camera_terms": ["Dolly In", "Pan Left", "Tracking Shot", "Crane Shot", "Static"],
      "mood_words": ["cinematic", "dreamy", "intense", "peaceful"]
    },
    "documentary": {
      "structure": ["subject", "action", "environment", "camera", "narration_hint"],
      "camera_terms": ["Handheld", "Steadicam", "Aerial"],
      "mood_words": ["authentic", "raw", "observational"]
    },
    "vlog": {
      "structure": ["subject", "action", "environment", "camera", "personal_touch"],
      "camera_terms": ["Selfie", "POV", "Handheld"],
      "mood_words": ["casual", "friendly", "relaxed"]
    }
  }
}
```

## 接口定义

### PromptKnowledgeService

```python
class PromptKnowledgeService:
    def __init__(self, config: dict):
        """初始化提示词知识服务"""
    
    def fetch_image_prompt_knowledge(self) -> dict:
        """
        从网络获取图片提示词最佳实践
        
        Returns:
            {
                "layered_structure": [...],
                "composition_terms": [...],
                "lighting_descriptions": [...],
                "style_words": {...},
                "quality_params": [...]
            }
        """
    
    def fetch_video_prompt_knowledge(self) -> dict:
        """
        从网络获取视频提示词最佳实践
        
        Returns:
            {
                "seven_layer_structure": [...],
                "camera_movement_terms": [...],
                "lighting_descriptions": [...],
                "mood_words": {...},
                "negative_prompts": [...]
            }
        """
    
    def get_cached_knowledge(self, knowledge_type: str) -> dict:
        """获取缓存的提示词知识"""
    
    def build_image_prompt_from_template(self, scene: dict, style: str = "photography") -> str:
        """
        基于模板生成图片提示词
        
        Args:
            scene: 场景信息 {"subject": ..., "environment": ...}
            style: 图片风格
        
        Returns:
            结构化的图片提示词
        """
    
    def build_video_prompt_from_template(self, scene: dict, style: str = "cinematic") -> str:
        """
        基于模板生成视频提示词
        
        Args:
            scene: 场景信息 {"subject": ..., "action": ..., "environment": ...}
            style: 视频风格
        
        Returns:
            结构化的视频提示词
        """
```

### ScenePlanner

```python
class ScenePlanner:
    def __init__(self, config: dict, prompt_knowledge_service):
        """初始化场景规划器"""
    
    def plan_for_images(self, topic: str, count: int, style: str = "photography") -> dict:
        """
        规划图片场景分片
        
        Args:
            topic: 用户输入的主题
            count: 目标图片数量
            style: 图片风格
        
        Returns:
            {
                "topic": "四季变化",
                "total_count": 4,
                "scenes": [
                    {
                        "index": 0,
                        "title": "春日花开",
                        "description": "樱花盛开的春日景象",
                        "prompt": "...",
                        "composition": "Rule of Thirds",
                        "lighting": "Soft morning light",
                        "style": "romantic"
                    },
                    ...
                ]
            }
        """
    
    def plan_for_video(self, topic: str, duration_minutes: float, style: str = "cinematic") -> dict:
        """
        规划视频场景分片和时间分配
        
        Args:
            topic: 用户输入的主题
            duration_minutes: 目标时长（分钟）
            style: 视频风格
        
        Returns:
            {
                "topic": "海边日落",
                "total_duration_minutes": 3.0,
                "total_segments": 36,
                "scenes": [
                    {
                        "index": 0,
                        "title": "海浪轻拍沙滩",
                        "description": "金色阳光下的海浪缓缓涌向沙滩",
                        "duration_seconds": 30,
                        "segment_count": 6,
                        "prompts": ["...", "...", ...],
                        "camera": "Slow Dolly In",
                        "lighting": "Golden hour",
                        "mood": "peaceful"
                    },
                    ...
                ]
            }
        """
    
    def _call_llm_for_image_planning(self, topic: str, count: int, style: str) -> list:
        """调用 LLM 进行图片场景规划"""
    
    def _call_llm_for_video_planning(self, topic: str, target_segments: int, style: str) -> list:
        """调用 LLM 进行视频场景规划"""
```

### ImageSeriesGenerator

```python
class ImageSeriesGenerator:
    def __init__(self, config: dict, platform_manager, route_service, prompt_knowledge_service):
        """初始化系列图片生成器"""
    
    def generate_from_topic(self, topic: str, count: int, style: str = "photography") -> list[str]:
        """
        基于主题生成系列图片
        
        流程：
        1. 调用 ScenePlanner 进行场景规划
        2. 为每个场景生成提示词
        3. 逐个生成图片
        4. 返回所有图片路径
        
        Args:
            topic: 主题描述
            count: 图片数量
            style: 图片风格
        
        Returns:
            所有图片文件路径列表
        """
```

### LongVideoGenerator 扩展

```python
def generate_from_topic(
    self,
    topic: str,
    duration_minutes: float,
    style: str = "cinematic"
) -> str:
    """
    基于主题生成长视频
    
    流程：
    1. 调用 ScenePlanner 进行场景规划
    2. 获取每个场景的提示词序列
    3. 链式生成所有视频片段
    4. 拼接输出最终视频
    
    Args:
        topic: 主题描述
        duration_minutes: 目标时长
        style: 视频风格
    
    Returns:
        最终视频文件路径
    """
```

## 技术方案

### 图片场景规划 LLM Prompt

```text
你是一位专业的摄影师和视觉设计师。请根据用户提供的主题，将其分解为多个连贯的视觉场景，用于生成系列图片。

## 输入
- 主题: {topic}
- 目标图片数: {count}
- 风格: {style}

## 要求
1. 将主题分解为指定数量的场景
2. 场景之间要有视觉连贯性和叙事性
3. 每个场景需要包含：标题、描述、构图方式、光影氛围、风格基调
4. 描述要具体，便于AI生成

## 输出格式 (JSON)
{
  "scenes": [
    {
      "title": "场景标题",
      "description": "详细场景描述",
      "composition": "构图方式",
      "lighting": "光影描述",
      "style": "风格基调"
    }
  ]
}

请直接输出 JSON，不要有其他内容。
```

### 视频场景规划 LLM Prompt

```text
你是一位专业的视频导演和场景规划师。请根据用户提供的主题，将其分解为多个连贯的视频场景。

## 输入
- 主题: {topic}
- 目标片段数: {target_segments}
- 视频风格: {style}

## 要求
1. 将主题分解为 5-15 个场景，每个场景包含多个片段
2. 场景之间要有叙事连贯性
3. 每个场景需要包含：标题、描述、运镜方式、光影氛围、情绪基调
4. 总片段数应接近目标片段数

## 输出格式 (JSON)
{
  "scenes": [
    {
      "title": "场景标题",
      "description": "详细场景描述",
      "segment_count": 5,
      "camera": "运镜方式",
      "lighting": "光影描述",
      "mood": "情绪基调"
    }
  ]
}

请直接输出 JSON，不要有其他内容。
```

### 图片提示词分层结构

```
1. 主体 (Subject): 核心对象描述
2. 环境 (Environment): 场景背景和细节
3. 构图 (Composition): 画面布局方式
4. 光影 (Lighting): 光线和氛围
5. 风格 (Style): 艺术风格
6. 质量 (Quality): 画质参数
```

### 视频提示词七层结构

```
1. 主体 (Subject): 核心对象描述
2. 动作 (Action): 主体在做什么
3. 环境 (Environment): 场景背景和细节
4. 运镜 (Camera): 镜头运动方式
5. 光影 (Lighting): 光线和氛围
6. 情绪 (Mood): 整体感觉词
7. 负向约束 (Negative): 避免的元素
```

### 生成流程

```
┌─────────────────────────────────────────────────────────────────┐
│                  主题驱动的内容生成流程                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  用户输入: "四季变化" --topic --count 4                          │
│                                                                 │
│  ┌────────────────┐                                             │
│  │ 1. 获取知识     │ 图片/视频提示词最佳实践、模板库              │
│  └───────┬────────┘                                             │
│          ▼                                                      │
│  ┌────────────────┐                                             │
│  │ 2. 场景规划     │ LLM 分解主题为多个场景                       │
│  └───────┬────────┘                                             │
│          │                                                      │
│          │  图片模式: 4个场景 → 4张图片                           │
│          │  视频模式: N个场景 → M个片段 → 长视频                   │
│          ▼                                                      │
│  ┌────────────────┐                                             │
│  │ 3. 提示词生成   │ 为每个场景生成结构化提示词                   │
│  └───────┬────────┘                                             │
│          │                                                      │
│          │  图片提示词:                                          │
│          │  "樱花盛开的春日景象，三分法构图，                      │
│          │   柔和晨光，浪漫风格，专业摄影"                         │
│          │                                                      │
│          │  视频提示词:                                          │
│          │  "金色阳光下的海浪缓缓涌向沙滩，                       │
│          │   镜头缓慢推进，金色逆光，电影感"                       │
│          ▼                                                      │
│  ┌────────────────┐                                             │
│  │ 4. 内容生成     │ 图片: 逐张生成                               │
│  │                │ 视频: 链式生成片段（保证连续性）              │
│  └───────┬────────┘                                             │
│          ▼                                                      │
│  ┌────────────────┐                                             │
│  │ 5. 输出        │ 图片: 系列图片文件                            │
│  │                │ 视频: 拼接后的长视频文件                      │
│  └────────────────┘                                             │
│                                                                 │
│  输出:                                                          │
│  - 图片: 四季变化_01_春.jpg, 四季变化_02_夏.jpg, ...             │
│  - 视频: long_video_20260311_xxx.mp4 (约3分钟)                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 依赖

无需新增依赖，复用现有的 `requests` 库进行网络请求。

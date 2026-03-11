# 连续长视频生成 Spec

## Why

现有系统已支持短视频生成（通常5-10秒），用户需要生成更长的连续视频（约5分钟）。通过生成多个视频片段并拼接的方式，实现长视频生成能力。

**核心挑战**：如何保证多个片段之间的视觉连续性？

**解决方案**：采用**图生视频链式生成**策略，使用前一个片段的最后一帧作为下一个片段的起始帧，确保视觉连续性。

## What Changes

- 新增 `VideoComposer` 视频拼接器，负责多视频片段拼接
- 新增 `LongVideoGenerator` 长视频生成器，协调多片段生成与拼接
- 扩展 `main.py` 命令行参数，支持长视频生成模式
- 扩展配置文件，支持长视频相关配置

## Impact

- Affected specs: extend-video-generation（依赖其视频生成能力）
- Affected code: 
  - 新增 `src/video_composer.py`
  - 新增 `src/long_video_generator.py`
  - 修改 `main.py`
  - 修改 `config.json`

## ADDED Requirements

### Requirement: 长视频生成

系统SHALL支持通过生成多个视频片段并拼接的方式生成长视频。

#### Scenario: 基本长视频生成
- **GIVEN** 用户输入提示词和目标时长（如5分钟）
- **WHEN** 系统执行长视频生成
- **THEN** 系统生成多个视频片段，拼接后输出一个完整的长视频文件

#### Scenario: 自动计算片段数量
- **GIVEN** 目标时长为5分钟，每个片段约5秒
- **WHEN** 系统计算需要生成的片段数量
- **THEN** 自动计算需要约60个片段

#### Scenario: 片段生成失败处理
- **GIVEN** 某个片段生成失败
- **WHEN** 系统检测到失败
- **THEN** 跳过该片段继续生成其他片段，最终拼接已成功的片段

### Requirement: 视频连续性保证

系统SHALL通过图生视频链式生成策略保证视频片段之间的连续性。

#### Scenario: 链式生成流程
- **GIVEN** 用户请求生成长视频
- **WHEN** 系统生成视频片段
- **THEN** 第一个片段使用文生视频生成，后续片段使用前一个片段的最后一帧作为起始帧进行图生视频

#### Scenario: 抽帧获取最后一帧
- **GIVEN** 一个视频片段生成完成
- **WHEN** 需要生成下一个片段
- **THEN** 系统从视频片段中抽取最后一帧作为图片

#### Scenario: 图生视频连续生成
- **GIVEN** 前一个片段的最后一帧图片
- **WHEN** 生成下一个视频片段
- **THEN** 使用图生视频平台，以该图片为起始帧，保持视觉连续性

#### Scenario: 无图生视频平台时的降级方案
- **GIVEN** 没有可用的图生视频平台
- **WHEN** 生成长视频
- **THEN** 使用统一提示词生成所有片段（内容可能不连贯，但风格一致）

### Requirement: 视频拼接

系统SHALL支持将多个视频片段拼接为一个连续视频。

#### Scenario: 视频格式一致
- **GIVEN** 所有视频片段格式相同（MP4）
- **WHEN** 执行拼接操作
- **THEN** 直接按顺序拼接，输出完整视频

#### Scenario: 视频格式不一致
- **GIVEN** 视频片段格式不同
- **WHEN** 执行拼接操作
- **THEN** 自动转码为统一格式后拼接

#### Scenario: 视频分辨率不一致
- **GIVEN** 视频片段分辨率不同
- **WHEN** 执行拼接操作
- **THEN** 自动缩放为统一分辨率后拼接

### Requirement: 提示词分段生成

系统SHALL支持为每个视频片段生成连贯的提示词。

#### Scenario: 统一提示词
- **GIVEN** 用户只提供一个提示词
- **WHEN** 生成多个视频片段
- **THEN** 所有片段使用相同提示词

#### Scenario: 提示词序列
- **GIVEN** 用户提供提示词序列（描述不同场景）
- **WHEN** 生成多个视频片段
- **THEN** 每个片段使用对应的提示词

#### Scenario: 大模型自动扩展
- **GIVEN** 用户启用大模型扩展功能
- **WHEN** 生成多个视频片段
- **THEN** 大模型为每个片段生成连贯的场景描述

### Requirement: 进度显示

系统SHALL在长视频生成过程中显示进度。

#### Scenario: 显示当前进度
- **GIVEN** 正在生成长视频
- **WHEN** 用户查看控制台
- **THEN** 显示当前片段进度（如 "片段 15/60"）

#### Scenario: 显示预估时间
- **GIVEN** 正在生成长视频
- **WHEN** 用户查看控制台
- **THEN** 显示预估剩余时间

### Requirement: 临时文件管理

系统SHALL妥善管理长视频生成过程中的临时文件。

#### Scenario: 临时文件存储
- **GIVEN** 正在生成长视频
- **WHEN** 生成视频片段和抽帧图片
- **THEN** 临时文件存储在指定目录（默认 `output/temp/`）

#### Scenario: 临时文件清理
- **GIVEN** 长视频生成完成
- **WHEN** 最终视频输出成功
- **THEN** 自动清理所有临时片段和抽帧图片

#### Scenario: 生成失败时的清理
- **GIVEN** 长视频生成过程中断或失败
- **WHEN** 用户取消或系统错误
- **THEN** 保留已生成的片段以便恢复，或根据配置清理

### Requirement: 平台选择策略

系统SHALL智能选择视频生成平台。

#### Scenario: 文生视频平台选择
- **GIVEN** 需要生成第一个片段
- **WHEN** 选择平台
- **THEN** 从文生视频平台中选择（description 包含"文生视频"）

#### Scenario: 图生视频平台选择
- **GIVEN** 需要生成后续片段（有起始帧）
- **WHEN** 选择平台
- **THEN** 从图生视频平台中选择（description 包含"图生视频"）

#### Scenario: 平台不可用时的处理
- **GIVEN** 选定的平台不可用（API密钥缺失等）
- **WHEN** 尝试生成
- **THEN** 自动切换到其他可用平台

### Requirement: 扩展性设计

系统SHALL设计为可扩展的架构。

#### Scenario: 支持不同的拼接策略
- **GIVEN** 新的拼接需求（如添加转场效果）
- **WHEN** 扩展系统
- **THEN** 可通过配置或插件方式添加新策略

#### Scenario: 支持不同的生成策略
- **GIVEN** 新的生成需求（如并行生成）
- **WHEN** 扩展系统
- **THEN** 可通过配置切换生成策略

## MODIFIED Requirements

### Requirement: 命令行参数扩展

main.py 命令行参数SHALL支持长视频生成模式。

**复用现有参数**（继承自 extend-video-generation）：
- `prompt` - 提示词（位置参数）
- `--width`, `-W` - 图片宽度
- `--height`, `-H` - 图片高度
- `--output`, `-o` - 输出目录
- `--no-enhance` - 禁用提示词增强

**新增参数**：
- `--duration` - 目标视频时长（分钟），启用长视频生成模式
- `--segment-duration` - 每个片段时长（秒），默认使用配置值
- `--prompts-file` - 提示词文件路径，用于分段生成

## 配置结构

```json
{
  "long_video": {
    "default_duration_minutes": 5,
    "segment_duration_seconds": 5,
    "max_concurrent_segments": 1,
    "output_format": "mp4",
    "output_resolution": "1080p",
    "transition": {
      "enabled": false,
      "type": "fade",
      "duration_seconds": 0.5
    },
    "retry_failed_segments": true,
    "min_success_ratio": 0.8,
    "temp_directory": "output/temp",
    "cleanup_on_success": true,
    "cleanup_on_failure": false
  }
}
```

## 接口定义

### VideoComposer

```python
class VideoComposer:
    def __init__(self, config: dict):
        """初始化视频拼接器"""
    
    def compose(self, video_paths: list[str], output_path: str, transition_config: dict = None) -> str:
        """
        拼接多个视频片段
        
        Args:
            video_paths: 视频片段路径列表
            output_path: 输出文件路径
            transition_config: 转场配置（可选）
        
        Returns:
            输出文件路径
        """
    
    def get_video_info(self, video_path: str) -> dict:
        """获取视频信息（时长、分辨率、格式等）"""
    
    def extract_last_frame(self, video_path: str) -> str:
        """
        从视频中抽取最后一帧
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            最后一帧图片的路径
        """
```

### LongVideoGenerator

```python
class LongVideoGenerator:
    def __init__(self, config: dict, platform_manager, route_service, video_composer):
        """初始化长视频生成器"""
    
    def generate(self, prompt: str, duration_minutes: float, prompts_list: list[str] = None) -> str:
        """
        生成长视频
        
        流程：
        1. 计算需要生成的片段数量
        2. 链式生成所有视频片段（保证连续性）
        3. 拼接所有片段为最终视频
        4. 清理临时文件
        
        Args:
            prompt: 基础提示词
            duration_minutes: 目标时长（分钟）
            prompts_list: 提示词列表（可选，用于分段生成）
        
        Returns:
            最终视频文件路径
        """
    
    def _generate_segment(self, prompt: str, index: int, start_frame_path: str = None) -> str:
        """
        生成单个视频片段
        
        Args:
            prompt: 提示词
            index: 片段索引
            start_frame_path: 起始帧图片路径（图生视频时使用）
        
        Returns:
            视频片段路径
        """
    
    def _calculate_segment_count(self, duration_minutes: float) -> int:
        """计算需要生成的片段数量"""
    
    def _generate_with_chain(self, prompt: str, segment_count: int) -> list[str]:
        """
        链式生成视频片段（保证连续性）
        
        流程：
        1. 第一个片段：文生视频
        2. 后续片段：抽取前一帧 → 图生视频
        
        Returns:
            所有视频片段路径列表
        """
```

## 技术方案

### 视频拼接方案

使用 `moviepy` 库进行视频拼接：

```python
from moviepy.editor import VideoFileClip, concatenate_videoclips

clips = [VideoFileClip(path) for path in video_paths]
final_clip = concatenate_videoclips(clips, method="compose")
final_clip.write_videofile(output_path)
```

### 抽帧方案

使用 `moviepy` 或 `opencv` 抽取视频最后一帧：

```python
from moviepy.editor import VideoFileClip

def extract_last_frame(video_path: str, output_path: str) -> str:
    clip = VideoFileClip(video_path)
    last_frame = clip.get_frame(clip.duration - 0.01)  # 获取接近末尾的帧
    
    from PIL import Image
    img = Image.fromarray(last_frame)
    img.save(output_path)
    return output_path
```

### 链式生成流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     长视频生成流程                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  提示词: "一只猫在奔跑"                                          │
│  目标时长: 5分钟                                                 │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐         ┌───────┐ │
│  │ 片段1    │───▶│ 片段2    │───▶│ 片段3    │─── ... ─▶│ 片段N │ │
│  │ 文生视频 │    │ 图生视频 │    │ 图生视频 │         │图生视频│ │
│  └──────────┘    └──────────┘    └──────────┘         └───────┘ │
│       │               ▲               ▲                      ▲  │
│       │    ┌──────────┘    ┌──────────┘                      │  │
│       │    │               │                                 │  │
│       ▼    │               │                                 │  │
│  ┌─────────┴┐         ┌────┴─────┐                     ┌────┴───┐│
│  │ 最后一帧 │────────▶│ 最后一帧 │───────── ... ──────▶│ 最后一帧││
│  └──────────┘         └──────────┘                     └────────┘│
│                                                                 │
│  最终输出: 拼接所有片段 → 5分钟连续视频                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 依赖

需要在 `requirements.txt` 中添加：
- `moviepy>=1.0.3` - 视频编辑
- `imageio-ffmpeg>=0.4.9` - FFmpeg 支持（moviepy 依赖）
- `Pillow>=9.0.0` - 图片处理（抽帧保存）

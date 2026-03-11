# Tasks

## Phase 1: 核心组件开发

- [x] Task 1: 创建 VideoComposer 视频拼接器
  - [x] 创建 `src/video_composer.py`
  - [x] 实现 `get_video_info()` 方法获取视频信息
  - [x] 实现 `compose()` 方法拼接视频片段
  - [x] 实现 `extract_last_frame()` 方法抽取视频最后一帧
  - [x] 处理视频格式不一致的情况（统一转码）
  - [x] 处理视频分辨率不一致的情况（统一缩放）

- [x] Task 2: 创建 LongVideoGenerator 长视频生成器
  - [x] 创建 `src/long_video_generator.py`
  - [x] 实现 `_calculate_segment_count()` 计算片段数量
  - [x] 实现 `_generate_segment()` 生成单个片段（支持文生视频和图生视频）
  - [x] 实现 `_generate_with_chain()` 链式生成视频片段（保证连续性）
  - [x] 实现 `generate()` 协调多片段生成与拼接
  - [x] 实现进度显示功能
  - [x] 实现无图生视频平台时的降级方案
  - [x] 实现平台选择策略（文生视频 vs 图生视频）

## Phase 2: 提示词处理

- [x] Task 3: 扩展提示词生成能力
  - [x] 实现统一提示词模式（所有片段使用相同提示词）
  - [x] 实现提示词序列模式（每个片段使用不同提示词）
  - [ ] 扩展 EnhanceService 支持批量提示词生成（可选）

## Phase 3: 命令行扩展

- [x] Task 4: 扩展 main.py 命令行参数
  - [x] 添加 `--duration` 参数（目标时长，分钟）
  - [x] 添加 `--segment-duration` 参数（片段时长，秒）
  - [x] 添加 `--prompts-file` 参数（提示词文件路径）
  - [x] 实现长视频生成模式入口

## Phase 4: 配置更新

- [x] Task 5: 更新配置文件
  - [x] config.json 添加 `long_video` 配置节（包含临时文件管理配置）
  - [x] requirements.txt 添加 moviepy、Pillow 依赖

## Phase 5: 临时文件管理

- [x] Task 6: 实现临时文件管理
  - [x] 创建临时目录（默认 `output/temp/`）
  - [x] 生成成功后自动清理临时文件
  - [x] 生成失败时保留临时文件（可配置）

## Phase 6: 测试

- [x] Task 7: 编写测试
  - [x] VideoComposer 单元测试（包括抽帧测试）
  - [x] LongVideoGenerator 单元测试（包括链式生成测试）
  - [x] 临时文件管理测试
  - [x] 集成测试（端到端长视频生成）

# Task Dependencies

- [Task 2] depends on [Task 1]
- [Task 3] 可以与 [Task 1, Task 2] 并行开发
- [Task 4] depends on [Task 1, Task 2]
- [Task 5] 可以与 [Task 1, Task 2, Task 3] 并行开发
- [Task 6] 可以与 [Task 2] 并行开发
- [Task 7] depends on [Task 1, Task 2, Task 3, Task 4, Task 5, Task 6]

# 关键设计决策

1. **链式生成保证连续性**：第一个片段文生视频，后续片段使用前一帧图生视频
2. **复用现有能力**：复用 PlatformManager 的文生视频和图生视频能力
3. **渐进式生成**：逐个生成片段，避免内存溢出
4. **容错机制**：片段生成失败时跳过，保证最终输出
5. **降级方案**：无图生视频平台时，使用统一提示词生成
6. **进度反馈**：实时显示生成进度，提升用户体验
7. **临时文件管理**：自动清理临时文件，支持失败恢复
8. **平台智能选择**：根据片段类型自动选择文生视频或图生视频平台
9. **可扩展架构**：支持未来添加转场效果、并行生成等高级功能

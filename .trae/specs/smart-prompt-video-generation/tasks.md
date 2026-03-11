# Tasks

## Phase 1: 提示词知识服务

- [ ] Task 1: 创建 PromptKnowledgeService 提示词知识服务
  - [ ] SubTask 1.1: 创建 `src/prompt_knowledge_service.py`
  - [ ] SubTask 1.2: 实现 `fetch_image_prompt_knowledge()` 从网络获取图片提示词知识
  - [ ] SubTask 1.3: 实现 `fetch_video_prompt_knowledge()` 从网络获取视频提示词知识
  - [ ] SubTask 1.4: 实现知识缓存机制（JSON文件缓存）
  - [ ] SubTask 1.5: 实现 `build_image_prompt_from_template()` 基于模板生成图片提示词
  - [ ] SubTask 1.6: 实现 `build_video_prompt_from_template()` 基于模板生成视频提示词
  - [ ] SubTask 1.7: 内置图片提示词知识库（分层结构、构图术语、光影描述等）
  - [ ] SubTask 1.8: 内置视频提示词知识库（七层结构、运镜术语、光影描述等）

## Phase 2: 场景规划器

- [ ] Task 2: 创建 ScenePlanner 场景规划器
  - [ ] SubTask 2.1: 创建 `src/scene_planner.py`
  - [ ] SubTask 2.2: 实现 `plan_for_images()` 图片场景规划方法
  - [ ] SubTask 2.3: 实现 `plan_for_video()` 视频场景规划方法
  - [ ] SubTask 2.4: 实现 `_call_llm_for_image_planning()` 调用 LLM 进行图片场景分解
  - [ ] SubTask 2.5: 实现 `_call_llm_for_video_planning()` 调用 LLM 进行视频场景分解
  - [ ] SubTask 2.6: 实现场景连贯性检查和优化
  - [ ] SubTask 2.7: 实现智能输出类型判断逻辑

## Phase 3: 提示词增强扩展

- [ ] Task 3: 扩展 EnhanceService 支持图片和视频提示词
  - [ ] SubTask 3.1: 添加图片提示词增强模式（分层结构）
  - [ ] SubTask 3.2: 添加视频提示词增强模式（七层结构）
  - [ ] SubTask 3.3: 实现摄影术语自动添加（图片模式）
  - [ ] SubTask 3.4: 实现运镜术语自动添加（视频模式）
  - [ ] SubTask 3.5: 实现感觉词自动添加
  - [ ] SubTask 3.6: 添加 `enhance_image_prompt()` 方法
  - [ ] SubTask 3.7: 添加 `enhance_video_prompt()` 方法

## Phase 4: 系列图片生成器

- [ ] Task 4: 创建 ImageSeriesGenerator 系列图片生成器
  - [ ] SubTask 4.1: 创建 `src/image_series_generator.py`
  - [ ] SubTask 4.2: 实现 `generate_from_topic()` 方法
  - [ ] SubTask 4.3: 集成 ScenePlanner 进行场景规划
  - [ ] SubTask 4.4: 实现系列图片命名规则（主题_序号_场景名）
  - [ ] SubTask 4.5: 实现图片生成进度显示

## Phase 5: 长视频生成器扩展

- [ ] Task 5: 扩展 LongVideoGenerator 支持主题驱动
  - [ ] SubTask 5.1: 实现 `generate_from_topic()` 方法
  - [ ] SubTask 5.2: 集成 ScenePlanner 进行场景规划
  - [ ] SubTask 5.3: 实现场景进度显示（当前场景/总场景）
  - [ ] SubTask 5.4: 处理场景规划失败的情况

## Phase 6: 命令行扩展

- [ ] Task 6: 扩展 main.py 命令行参数
  - [ ] SubTask 6.1: 添加 `--topic` 参数（主题模式开关）
  - [ ] SubTask 6.2: 添加 `--count` 参数（图片数量）
  - [ ] SubTask 6.3: 添加 `--style` 参数（内容风格选择）
  - [ ] SubTask 6.4: 实现参数组合逻辑判断
  - [ ] SubTask 6.5: 实现主题模式的完整流程入口（图片和视频）
  - [ ] SubTask 6.6: 复用现有 RouteService 进行平台选择

## Phase 7: 配置更新

- [ ] Task 7: 更新配置文件
  - [ ] SubTask 7.1: config.json 添加 `scene_planner` 配置节
  - [ ] SubTask 7.2: config.json 添加 `prompt_knowledge` 配置节
  - [ ] SubTask 7.3: config.json 添加 `image_prompt_templates` 配置节
  - [ ] SubTask 7.4: config.json 添加 `video_prompt_templates` 配置节

## Phase 8: 测试

- [ ] Task 8: 编写测试
  - [ ] SubTask 8.1: PromptKnowledgeService 单元测试（图片和视频知识获取）
  - [ ] SubTask 8.2: ScenePlanner 单元测试（图片和视频场景规划，Mock LLM 响应）
  - [ ] SubTask 8.3: 图片提示词增强测试
  - [ ] SubTask 8.4: 视频提示词增强测试
  - [ ] SubTask 8.5: ImageSeriesGenerator 单元测试
  - [ ] SubTask 8.6: 集成测试（主题驱动的系列图片生成）
  - [ ] SubTask 8.7: 集成测试（主题驱动的长视频生成）

# Task Dependencies

- [Task 2] depends on [Task 1]
- [Task 3] 可以与 [Task 1, Task 2] 并行开发
- [Task 4] depends on [Task 1, Task 2, Task 3]
- [Task 5] depends on [Task 1, Task 2, Task 3]
- [Task 6] depends on [Task 4, Task 5]
- [Task 7] 可以与 [Task 1, Task 2, Task 3] 并行开发
- [Task 8] depends on [Task 1, Task 2, Task 3, Task 4, Task 5, Task 6, Task 7]

# 关键设计决策

1. **双模式支持**：同时支持图片和视频两种输出形式，通过参数组合选择
2. **内置知识库优先**：优先使用内置的提示词知识库，网络获取作为补充
3. **LLM 驱动规划**：场景分片完全由 LLM 决定，保证创意性和灵活性
4. **模板化提示词**：使用模板生成结构化提示词，保证质量和一致性
5. **渐进式生成**：逐场景生成，避免内存溢出
6. **向后兼容**：不破坏现有的提示词文件模式和统一提示词模式
7. **风格可配置**：支持电影感、纪录片、Vlog、摄影、数字艺术等多种风格
8. **缓存机制**：知识库缓存减少网络请求，提升响应速度
9. **复用现有组件**：复用 RouteService 进行平台选择，避免重复实现
10. **参数语义一致**：`prompt` 始终是必需参数，`--topic` 改变其解释方式

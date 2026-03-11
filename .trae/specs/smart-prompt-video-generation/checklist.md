# Checklist

## 1. PromptKnowledgeService 验收

- [ ] `PromptKnowledgeService` 类正确初始化
- [ ] `fetch_image_prompt_knowledge()` 能从网络获取图片提示词知识
- [ ] `fetch_video_prompt_knowledge()` 能从网络获取视频提示词知识
- [ ] 知识缓存机制正常工作（写入和读取）
- [ ] `build_image_prompt_from_template()` 能生成结构化图片提示词
- [ ] `build_video_prompt_from_template()` 能生成结构化视频提示词
- [ ] 内置图片知识库包含分层结构、构图术语、光影描述等
- [ ] 内置视频知识库包含七层结构、运镜术语、光影描述等
- [ ] 缓存过期机制正常工作

## 2. ScenePlanner 验收

- [ ] `ScenePlanner` 类正确初始化
- [ ] `plan_for_images()` 能将主题分解为图片场景
- [ ] `plan_for_video()` 能将主题分解为视频场景
- [ ] 图片场景数量与目标数量匹配
- [ ] 视频场景片段数与目标时长匹配
- [ ] 每个图片场景包含标题、描述、构图、光影、风格等信息
- [ ] 每个视频场景包含标题、描述、运镜、光影、情绪等信息
- [ ] `_call_llm_for_image_planning()` 能正确调用 LLM
- [ ] `_call_llm_for_video_planning()` 能正确调用 LLM
- [ ] 场景之间保持叙事连贯性
- [ ] 返回的规划结果格式正确（JSON结构）

## 3. 图片提示词增强验收

- [ ] `enhance_image_prompt()` 方法正常工作
- [ ] 生成的图片提示词包含分层结构
- [ ] 摄影术语正确添加
- [ ] 风格词正确添加
- [ ] 支持不同风格的图片提示词模板

## 4. 视频提示词增强验收

- [ ] `enhance_video_prompt()` 方法正常工作
- [ ] 生成的视频提示词包含七层结构
- [ ] 运镜术语正确添加
- [ ] 感觉词正确添加
- [ ] 负向约束正确添加
- [ ] 支持不同风格的视频提示词模板

## 5. ImageSeriesGenerator 验收

- [ ] `ImageSeriesGenerator` 类正确初始化
- [ ] `generate_from_topic()` 方法正常工作
- [ ] 能正确调用 ScenePlanner 进行规划
- [ ] 能根据规划结果生成图片
- [ ] 系列图片命名正确（主题_序号_场景名）
- [ ] 图片生成进度显示正确

## 6. LongVideoGenerator 扩展验收

- [ ] `generate_from_topic()` 方法正常工作
- [ ] 能正确调用 ScenePlanner 进行规划
- [ ] 能根据规划结果生成视频片段
- [ ] 场景进度显示正确（当前场景/总场景）
- [ ] 场景规划失败时能正确处理
- [ ] 最终视频时长接近目标时长

## 7. 命令行参数验收

- [ ] `--topic` 参数正确传递
- [ ] `--count` 参数正确传递
- [ ] `--style` 参数正确传递
- [ ] `prompt` + `--topic` 组合触发主题模式
- [ ] `prompt` + `--topic` + `--count` 组合触发系列图片模式
- [ ] `prompt` + `--topic` + `--duration` 组合触发长视频模式
- [ ] 不使用 `--topic` 时保持原有行为
- [ ] 帮助信息正确显示新参数

## 8. 配置文件验收

- [ ] config.json 包含 `scene_planner` 配置节
- [ ] config.json 包含 `prompt_knowledge` 配置节
- [ ] config.json 包含 `image_prompt_templates` 配置节
- [ ] config.json 包含 `video_prompt_templates` 配置节
- [ ] 默认配置值合理

## 9. 智能输出类型判断验收

- [ ] 动态场景主题（如"奔跑"）自动判断为视频
- [ ] 静态场景主题（如"风景"）自动判断为图片
- [ ] `--count` 参数明确指定图片模式
- [ ] `--duration` 参数明确指定视频模式
- [ ] 主题模式正确复用 RouteService 进行平台选择

## 10. 端到端验收

### 图片模式
- [ ] 运行 `python main.py "四季变化" --topic --count 4` 能生成4张系列图片
- [ ] 生成的图片文件名包含主题和场景序号
- [ ] 控制台显示完整的生成流程

### 视频模式
- [ ] 运行 `python main.py "海边日落" --topic --duration 1` 能生成约1分钟的视频
- [ ] 生成的视频场景连贯
- [ ] 控制台显示完整的生成流程

### 智能判断模式
- [ ] 运行 `python main.py "一只猫在奔跑" --topic` 自动判断为视频并生成
- [ ] 运行 `python main.py "美丽的风景" --topic` 自动判断为图片并生成

### 向后兼容测试
- [ ] 运行 `python main.py "一只猫"` 正常生成单张图片（现有模式）
- [ ] 运行 `python main.py "一只猫在奔跑" --duration 1` 正常生成长视频（现有模式）

## 11. 风格模板验收

### 图片风格
- [ ] `photography` 风格模板正常工作
- [ ] `digital_art` 风格模板正常工作
- [ ] 不同风格生成的图片提示词有明显差异

### 视频风格
- [ ] `cinematic` 风格模板正常工作
- [ ] `documentary` 风格模板正常工作
- [ ] `vlog` 风格模板正常工作
- [ ] 不同风格生成的视频提示词有明显差异

## 12. 向后兼容性验收

- [ ] 不使用 `--topic` 参数时，原有图片/视频生成功能正常
- [ ] 使用 `--duration` 但不使用 `--topic` 时，统一提示词模式正常
- [ ] 使用 `--prompts-file` 时，提示词文件模式正常
- [ ] 原有命令行参数仍然有效

## 13. 错误处理验收

- [ ] LLM 调用失败时有合理的错误提示
- [ ] 网络获取知识失败时使用内置知识库
- [ ] 场景规划结果无效时能正确处理
- [ ] 部分场景生成失败时能继续执行
- [ ] 无可用平台时有明确的错误提示

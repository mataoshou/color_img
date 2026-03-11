# Tasks

## Phase 1: 核心扩展

- [x] Task 1: 扩展 ServiceClient
  - [x] 添加 `result_url_path` 属性（向后兼容 `image_url_path`）
  - [x] 添加 `async_config` 配置读取（task_id_path, status_url, status_path, status_complete_value, result_url_path, poll_interval, max_poll_time）
  - [x] 修改 `request()` 方法，根据 `is_async` 选择同步或异步模式
  - [x] 实现 `_request_async()` 异步轮询方法
  - [x] 复用现有 `_download_image()` 下载视频（不区分图片/视频）

- [x] Task 2: 创建 RouteService 智能路由
  - [x] 创建 `src/route_service.py`
  - [x] 复用 EnhanceService 的配置和 LLM 调用逻辑
  - [x] 实现 `select_platform()` 方法（返回平台配置+保存类型+后续步骤）
  - [x] 实现 `select_i2v_platform()` 方法（选择图生视频平台）

## Phase 2: 视频保存

- [x] Task 3: 创建 VideoSaver
  - [x] 创建 `src/video_saver.py`
  - [x] 复用 ImageSaver 的目录创建、命名、冲突解决逻辑
  - [x] 实现 `save_video()` 方法
  - [x] 实现 `_detect_video_format()` 方法（MP4, WebM）

## Phase 3: 主程序扩展

- [x] Task 4: 扩展 main.py 和 PlatformManager
  - [x] PlatformManager.generate() 支持 `image_url` 参数
  - [x] 调用 RouteService.select_platform() 获取平台和保存类型
  - [x] 根据大模型返回的 save_type 选择保存器
  - [x] 处理 next_step="image-to-video" 流程

## Phase 4: 配置更新

- [x] Task 5: 更新配置文件
  - [x] config.json 在 platforms 中添加文生视频平台
  - [x] config.json 在 platforms 中添加图生视频平台
  - [x] .env.example 添加视频平台API密钥示例

## Phase 5: 测试

- [x] Task 6: 编写测试
  - [x] RouteService 平台选择测试
  - [x] RouteService 图生视频流程测试
  - [x] ServiceClient 异步轮询测试
  - [x] ServiceClient async_config 配置测试
  - [x] VideoSaver 测试
  - [x] 集成测试

# Task Dependencies

- [Task 2] 可以与 [Task 1] 并行开发
- [Task 3] 可以与 [Task 1, Task 2] 并行开发
- [Task 4] depends on [Task 1, Task 2, Task 3]
- [Task 5] 可以与 [Task 1, Task 2, Task 3] 并行开发
- [Task 6] depends on [Task 4, Task 5]

# 关键设计决策

1. **大模型完全控制**：选择平台 + 返回保存类型 + 决定是否需要后续流程
2. **一次大模型调用**：返回所有决策信息
3. **系统只执行**：根据大模型返回执行，不做判断
4. **支持多步流程**：文本→图片→视频
5. **复用 PlatformManager**：直接传入选中的平台
6. **复用 ServiceClient**：扩展 is_async 逻辑
7. **向后兼容**：result_url_path 兼容 image_url_path

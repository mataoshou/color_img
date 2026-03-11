# Tasks

- [x] Task 1: 项目初始化与基础结构
  - [x] 创建项目目录结构
  - [x] 创建 requirements.txt 或 pyproject.toml
  - [x] 创建主入口文件 main.py
  - [x] 创建 .env.example 文件（环境变量示例）

- [x] Task 2: 实现核心配置模块
  - [x] 创建配置管理模块 config.py
  - [x] 定义默认配置值（图片生成平台、增强服务、切换策略、保存路径、图片尺寸、日志级别等）
  - [x] 定义图片生成平台配置结构（api_url、request_method、request_params、request_headers、request_body、auth_type等）
  - [x] 定义增强服务配置结构（model、api_url、api_key_env、system_prompt）
  - [x] 定义图片保存路径配置
  - [x] 定义文件命名规则配置（timestamp、sequential、prompt）
  - [x] 定义平台切换策略配置（重试次数、重试间隔、超时时间等）
  - [x] 定义图片尺寸配置（默认宽高）
  - [x] 实现配置文件读取和写入功能
  - [x] 实现默认配置生成功能（首次运行自动创建配置文件）
  - [x] 实现 .env 文件加载功能

- [x] Task 3: 实现日志模块
  - [x] 创建日志模块 logger.py
  - [x] 实现日志级别配置
  - [x] 实现控制台日志输出
  - [x] 实现文件日志输出（可选）
  - [x] 实现进度信息输出

- [x] Task 4: 实现通用服务调用模块
  - [x] 创建服务调用器 service_client.py
  - [x] 实现基于配置的API请求构建功能
  - [x] 实现参数模板替换功能（{prompt}、{model}、{api_key}、{width}、{height}等）
  - [x] 实现多种认证方式支持（none、api_key、bearer）
  - [x] 实现多种响应类型处理（binary、image_url、json）
  - [x] 实现错误处理和降级逻辑
  - [x] 实现重试逻辑（支持重试间隔）

- [x] Task 5: 实现OpenAI兼容的增强服务模块
  - [x] 创建增强服务模块 enhance_service.py
  - [x] 实现OpenAI API调用逻辑
  - [x] 实现系统提示词管理
  - [x] 实现服务不可用时的降级处理

- [x] Task 6: 实现配置驱动的图片生成模块
  - [x] 创建平台管理器 platform_manager.py
  - [x] 实现平台切换逻辑（基于配置的平台列表）
  - [x] 实现平台重试逻辑（基于配置的重试次数和间隔）
  - [x] 集成通用服务调用模块处理API请求

- [x] Task 7: 实现图片保存功能
  - [x] 创建图片保存模块 image_saver.py
  - [x] 实现图片下载功能
  - [x] 实现输出目录自动创建
  - [x] 实现文件命名规则（timestamp、sequential、prompt）
  - [x] 实现文件名冲突处理（自动添加序号后缀）

- [x] Task 8: 实现主程序逻辑
  - [x] 整合所有模块
  - [x] 实现命令行参数解析（只需描述文字参数）
  - [x] 实现完整工作流：输入 -> 增强处理（翻译、优化） -> 生成 -> 保存
  - [x] 实现进度信息输出
  - [x] 实现错误信息输出

- [x] Task 9: 编写测试
  - [x] 编写通用服务调用模块单元测试
  - [x] 编写平台管理器单元测试
  - [x] 编写配置模块单元测试
  - [x] 编写图片保存模块单元测试
  - [x] 编写集成测试

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 1]
- [Task 5] depends on [Task 2, Task 4]
- [Task 6] depends on [Task 2, Task 4]
- [Task 7] depends on [Task 1]
- [Task 8] depends on [Task 2, Task 3, Task 4, Task 5, Task 6, Task 7]
- [Task 9] depends on [Task 8]
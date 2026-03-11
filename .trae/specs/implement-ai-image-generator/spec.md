# AI图片生成系统 Spec

## Why
用户需要一个简单易用的AI图片生成工具，能够通过文字描述自动生成图片，支持中文输入、提示词增强和多平台自动切换，且无需复杂配置即可使用。

## What Changes
- 创建命令行AI图片生成工具
- 实现多平台图片生成支持（配置驱动，支持添加新平台）
- 实现OpenAI兼容的提示词增强服务（翻译、优化）
- 实现平台自动切换和重试机制
- 实现图片保存功能（支持多种命名规则）
- 实现配置系统（JSON配置文件 + 环境变量）

## Impact
- 新增项目：Python命令行工具
- 核心模块：配置管理、服务调用、平台管理、图片保存、日志
- 配置文件：config.json、.env

## ADDED Requirements

### Requirement: 文字描述输入
系统SHALL接收用户输入的文字描述作为命令行参数。

#### Scenario: 基本输入
- **WHEN** 用户运行 `python main.py "一只猫"`
- **THEN** 系统接收描述并开始处理

#### Scenario: 英文输入
- **WHEN** 用户运行 `python main.py "a cute cat"`
- **THEN** 系统接收描述并开始处理

### Requirement: 提示词增强服务
系统SHALL支持可选的提示词增强功能，将简单描述扩展为详细提示词。

#### Scenario: 增强服务启用
- **GIVEN** 配置中启用了增强服务且配置了API密钥
- **WHEN** 用户输入描述
- **THEN** 系统调用GLM API进行翻译和优化
- **AND** 使用增强后的提示词生成图片

#### Scenario: 增强服务禁用
- **GIVEN** 配置中禁用了增强服务
- **WHEN** 用户输入描述
- **THEN** 系统直接使用原始描述生成图片

#### Scenario: 增强服务降级
- **GIVEN** 增强服务启用但不可用
- **WHEN** 用户输入描述
- **THEN** 系统降级使用原始描述生成图片
- **AND** 输出警告信息

### Requirement: 多平台图片生成
系统SHALL支持多个图片生成平台，并能自动切换。

#### Scenario: 默认平台可用
- **GIVEN** 默认配置的平台可用
- **WHEN** 用户请求生成图片
- **THEN** 系统使用默认平台生成图片

#### Scenario: 平台自动切换
- **GIVEN** 当前平台失败
- **WHEN** 达到重试次数上限
- **THEN** 系统自动切换到下一个平台

#### Scenario: 所有平台失败
- **GIVEN** 所有平台都失败
- **WHEN** 用户请求生成图片
- **THEN** 系统返回友好的错误信息

### Requirement: 配置驱动架构
系统SHALL通过配置文件驱动，支持添加新平台无需修改代码。

#### Scenario: 首次运行
- **WHEN** 用户首次运行程序
- **THEN** 系统自动创建默认配置文件 config.json
- **AND** 系统自动创建 .env.example 文件

#### Scenario: 添加新平台
- **GIVEN** 用户在配置文件中添加新平台配置
- **WHEN** 用户运行程序
- **THEN** 系统能够使用新平台生成图片

#### Scenario: 配置修改生效
- **GIVEN** 用户修改了配置文件
- **WHEN** 用户重新运行程序
- **THEN** 新配置生效

### Requirement: 图片保存
系统SHALL将生成的图片保存到本地。

#### Scenario: 保存成功
- **WHEN** 图片生成成功
- **THEN** 图片保存到配置的目录
- **AND** 文件名符合配置的命名规则

#### Scenario: 目录不存在
- **GIVEN** 输出目录不存在
- **WHEN** 图片生成成功
- **THEN** 系统自动创建目录并保存图片

#### Scenario: 文件名冲突
- **GIVEN** 目标文件名已存在
- **WHEN** 保存图片
- **THEN** 系统自动添加序号后缀

### Requirement: 日志与进度
系统SHALL提供清晰的进度信息和错误提示。

#### Scenario: 正常流程
- **WHEN** 系统处理请求
- **THEN** 输出进度信息（增强处理、生成中、保存中）

#### Scenario: 错误处理
- **WHEN** 发生错误
- **THEN** 输出友好的错误信息
- **AND** 不输出敏感信息（如API密钥）

## Configuration Structure

### config.json 结构
```json
{
  "platforms": [
    {
      "name": "平台名称",
      "api_url": "API地址",
      "request_method": "GET|POST",
      "request_params": {},
      "request_headers": {},
      "request_body": {},
      "auth_type": "none|api_key|bearer",
      "response_type": "binary|image_url|json",
      "image_url_path": "响应中图片URL的JSON路径"
    }
  ],
  "enhance_service": {
    "enabled": true,
    "model": "glm-4-flash",
    "api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    "api_key_env": "GLM_API_KEY",
    "system_prompt": "系统提示词"
  },
  "output": {
    "directory": "./output",
    "naming": "timestamp|sequential|prompt"
  },
  "image": {
    "width": 512,
    "height": 512
  },
  "retry": {
    "max_retries": 3,
    "retry_interval": 1,
    "timeout": 30
  },
  "logging": {
    "level": "INFO",
    "file": null
  }
}
```

### .env 文件结构
```
GLM_API_KEY=your_api_key_here
```

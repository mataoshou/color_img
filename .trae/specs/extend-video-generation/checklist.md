# Checklist

## 1. RouteService 大模型控制验收

* [x] `RouteService.select_platform()` 能正确解析提示词并返回决策

* [x] 返回格式为 `{"platform": 平台配置, "save_type": "image或video", "next_step": "image-to-video或null"}`

* [x] 大模型能根据提示词内容判断应该选择的平台

* [x] 大模型能根据提示词内容判断是否需要图生视频流程

* [x] `RouteService.select_i2v_platform()` 能正确选择图生视频平台

* [x] 复用 EnhanceService 的 LLM 调用逻辑

## 2. ServiceClient 扩展验收

* [x] `result_url_path` 属性正确读取，向后兼容 `image_url_path`

* [x] `async_config` 配置正确读取（task\_id\_path, status\_url, status\_path, status\_complete\_value, result\_url\_path, poll\_interval, max\_poll\_time）

* [x] `is_async=True` 时，`request()` 方法调用 `_request_async()` 而非同步逻辑

* [x] `_request_async()` 方法存在且可调用

* [x] 异步请求返回 `(True, bytes_data, None)` 表示成功

* [x] 异步请求返回 `(False, None, error_message)` 表示失败

* [x] 超时时返回错误信息包含 "超时" 字样

* [x] `_download_image()` 可用于下载视频（不区分图片/视频）

## 3. PlatformManager 扩展验收

* [x] `image_url` 等模板变量通过现有 `**kwargs` 正确传递并替换

## 4. VideoSaver 验收

* [x] `save_video(b'\x00\x00\x00\x1c...', "test")` 返回文件路径字符串

* [x] 返回的文件路径存在且文件大小 > 0

* [x] MP4 格式检测：`_detect_video_format(b'\x00\x00\x00\x1c...')` 返回 `.mp4`

* [x] WebM 格式检测：`_detect_video_format(b'\x1a\x45\xdf\xa3...')` 返回 `.webm`

* [x] 未知格式默认返回 `.mp4`

* [x] 文件名包含时间戳

* [x] 文件名冲突时自动添加 `_1`, `_2` 等后缀

## 5. main.py 扩展验收

* [x] 调用 `RouteService.select_platform()` 获取平台和保存类型

* [x] 根据大模型返回的 `save_type` 选择保存器（无系统判断）

* [x] 处理 `next_step="image-to-video"` 流程：先生成图片，再调用图生视频平台

* [x] 图片生成成功后打印 "图片已保存到: {path}"

* [x] 视频生成成功后打印 "视频已保存到: {path}"

## 6. 配置文件验收

* [x] config.json 的 platforms 包含图片平台（有 description）

* [x] config.json 的 platforms 包含文生视频平台（有 description）

* [x] config.json 的 platforms 包含图生视频平台（有 description）

* [x] .env.example 包含 `GLM_API_KEY=` 示例

* [x] .env.example 包含 `ALIYUN_API_KEY=` 示例

## 7. 端到端验收

* [x] 运行 `python main.py "一只猫"` 时，output 目录生成图片文件（静态场景）

* [x] 运行 `python main.py "一只猫在奔跑"` 时，output 目录生成视频文件（动态场景，直接生成）

* [ ] 运行 `python main.py "鸟儿飞翔"` 时，output 目录生成视频文件（动态场景，直接生成）

* [ ] 运行 `python main.py "生成一只猫的图片，然后让它动起来"` 时，output 目录同时生成图片和视频文件（两步流程：先生成图片，再图生视频）

## 8. 向后兼容性验收

* [x] 不修改 config.json 时，原有图片生成功能正常

* [x] 原有命令行参数 `--prompt`, `--output` 仍然有效

* [x] 原有日志输出格式不变

import argparse
import sys
from pathlib import Path
from typing import Optional

from src.config import get_config_manager, get_env
from src.logger import setup_logger, get_logger
from src.enhance_service import EnhanceService
from src.platform_manager import PlatformManager
from src.image_saver import ImageSaver
from src.route_service import RouteService
from src.video_saver import VideoSaver
from src.video_composer import VideoComposer
from src.long_video_generator import LongVideoGenerator


def parse_args():
    parser = argparse.ArgumentParser(
        description='AI Image Generator - 智能图片生成工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python main.py "一只猫"
  python main.py "a cute cat" --width 512 --height 512
  python main.py "一只猫" --output ./my_images
  python main.py "一只猫" --no-enhance
  python main.py "一只猫在奔跑" --duration 2
  python main.py "风景变化" --prompts-file prompts.txt
        '''
    )
    parser.add_argument(
        'prompt',
        type=str,
        help='图片生成的提示词（描述文字）'
    )
    parser.add_argument(
        '--width', '-W',
        type=int,
        default=None,
        help='图片宽度（默认使用配置文件中的值）'
    )
    parser.add_argument(
        '--height', '-H',
        type=int,
        default=None,
        help='图片高度（默认使用配置文件中的值）'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='输出目录（默认使用配置文件中的值）'
    )
    parser.add_argument(
        '--no-enhance',
        action='store_true',
        help='禁用提示词增强服务'
    )
    parser.add_argument(
        '--duration', '-d',
        type=float,
        default=None,
        help='目标视频时长（分钟），启用长视频生成模式'
    )
    parser.add_argument(
        '--segment-duration',
        type=float,
        default=None,
        help='每个片段时长（秒），默认使用配置值'
    )
    parser.add_argument(
        '--prompts-file',
        type=str,
        default=None,
        help='提示词文件路径，每行一个提示词，用于分段生成'
    )
    return parser.parse_args()


def ensure_env_example_exists() -> bool:
    env_example_path = Path(".env.example")
    if not env_example_path.exists():
        env_example_content = """GLM_API_KEY=your_api_key_here
"""
        with open(env_example_path, 'w', encoding='utf-8') as f:
            f.write(env_example_content)
        return True
    return False


def check_first_run(config_manager) -> bool:
    config_path = config_manager.get_config_path()
    if config_path is None or not config_path.exists():
        return True
    return False


def print_first_run_info() -> None:
    print("\n" + "=" * 50)
    print("欢迎使用 AI 内容生成器!")
    print("=" * 50)
    print("\n首次运行，已自动创建配置文件:")
    print("  - config.json    配置文件")
    print("  - .env.example   环境变量示例")
    print("\n如需使用提示词增强和智能路由功能，请:")
    print("  1. 复制 .env.example 为 .env")
    print("  2. 在 .env 中填入你的 GLM_API_KEY")
    print("\n功能说明:")
    print("  - 智能路由：自动判断生成图片还是视频")
    print("  - 图片生成：静态场景（如'一只猫'）")
    print("  - 视频生成：动态场景（如'一只猫在奔跑'）")
    print("  - 图生视频：先生成图片再转为视频")
    print("\n" + "=" * 50 + "\n")


def main():
    args = parse_args()
    
    config_manager = get_config_manager()
    is_first_run = check_first_run(config_manager)
    
    config_path = config_manager.ensure_config_exists()
    config = config_manager.load_config()
    
    env_example_created = ensure_env_example_exists()
    
    logging_config = config_manager.get_logging_config()
    setup_logger(
        level=logging_config.get("level", "INFO"),
        log_file=logging_config.get("log_file") if logging_config.get("file_output") else None,
        console_output=logging_config.get("console_output", True),
        log_format=logging_config.get("log_format")
    )
    logger = get_logger()
    
    if is_first_run or env_example_created:
        print_first_run_info()
    
    try:
        prompt = args.prompt
        
        if args.duration or args.prompts_file:
            logger.info("进入长视频生成模式")
            print("正在初始化长视频生成器...")
            
            video_composer = VideoComposer(config)
            long_video_generator = LongVideoGenerator(
                config=config,
                platform_manager=PlatformManager(config),
                route_service=RouteService(config),
                video_composer=video_composer
            )
            
            final_path = long_video_generator.generate(
                prompt=prompt,
                duration_minutes=args.duration,
                prompts_file=args.prompts_file
            )
            
            logger.info(f"长视频生成完成: {final_path}")
            return
        
        if args.no_enhance:
            logger.info("增强服务已禁用")
            enhanced_prompt = prompt
        else:
            print("正在处理提示词...")
            enhance_config = config_manager.get_enhance_service_config()
            enhance_service = EnhanceService(enhance_config)
            
            if enhance_service.is_available():
                enhanced_prompt = enhance_service.enhance(prompt)
                if enhanced_prompt != prompt:
                    logger.info(f"提示词已增强: {prompt} -> {enhanced_prompt}")
                else:
                    logger.info("使用原始提示词")
            else:
                logger.warning("增强服务不可用（未配置API密钥），使用原始提示词")
                enhanced_prompt = prompt
        
        output_config = config_manager.get_output_config()
        output_dir = args.output or output_config.get("directory", "output")
        saver_config = {"output": output_config.copy()}
        saver_config["output"]["directory"] = output_dir
        
        image_config = config_manager.get_image_config()
        width = args.width or image_config.get("default_width", 1024)
        height = args.height or image_config.get("default_height", 1024)
        
        route_service = RouteService(config)
        platform_manager = PlatformManager(config)
        
        platforms = config.get("platforms", [])
        i2v_platforms = [p for p in platforms if "图生视频" in p.get("description", "")]
        
        if route_service.is_available() and platforms:
            logger.info("开始智能路由分析...")
            print("正在智能路由...")
            route_result = route_service.select_platform(enhanced_prompt, platforms)
            
            platform_config = route_result.get("platform", {})
            save_type = route_result.get("save_type", "image")
            next_step = route_result.get("next_step")
            
            logger.info(f"智能路由结果: 平台={platform_config.get('name')}, 类型={save_type}, 后续步骤={next_step}")
            
            if next_step == "image-to-video":
                save_type = "image"
                logger.info("检测到图生视频流程，先生成图片")
            
            if not platform_config:
                logger.error("未找到可用平台")
                print("错误: 未找到可用平台")
                sys.exit(1)
            
            logger.info(f"开始生成{save_type}，使用平台: {platform_config.get('name')}")
            print(f"正在生成{save_type}...")
            
            success, data, error = platform_manager.generate_with_platform(
                platform_config=platform_config,
                prompt=enhanced_prompt,
                width=width,
                height=height
            )
            
            if not success:
                logger.error(f"平台 {platform_config.get('name')} 生成失败: {error}")
                if "未配置API密钥" in str(error) or "跳过" in str(error):
                    logger.warning(f"智能路由选择的平台不可用: {error}，尝试其他平台...")
                    success, data, error = platform_manager.generate(
                        prompt=enhanced_prompt,
                        width=width,
                        height=height
                    )
                
                if not success:
                    logger.error(f"所有平台均失败: {error}")
                    print(f"错误: 内容生成失败 - {error}")
                    sys.exit(1)
            
            logger.info(f"平台 {platform_config.get('name')} 生成成功")
            
            if save_type == "image":
                logger.info(f"开始保存图片到: {output_dir}")
                image_saver = ImageSaver(saver_config)
                saved_path = image_saver.save_image(
                    image_data=data,
                    prompt=enhanced_prompt,
                    format=image_config.get("default_format", "png")
                )
                logger.info(f"图片已保存: {saved_path}")
                print(f"图片已保存到: {saved_path}")
                
                if next_step == "image-to-video" and i2v_platforms:
                    print("正在生成视频...")
                    
                    import base64
                    with open(saved_path, 'rb') as f:
                        image_base64 = base64.b64encode(f.read()).decode('utf-8')
                    image_url_data = f"data:image/png;base64,{image_base64}"
                    
                    i2v_result = route_service.select_i2v_platform(enhanced_prompt, saved_path, i2v_platforms)
                    i2v_platform_config = i2v_result.get("platform", {})
                    
                    if i2v_platform_config:
                        success, video_data, error = platform_manager.generate_with_platform(
                            platform_config=i2v_platform_config,
                            prompt=enhanced_prompt,
                            image_url=image_url_data
                        )
                        
                        if not success:
                            print(f"警告: 视频生成失败 - {error}")
                        else:
                            video_saver = VideoSaver(saver_config)
                            video_path = video_saver.save_video(
                                video_data=video_data,
                                prompt=enhanced_prompt
                            )
                            print(f"视频已保存到: {video_path}")
                    else:
                        print("警告: 未找到可用的图生视频平台")
            else:
                video_saver = VideoSaver(saver_config)
                video_path = video_saver.save_video(
                    video_data=data,
                    prompt=enhanced_prompt
                )
                print(f"视频已保存到: {video_path}")
            
            logger.info(f"生成完成 - 平台: {platform_config.get('name')}, 尺寸: {width}x{height}")
        else:
            print("正在生成图片...")
            
            success, image_data, error = platform_manager.generate(
                prompt=enhanced_prompt,
                width=width,
                height=height
            )
            
            if not success:
                print(f"错误: 图片生成失败 - {error}")
                sys.exit(1)
            
            print("正在保存图片...")
            
            image_saver = ImageSaver(saver_config)
            
            saved_path = image_saver.save_image(
                image_data=image_data,
                prompt=enhanced_prompt,
                format=image_config.get("default_format", "png")
            )
            
            print(f"图片已保存到: {saved_path}")
            
            logger.info(f"生成完成 - 平台: {platform_manager.get_current_platform()}, 尺寸: {width}x{height}")
        
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(130)
    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg or "token" in error_msg.lower():
            print("错误: API配置无效，请检查环境变量配置")
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            print("错误: 网络连接失败，请检查网络设置")
        else:
            print(f"错误: {error_msg}")
        logger.debug(f"详细错误信息: {error_msg}")
        sys.exit(1)


if __name__ == '__main__':
    main()

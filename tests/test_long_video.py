import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from src.video_composer import VideoComposer
from src.long_video_generator import LongVideoGenerator


class TestVideoComposer:
    """VideoComposer 单元测试"""

    def test_video_composer_init(self):
        """测试 VideoComposer 初始化"""
        config = {
            "long_video": {
                "temp_directory": "output/temp",
                "output_format": "mp4",
                "output_resolution": "1080p"
            }
        }
        composer = VideoComposer(config)
        
        assert composer.temp_directory == "output/temp"
        assert composer.output_format == "mp4"
        assert composer.output_resolution == "1080p"

    def test_video_composer_init_default(self):
        """测试 VideoComposer 默认初始化"""
        config = {}
        composer = VideoComposer(config)
        
        assert composer.temp_directory == "output/temp"
        assert composer.output_format == "mp4"
        assert composer.output_resolution == "1080p"

    def test_resolution_mapping(self):
        """测试分辨率映射"""
        config = {"long_video": {"output_resolution": "720p"}}
        composer = VideoComposer(config)
        
        target_res = composer._get_target_resolution()
        assert target_res == (1280, 720)

    def test_get_video_info_file_not_found(self):
        """测试获取不存在视频的信息"""
        config = {}
        composer = VideoComposer(config)
        
        with pytest.raises((FileNotFoundError, RuntimeError)):
            composer.get_video_info("nonexistent_video.mp4")


class TestVideoComposerExtractFrame:
    """VideoComposer 抽帧测试"""

    def test_extract_last_frame_file_not_found(self):
        """测试抽取不存在视频的帧"""
        config = {}
        composer = VideoComposer(config)
        
        with pytest.raises((FileNotFoundError, RuntimeError)):
            composer.extract_last_frame("nonexistent_video.mp4")


class TestLongVideoGenerator:
    """LongVideoGenerator 单元测试"""

    def test_long_video_generator_init(self):
        """测试 LongVideoGenerator 初始化"""
        config = {
            "long_video": {
                "default_duration_minutes": 5,
                "segment_duration_seconds": 5,
                "temp_directory": "output/temp"
            }
        }
        platform_manager = MagicMock()
        route_service = MagicMock()
        video_composer = MagicMock()
        
        generator = LongVideoGenerator(
            config=config,
            platform_manager=platform_manager,
            route_service=route_service,
            video_composer=video_composer
        )
        
        assert generator.default_duration_minutes == 5
        assert generator.segment_duration_seconds == 5
        assert generator.temp_directory == "output/temp"

    def test_calculate_segment_count(self):
        """测试片段数量计算"""
        config = {"long_video": {"segment_duration_seconds": 5}}
        generator = LongVideoGenerator(
            config=config,
            platform_manager=MagicMock(),
            route_service=MagicMock(),
            video_composer=MagicMock()
        )
        
        assert generator._calculate_segment_count(1) == 12
        assert generator._calculate_segment_count(5) == 60
        assert generator._calculate_segment_count(0.5) == 6

    def test_load_prompts_from_file(self):
        """测试从文件加载提示词"""
        config = {}
        generator = LongVideoGenerator(
            config=config,
            platform_manager=MagicMock(),
            route_service=MagicMock(),
            video_composer=MagicMock()
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("提示词1\n")
            f.write("提示词2\n")
            f.write("提示词3\n")
            temp_path = f.name
        
        try:
            prompts = generator._load_prompts_from_file(temp_path)
            assert prompts == ["提示词1", "提示词2", "提示词3"]
        finally:
            os.unlink(temp_path)

    def test_load_prompts_from_file_not_found(self):
        """测试加载不存在的提示词文件"""
        config = {}
        generator = LongVideoGenerator(
            config=config,
            platform_manager=MagicMock(),
            route_service=MagicMock(),
            video_composer=MagicMock()
        )
        
        with pytest.raises(FileNotFoundError):
            generator._load_prompts_from_file("nonexistent_file.txt")

    def test_get_prompt_for_segment_unified(self):
        """测试统一提示词模式"""
        config = {}
        generator = LongVideoGenerator(
            config=config,
            platform_manager=MagicMock(),
            route_service=MagicMock(),
            video_composer=MagicMock()
        )
        
        prompt = generator._get_prompt_for_segment("一只猫", 0, None)
        assert prompt == "一只猫"
        
        prompt = generator._get_prompt_for_segment("一只猫", 5, None)
        assert prompt == "一只猫"

    def test_get_prompt_for_segment_sequence(self):
        """测试提示词序列模式"""
        config = {}
        generator = LongVideoGenerator(
            config=config,
            platform_manager=MagicMock(),
            route_service=MagicMock(),
            video_composer=MagicMock()
        )
        
        prompts_list = ["日出", "云海", "山峰"]
        
        prompt = generator._get_prompt_for_segment("基础提示词", 0, prompts_list)
        assert prompt == "日出"
        
        prompt = generator._get_prompt_for_segment("基础提示词", 1, prompts_list)
        assert prompt == "云海"
        
        prompt = generator._get_prompt_for_segment("基础提示词", 2, prompts_list)
        assert prompt == "山峰"

    def test_get_prompt_for_segment_out_of_range(self):
        """测试提示词索引超出范围 - 返回最后一个提示词"""
        config = {}
        generator = LongVideoGenerator(
            config=config,
            platform_manager=MagicMock(),
            route_service=MagicMock(),
            video_composer=MagicMock()
        )
        
        prompts_list = ["提示词1", "提示词2"]
        
        prompt = generator._get_prompt_for_segment("基础提示词", 5, prompts_list)
        assert prompt == "提示词2"


class TestLongVideoGeneratorPlatformSelection:
    """LongVideoGenerator 平台选择测试"""

    def test_get_t2v_platforms(self):
        """测试获取文生视频平台"""
        config = {
            "platforms": [
                {"name": "platform1", "description": "文生视频，适合动态场景"},
                {"name": "platform2", "description": "图生视频，将静态图片转为动态"},
                {"name": "platform3", "description": "文生视频平台"},
            ]
        }
        
        generator = LongVideoGenerator(
            config=config,
            platform_manager=MagicMock(),
            route_service=MagicMock(),
            video_composer=MagicMock()
        )
        
        t2v_platforms = generator._get_t2v_platforms()
        assert len(t2v_platforms) == 2
        assert t2v_platforms[0]["name"] == "platform1"
        assert t2v_platforms[1]["name"] == "platform3"

    def test_get_i2v_platforms(self):
        """测试获取图生视频平台"""
        config = {
            "platforms": [
                {"name": "platform1", "description": "文生视频，适合动态场景"},
                {"name": "platform2", "description": "图生视频，将静态图片转为动态"},
                {"name": "platform3", "description": "图生视频平台"},
            ]
        }
        
        generator = LongVideoGenerator(
            config=config,
            platform_manager=MagicMock(),
            route_service=MagicMock(),
            video_composer=MagicMock()
        )
        
        i2v_platforms = generator._get_i2v_platforms()
        assert len(i2v_platforms) == 2
        assert i2v_platforms[0]["name"] == "platform2"
        assert i2v_platforms[1]["name"] == "platform3"


class TestLongVideoGeneratorIntegration:
    """LongVideoGenerator 集成测试"""

    @patch('src.long_video_generator.LongVideoGenerator._generate_segment')
    def test_generate_long_video_flow(self, mock_generate_segment):
        """测试长视频生成流程"""
        config = {
            "long_video": {
                "segment_duration_seconds": 5,
                "cleanup_on_success": False
            }
        }
        
        mock_generate_segment.return_value = (True, "temp_segment.mp4", None)
        
        platform_manager = MagicMock()
        platform_manager.platforms = [
            {"name": "t2v", "description": "文生视频"}
        ]
        
        route_service = MagicMock()
        video_composer = MagicMock()
        video_composer.compose.return_value = "final_video.mp4"
        
        generator = LongVideoGenerator(
            config=config,
            platform_manager=platform_manager,
            route_service=route_service,
            video_composer=video_composer
        )
        
        result = generator.generate(
            prompt="一只猫在奔跑",
            duration_minutes=0.1
        )
        
        assert result is not None
        assert mock_generate_segment.call_count > 0

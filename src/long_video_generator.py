import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.logger import get_logger


class LongVideoGenerator:
    def __init__(
        self,
        config: dict,
        platform_manager,
        route_service,
        video_composer
    ):
        self.config = config
        self.platform_manager = platform_manager
        self.route_service = route_service
        self.video_composer = video_composer
        self.logger = get_logger()
        
        long_video_config = config.get("long_video", {})
        self.default_duration_minutes = long_video_config.get("default_duration_minutes", 5)
        self.segment_duration_seconds = long_video_config.get("segment_duration_seconds", 5)
        self.max_concurrent_segments = long_video_config.get("max_concurrent_segments", 1)
        self.retry_failed_segments = long_video_config.get("retry_failed_segments", True)
        self.min_success_ratio = long_video_config.get("min_success_ratio", 0.8)
        self.temp_directory = long_video_config.get("temp_directory", "output/temp")
        self.cleanup_on_success = long_video_config.get("cleanup_on_success", True)
        self.cleanup_on_failure = long_video_config.get("cleanup_on_failure", False)
        
        self._ensure_temp_directory()
    
    def _ensure_temp_directory(self) -> None:
        Path(self.temp_directory).mkdir(parents=True, exist_ok=True)
    
    def _generate_temp_path(self, prefix: str = "segment", suffix: str = ".mp4") -> str:
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}_{int(time.time())}{suffix}"
        return str(Path(self.temp_directory) / filename)
    
    def _load_prompts_from_file(self, file_path: str) -> List[str]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"提示词文件不存在: {file_path}")
        
        prompts = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    prompts.append(line)
        
        if not prompts:
            raise ValueError(f"提示词文件为空或没有有效提示词: {file_path}")
        
        self.logger.info(f"从文件加载了 {len(prompts)} 个提示词: {file_path}")
        return prompts
    
    def _get_prompt_for_segment(
        self,
        base_prompt: str,
        index: int,
        prompts_list: Optional[List[str]] = None
    ) -> str:
        if prompts_list is None or len(prompts_list) == 0:
            return base_prompt
        
        if index < len(prompts_list):
            return prompts_list[index]
        else:
            return prompts_list[-1]
    
    def _calculate_segment_count(self, duration_minutes: float) -> int:
        total_seconds = duration_minutes * 60
        segment_count = int(total_seconds / self.segment_duration_seconds)
        return max(1, segment_count)
    
    def _get_t2v_platforms(self) -> List[Dict[str, Any]]:
        platforms = self.config.get("platforms", [])
        return [p for p in platforms if "文生视频" in p.get("description", "")]
    
    def _get_i2v_platforms(self) -> List[Dict[str, Any]]:
        platforms = self.config.get("platforms", [])
        return [p for p in platforms if "图生视频" in p.get("description", "")]
    
    def _generate_segment(
        self,
        prompt: str,
        index: int,
        start_frame_path: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        self.logger.info(f"生成片段 {index + 1}: prompt='{prompt[:50]}...', start_frame={start_frame_path is not None}")
        
        segment_path = self._generate_temp_path(f"segment_{index:04d}", ".mp4")
        
        if start_frame_path and os.path.exists(start_frame_path):
            i2v_platforms = self._get_i2v_platforms()
            if i2v_platforms:
                import base64
                with open(start_frame_path, 'rb') as f:
                    image_base64 = base64.b64encode(f.read()).decode('utf-8')
                image_url_data = f"data:image/png;base64,{image_base64}"
                
                if self.route_service and self.route_service.is_available():
                    result = self.route_service.select_i2v_platform(prompt, start_frame_path, i2v_platforms)
                    platform_config = result.get("platform", {})
                else:
                    platform_config = i2v_platforms[0]
                
                if not platform_config:
                    self.logger.warning("未找到可用的图生视频平台，尝试文生视频")
                    return self._generate_t2v_segment(prompt, segment_path)
                
                success, data, error = self.platform_manager.generate_with_platform(
                    platform_config=platform_config,
                    prompt=prompt,
                    image_url=image_url_data
                )
                
                if success:
                    with open(segment_path, 'wb') as f:
                        f.write(data)
                    self.logger.info(f"片段 {index + 1} 生成成功 (图生视频): {segment_path}")
                    return True, segment_path, None
                else:
                    self.logger.warning(f"图生视频失败: {error}，尝试文生视频")
                    return self._generate_t2v_segment(prompt, segment_path)
            else:
                self.logger.warning("没有可用的图生视频平台，使用文生视频")
                return self._generate_t2v_segment(prompt, segment_path)
        else:
            return self._generate_t2v_segment(prompt, segment_path)
    
    def _generate_t2v_segment(
        self,
        prompt: str,
        output_path: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        t2v_platforms = self._get_t2v_platforms()
        
        if not t2v_platforms:
            return False, None, "没有可用的文生视频平台"
        
        if self.route_service and self.route_service.is_available():
            result = self.route_service.select_platform(prompt, t2v_platforms)
            platform_config = result.get("platform", {})
        else:
            platform_config = t2v_platforms[0]
        
        if not platform_config:
            return False, None, "未找到可用的文生视频平台"
        
        success, data, error = self.platform_manager.generate_with_platform(
            platform_config=platform_config,
            prompt=prompt
        )
        
        if success:
            with open(output_path, 'wb') as f:
                f.write(data)
            self.logger.info(f"文生视频片段生成成功: {output_path}")
            return True, output_path, None
        else:
            return False, None, error
    
    def _generate_with_chain(
        self,
        base_prompt: str,
        segment_count: int,
        prompts_list: Optional[List[str]] = None
    ) -> List[str]:
        video_paths = []
        last_frame_path = None
        
        for i in range(segment_count):
            prompt = self._get_prompt_for_segment(base_prompt, i, prompts_list)
            
            print(f"正在生成片段 {i + 1}/{segment_count}...")
            
            success, segment_path, error = self._generate_segment(
                prompt=prompt,
                index=i,
                start_frame_path=last_frame_path
            )
            
            if success and segment_path:
                video_paths.append(segment_path)
                
                if i < segment_count - 1:
                    try:
                        last_frame_path = self.video_composer.extract_last_frame(segment_path)
                        self.logger.debug(f"提取最后一帧: {last_frame_path}")
                    except Exception as e:
                        self.logger.warning(f"提取最后一帧失败: {e}")
                        last_frame_path = None
            else:
                self.logger.error(f"片段 {i + 1} 生成失败: {error}")
                if not self.retry_failed_segments:
                    continue
        
        return video_paths
    
    def generate(
        self,
        prompt: str,
        duration_minutes: Optional[float] = None,
        prompts_list: Optional[List[str]] = None,
        prompts_file: Optional[str] = None
    ) -> str:
        if prompts_file:
            prompts_list = self._load_prompts_from_file(prompts_file)
            self.logger.info(f"使用提示词文件，共 {len(prompts_list)} 个提示词")
        
        if prompts_list:
            segment_count = len(prompts_list)
            self.logger.info(f"使用提示词列表，将生成 {segment_count} 个片段")
        else:
            duration = duration_minutes or self.default_duration_minutes
            segment_count = self._calculate_segment_count(duration)
            self.logger.info(f"目标时长 {duration} 分钟，将生成 {segment_count} 个片段")
        
        print(f"\n开始生成长视频，共 {segment_count} 个片段...")
        print(f"提示词模式: {'提示词序列' if prompts_list else '统一提示词'}")
        
        start_time = time.time()
        
        video_paths = self._generate_with_chain(prompt, segment_count, prompts_list)
        
        if not video_paths:
            raise RuntimeError("所有视频片段生成失败")
        
        min_required = int(segment_count * self.min_success_ratio)
        if len(video_paths) < min_required:
            raise RuntimeError(
                f"成功片段数 {len(video_paths)} 小于最小要求 {min_required} "
                f"(成功率 {len(video_paths)/segment_count:.1%} < {self.min_success_ratio:.0%})"
            )
        
        print(f"\n片段生成完成，成功 {len(video_paths)}/{segment_count} 个")
        print("正在拼接视频...")
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = str(Path(self.temp_directory).parent / f"long_video_{timestamp}.mp4")
        
        final_path = self.video_composer.compose(video_paths, output_path)
        
        elapsed_time = time.time() - start_time
        print(f"\n长视频生成完成!")
        print(f"输出文件: {final_path}")
        print(f"总耗时: {elapsed_time:.1f} 秒")
        
        if self.cleanup_on_success:
            print("正在清理临时文件...")
            self.video_composer.cleanup_temp_files(video_paths)
        
        return final_path

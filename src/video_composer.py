import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.logger import get_logger

try:
    from moviepy import VideoFileClip, concatenate_videoclips
    from PIL import Image
    import numpy as np
    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        from moviepy.editor import VideoFileClip, concatenate_videoclips
        from PIL import Image
        import numpy as np
        MOVIEPY_AVAILABLE = True
    except ImportError:
        MOVIEPY_AVAILABLE = False


class VideoComposer:
    def __init__(self, config: dict):
        self.logger = get_logger()
        long_video_config = config.get("long_video", {})
        self.temp_directory = long_video_config.get("temp_directory", "output/temp")
        self.output_format = long_video_config.get("output_format", "mp4")
        self.output_resolution = long_video_config.get("output_resolution", "1080p")
        self.transition_config = long_video_config.get("transition", {})
        self._resolution_map = {
            "480p": (854, 480),
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "2k": (2560, 1440),
            "4k": (3840, 2160),
        }
        self._ensure_temp_directory()

    def _ensure_temp_directory(self) -> None:
        Path(self.temp_directory).mkdir(parents=True, exist_ok=True)

    def _get_target_resolution(self) -> Tuple[int, int]:
        return self._resolution_map.get(self.output_resolution, (1920, 1080))

    def _generate_temp_path(self, prefix: str = "temp", suffix: str = "") -> str:
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}_{int(time.time())}{suffix}"
        return str(Path(self.temp_directory) / filename)

    def get_video_info(self, video_path: str) -> dict:
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("moviepy 库未安装，无法获取视频信息")
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        self.logger.debug(f"获取视频信息: {video_path}")
        
        clip = VideoFileClip(video_path)
        try:
            info = {
                "duration": clip.duration,
                "fps": clip.fps,
                "width": clip.w,
                "height": clip.h,
                "resolution": f"{clip.w}x{clip.h}",
                "format": Path(video_path).suffix.lower().lstrip("."),
                "size_bytes": os.path.getsize(video_path),
                "path": video_path,
            }
            self.logger.debug(f"视频信息: 时长={info['duration']:.2f}s, 分辨率={info['resolution']}, FPS={info['fps']}")
            return info
        finally:
            clip.close()

    def compose(
        self,
        video_paths: List[str],
        output_path: str,
        transition_config: Optional[dict] = None
    ) -> str:
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("moviepy 库未安装，无法拼接视频")
        
        if not video_paths:
            raise ValueError("视频路径列表不能为空")
        
        for path in video_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"视频文件不存在: {path}")
        
        self.logger.info(f"开始拼接 {len(video_paths)} 个视频片段")
        
        transition = transition_config or self.transition_config
        target_width, target_height = self._get_target_resolution()
        
        clips = []
        for i, path in enumerate(video_paths):
            self.logger.debug(f"加载视频片段 {i+1}/{len(video_paths)}: {path}")
            clip = VideoFileClip(path)
            
            if clip.w != target_width or clip.h != target_height:
                self.logger.debug(f"缩放视频 {path}: {clip.w}x{clip.h} -> {target_width}x{target_height}")
                try:
                    clip = clip.resized(new_size=(target_width, target_height))
                except (AttributeError, TypeError):
                    try:
                        clip = clip.resize(newsize=(target_width, target_height))
                    except TypeError:
                        clip = clip.resize(new_size=(target_width, target_height))
            
            clips.append(clip)
        
        try:
            if transition and transition.get("enabled", False):
                final_clip = self._compose_with_transition(clips, transition)
            else:
                final_clip = concatenate_videoclips(clips, method="compose")
            
            output_path = self._ensure_output_format(output_path)
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"正在写入最终视频: {output_path}")
            final_clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=self._generate_temp_path("audio", ".m4a"),
                remove_temp=True,
                logger=None
            )
            
            total_duration = sum(clip.duration for clip in clips)
            self.logger.info(f"视频拼接完成: {output_path}, 总时长: {total_duration:.2f}s")
            
            return output_path
        finally:
            for clip in clips:
                clip.close()
            if 'final_clip' in locals():
                final_clip.close()

    def _compose_with_transition(self, clips: List, transition_config: dict) -> Any:
        transition_type = transition_config.get("type", "fade")
        transition_duration = transition_config.get("duration_seconds", 0.5)
        
        self.logger.debug(f"应用转场效果: type={transition_type}, duration={transition_duration}s")
        
        if transition_type == "fade":
            return self._apply_fade_transition(clips, transition_duration)
        elif transition_type == "crossfade":
            return self._apply_crossfade_transition(clips, transition_duration)
        else:
            return concatenate_videoclips(clips, method="compose")

    def _apply_fade_transition(self, clips: List, duration: float) -> Any:
        processed_clips = []
        for i, clip in enumerate(clips):
            if i == 0:
                processed_clips.append(clip.fadein(duration))
            elif i == len(clips) - 1:
                processed_clips.append(clip.fadeout(duration))
            else:
                processed_clips.append(clip.fadein(duration).fadeout(duration))
        
        return concatenate_videoclips(processed_clips, method="compose")

    def _apply_crossfade_transition(self, clips: List, duration: float) -> Any:
        if len(clips) == 1:
            return clips[0]
        
        result = clips[0]
        for i in range(1, len(clips)):
            result = result.crossfadein(clips[i], duration)
        
        return result

    def _ensure_output_format(self, output_path: str) -> str:
        path = Path(output_path)
        ext = path.suffix.lower()
        
        if ext not in [".mp4", ".webm", ".mov", ".avi"]:
            output_path = str(path.with_suffix(f".{self.output_format}"))
        
        return output_path

    def extract_last_frame(self, video_path: str) -> str:
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("moviepy 库未安装，无法抽取视频帧")
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        self.logger.debug(f"抽取最后一帧: {video_path}")
        
        clip = VideoFileClip(video_path)
        try:
            frame_time = max(0, clip.duration - 0.01)
            frame = clip.get_frame(frame_time)
            
            output_path = self._generate_temp_path("last_frame", ".png")
            
            img = Image.fromarray(frame)
            img.save(output_path, "PNG")
            
            self.logger.debug(f"最后一帧已保存: {output_path}")
            return output_path
        finally:
            clip.close()

    def extract_frame_at_time(self, video_path: str, time_seconds: float) -> str:
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("moviepy 库未安装，无法抽取视频帧")
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        clip = VideoFileClip(video_path)
        try:
            time_seconds = max(0, min(time_seconds, clip.duration - 0.01))
            frame = clip.get_frame(time_seconds)
            
            output_path = self._generate_temp_path("frame", ".png")
            
            img = Image.fromarray(frame)
            img.save(output_path, "PNG")
            
            return output_path
        finally:
            clip.close()

    def cleanup_temp_files(self, file_paths: Optional[List[str]] = None) -> None:
        if file_paths:
            for path in file_paths:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                        self.logger.debug(f"已清理临时文件: {path}")
                except Exception as e:
                    self.logger.warning(f"清理临时文件失败 {path}: {e}")
        else:
            temp_dir = Path(self.temp_directory)
            if temp_dir.exists():
                for file in temp_dir.iterdir():
                    try:
                        if file.is_file():
                            file.unlink()
                            self.logger.debug(f"已清理临时文件: {file}")
                    except Exception as e:
                        self.logger.warning(f"清理临时文件失败 {file}: {e}")

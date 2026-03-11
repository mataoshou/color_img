import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.video_saver import VideoSaver


MP4_HEADER = b'\x00\x00\x00\x1c' + b'\x00' * 100
WEBM_HEADER = b'\x1a\x45\xdf\xa3' + b'\x00' * 100


class TestVideoSaverInit:
    def test_init_with_config(self):
        config = {
            "output": {
                "directory": "./test_videos",
                "naming": "sequential",
            }
        }
        saver = VideoSaver(config)
        assert saver.directory == "./test_videos"
        assert saver.naming == "sequential"

    def test_init_default_values(self):
        config = {}
        saver = VideoSaver(config)
        assert saver.directory == "./output"
        assert saver.naming == "timestamp"

    def test_init_partial_config(self):
        config = {"output": {"directory": "./custom_videos"}}
        saver = VideoSaver(config)
        assert saver.directory == "./custom_videos"
        assert saver.naming == "timestamp"


class TestEnsureDirectory:
    def test_ensure_directory_creates_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "videos")
            config = {"output": {"directory": new_dir}}
            saver = VideoSaver(config)
            saver._ensure_directory()
            assert os.path.exists(new_dir)

    def test_ensure_directory_existing_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir}}
            saver = VideoSaver(config)
            saver._ensure_directory()
            assert os.path.exists(tmpdir)

    def test_ensure_directory_nested(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = os.path.join(tmpdir, "level1", "level2", "videos")
            config = {"output": {"directory": nested_dir}}
            saver = VideoSaver(config)
            saver._ensure_directory()
            assert os.path.exists(nested_dir)


class TestSanitizeFilename:
    def test_sanitize_filename_removes_invalid_chars(self):
        config = {}
        saver = VideoSaver(config)
        result = saver._sanitize_filename('video<>:"/\\|?*name')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "/" not in result
        assert "\\" not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result

    def test_sanitize_filename_replaces_spaces(self):
        config = {}
        saver = VideoSaver(config)
        result = saver._sanitize_filename("video name with spaces")
        assert " " not in result
        assert "_" in result

    def test_sanitize_filename_strips_dots_underscores(self):
        config = {}
        saver = VideoSaver(config)
        result = saver._sanitize_filename("._videoname._")
        assert not result.startswith(".")
        assert not result.startswith("_")
        assert not result.endswith(".")
        assert not result.endswith("_")

    def test_sanitize_filename_truncates_long_names(self):
        config = {}
        saver = VideoSaver(config)
        long_name = "a" * 200
        result = saver._sanitize_filename(long_name)
        assert len(result) <= 100

    def test_sanitize_filename_empty_result(self):
        config = {}
        saver = VideoSaver(config)
        result = saver._sanitize_filename("...///...")
        assert result == "video"


class TestGenerateFilenameTimestamp:
    def test_generate_filename_timestamp_format(self):
        config = {}
        saver = VideoSaver(config)
        result = saver._generate_filename_timestamp()
        assert len(result) == 15
        assert "_" in result

    def test_generate_filename_timestamp_unique(self):
        config = {}
        saver = VideoSaver(config)
        with patch("time.strftime", side_effect=["time1", "time2"]):
            result1 = saver._generate_filename_timestamp()
            result2 = saver._generate_filename_timestamp()
            assert result1 != result2 or result1 == "time1"


class TestGenerateFilenameSequential:
    def test_generate_filename_sequential_increments(self):
        config = {}
        saver = VideoSaver(config)
        result1 = saver._generate_filename_sequential()
        result2 = saver._generate_filename_sequential()
        assert result1 == "video_0001"
        assert result2 == "video_0002"

    def test_generate_filename_sequential_format(self):
        config = {}
        saver = VideoSaver(config)
        result = saver._generate_filename_sequential()
        assert result.startswith("video_")
        assert len(result.split("_")[1]) == 4


class TestGenerateFilenamePrompt:
    def test_generate_filename_prompt_basic(self):
        config = {}
        saver = VideoSaver(config)
        result = saver._generate_filename_prompt("a running cat")
        assert "a_running_cat" in result or "a" in result

    def test_generate_filename_prompt_empty(self):
        config = {}
        saver = VideoSaver(config)
        with patch.object(saver, "_generate_filename_timestamp", return_value="timestamp"):
            result = saver._generate_filename_prompt("")
            assert result == "timestamp"

    def test_generate_filename_prompt_sanitizes(self):
        config = {}
        saver = VideoSaver(config)
        result = saver._generate_filename_prompt('test<>:"/\\|?*prompt')
        assert "<" not in result


class TestGenerateFilename:
    def test_generate_filename_timestamp_mode(self):
        config = {"output": {"naming": "timestamp"}}
        saver = VideoSaver(config)
        with patch.object(saver, "_generate_filename_timestamp", return_value="timestamp_name"):
            result = saver._generate_filename()
            assert result == "timestamp_name"

    def test_generate_filename_sequential_mode(self):
        config = {"output": {"naming": "sequential"}}
        saver = VideoSaver(config)
        result = saver._generate_filename()
        assert result.startswith("video_")

    def test_generate_filename_prompt_mode(self):
        config = {"output": {"naming": "prompt"}}
        saver = VideoSaver(config)
        result = saver._generate_filename("test video")
        assert "test" in result or "video" in result


class TestResolveConflict:
    def test_resolve_conflict_no_conflict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir}}
            saver = VideoSaver(config)
            filepath = Path(tmpdir) / "new_video.mp4"
            result = saver._resolve_conflict(filepath)
            assert result == filepath

    def test_resolve_conflict_with_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir}}
            saver = VideoSaver(config)
            filepath = Path(tmpdir) / "existing.mp4"
            filepath.touch()
            result = saver._resolve_conflict(filepath)
            assert result.name == "existing_1.mp4"

    def test_resolve_conflict_multiple(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir}}
            saver = VideoSaver(config)
            filepath = Path(tmpdir) / "existing.mp4"
            filepath.touch()
            (Path(tmpdir) / "existing_1.mp4").touch()
            (Path(tmpdir) / "existing_2.mp4").touch()
            result = saver._resolve_conflict(filepath)
            assert result.name == "existing_3.mp4"


class TestDetectVideoFormat:
    def test_detect_video_format_mp4(self):
        config = {}
        saver = VideoSaver(config)
        result = saver._detect_video_format(MP4_HEADER)
        assert result == ".mp4"

    def test_detect_video_format_mp4_variant(self):
        config = {}
        saver = VideoSaver(config)
        mp4_variant = b'\x00\x00\x00\x20' + b'\x00' * 100
        result = saver._detect_video_format(mp4_variant)
        assert result == ".mp4"

    def test_detect_video_format_webm(self):
        config = {}
        saver = VideoSaver(config)
        result = saver._detect_video_format(WEBM_HEADER)
        assert result == ".webm"

    def test_detect_video_format_unknown(self):
        config = {}
        saver = VideoSaver(config)
        unknown_data = b'\x00\x00\x00\x00' + b'\x00' * 100
        result = saver._detect_video_format(unknown_data)
        assert result == ".mp4"


class TestDownloadVideo:
    def test_download_video_success(self):
        config = {}
        saver = VideoSaver(config)
        mock_response = MagicMock()
        mock_response.content = b"video_data"
        mock_response.raise_for_status = MagicMock()
        with patch("requests.get", return_value=mock_response):
            result = saver.download_video("https://example.com/video.mp4")
            assert result == b"video_data"

    def test_download_video_with_timeout(self):
        config = {}
        saver = VideoSaver(config)
        mock_response = MagicMock()
        mock_response.content = b"video_data"
        mock_response.raise_for_status = MagicMock()
        with patch("requests.get", return_value=mock_response) as mock_get:
            saver.download_video("https://example.com/video.mp4", timeout=120)
            mock_get.assert_called_once()
            assert mock_get.call_args.kwargs["timeout"] == 120


class TestSaveVideo:
    def test_save_video_mp4(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir, "naming": "timestamp"}}
            saver = VideoSaver(config)
            result = saver.save_video(MP4_HEADER)
            assert os.path.exists(result)
            assert result.endswith(".mp4")

    def test_save_video_webm(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir, "naming": "timestamp"}}
            saver = VideoSaver(config)
            result = saver.save_video(WEBM_HEADER)
            assert os.path.exists(result)
            assert result.endswith(".webm")

    def test_save_video_with_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir, "naming": "timestamp"}}
            saver = VideoSaver(config)
            video_data = b"fake_video_data"
            result = saver.save_video(video_data, format="webm")
            assert result.endswith(".webm")

    def test_save_video_with_prompt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir, "naming": "prompt"}}
            saver = VideoSaver(config)
            video_data = b"fake_video_data"
            result = saver.save_video(video_data, prompt="test video", format="mp4")
            assert os.path.exists(result)

    def test_save_video_url(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir, "naming": "timestamp"}}
            saver = VideoSaver(config)
            mock_response = MagicMock()
            mock_response.content = MP4_HEADER
            mock_response.raise_for_status = MagicMock()
            with patch("requests.get", return_value=mock_response):
                result = saver.save_video("https://example.com/video.mp4")
                assert os.path.exists(result)

    def test_save_video_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "new_videos")
            config = {"output": {"directory": new_dir, "naming": "timestamp"}}
            saver = VideoSaver(config)
            video_data = b"fake_video_data"
            result = saver.save_video(video_data, format="mp4")
            assert os.path.exists(new_dir)
            assert os.path.exists(result)

    def test_filename_conflict_resolution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir, "naming": "sequential"}}
            saver = VideoSaver(config)
            video_data = b"fake_video_data"
            result1 = saver.save_video(video_data, format="mp4")
            result2 = saver.save_video(video_data, format="mp4")
            assert result1 != result2

    def test_save_video_string_non_url(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir, "naming": "timestamp"}}
            saver = VideoSaver(config)
            result = saver.save_video("plain text data", format="txt")
            assert os.path.exists(result)
            with open(result, "rb") as f:
                content = f.read()
            assert content == b"plain text data"

    def test_save_video_format_normalization(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir, "naming": "timestamp"}}
            saver = VideoSaver(config)
            video_data = b"fake_video_data"
            result1 = saver.save_video(video_data, format="MP4")
            result2 = saver.save_video(video_data, format=".mp4")
            assert result1.endswith(".mp4")
            assert result2.endswith(".mp4")

    def test_save_video_format_with_dot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir, "naming": "timestamp"}}
            saver = VideoSaver(config)
            video_data = b"fake_video_data"
            result = saver.save_video(video_data, format=".webm")
            assert result.endswith(".webm")
            assert result.count(".webm") == 1

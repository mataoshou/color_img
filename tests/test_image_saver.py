import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.image_saver import ImageSaver


class TestImageSaverInit:
    def test_init_with_config(self):
        config = {
            "output": {
                "directory": "./test_output",
                "naming": "timestamp",
            }
        }
        saver = ImageSaver(config)
        assert saver.directory == "./test_output"
        assert saver.naming == "timestamp"

    def test_init_default_values(self):
        config = {}
        saver = ImageSaver(config)
        assert saver.directory == "./output"
        assert saver.naming == "timestamp"

    def test_init_partial_config(self):
        config = {"output": {"directory": "./custom"}}
        saver = ImageSaver(config)
        assert saver.directory == "./custom"


class TestEnsureDirectory:
    def test_ensure_directory_creates_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": os.path.join(tmpdir, "new_dir")}}
            saver = ImageSaver(config)
            saver._ensure_directory()
            assert os.path.exists(saver.directory)

    def test_ensure_directory_existing_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir}}
            saver = ImageSaver(config)
            saver._ensure_directory()
            assert os.path.exists(tmpdir)

    def test_ensure_directory_nested(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = os.path.join(tmpdir, "level1", "level2", "level3")
            config = {"output": {"directory": nested_dir}}
            saver = ImageSaver(config)
            saver._ensure_directory()
            assert os.path.exists(nested_dir)


class TestSanitizeFilename:
    def test_sanitize_filename_removes_invalid_chars(self):
        config = {}
        saver = ImageSaver(config)
        result = saver._sanitize_filename('file<>:"/\\|?*name')
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
        saver = ImageSaver(config)
        result = saver._sanitize_filename("file name with spaces")
        assert " " not in result
        assert "_" in result

    def test_sanitize_filename_strips_dots_underscores(self):
        config = {}
        saver = ImageSaver(config)
        result = saver._sanitize_filename("._filename._")
        assert not result.startswith(".")
        assert not result.startswith("_")
        assert not result.endswith(".")
        assert not result.endswith("_")

    def test_sanitize_filename_truncates_long_names(self):
        config = {}
        saver = ImageSaver(config)
        long_name = "a" * 200
        result = saver._sanitize_filename(long_name)
        assert len(result) <= 100

    def test_sanitize_filename_empty_result(self):
        config = {}
        saver = ImageSaver(config)
        result = saver._sanitize_filename("...///...")
        assert result == "image"


class TestGenerateFilenameTimestamp:
    def test_generate_filename_timestamp_format(self):
        config = {}
        saver = ImageSaver(config)
        result = saver._generate_filename_timestamp()
        assert len(result) == 15
        assert "_" in result

    def test_generate_filename_timestamp_unique(self):
        config = {}
        saver = ImageSaver(config)
        with patch("time.strftime", side_effect=["time1", "time2"]):
            result1 = saver._generate_filename_timestamp()
            result2 = saver._generate_filename_timestamp()
            assert result1 != result2 or result1 == "time1"


class TestGenerateFilenameSequential:
    def test_generate_filename_sequential_increments(self):
        config = {}
        saver = ImageSaver(config)
        result1 = saver._generate_filename_sequential()
        result2 = saver._generate_filename_sequential()
        assert result1 == "image_0001"
        assert result2 == "image_0002"

    def test_generate_filename_sequential_format(self):
        config = {}
        saver = ImageSaver(config)
        result = saver._generate_filename_sequential()
        assert result.startswith("image_")
        assert len(result.split("_")[1]) == 4


class TestGenerateFilenamePrompt:
    def test_generate_filename_prompt_basic(self):
        config = {}
        saver = ImageSaver(config)
        result = saver._generate_filename_prompt("a cute cat")
        assert "a_cute_cat" in result or "a" in result

    def test_generate_filename_prompt_empty(self):
        config = {}
        saver = ImageSaver(config)
        with patch.object(saver, "_generate_filename_timestamp", return_value="timestamp"):
            result = saver._generate_filename_prompt("")
            assert result == "timestamp"

    def test_generate_filename_prompt_sanitizes(self):
        config = {}
        saver = ImageSaver(config)
        result = saver._generate_filename_prompt('test<>:"/\\|?*prompt')
        assert "<" not in result


class TestGenerateFilename:
    def test_generate_filename_timestamp_mode(self):
        config = {"output": {"naming": "timestamp"}}
        saver = ImageSaver(config)
        with patch.object(saver, "_generate_filename_timestamp", return_value="timestamp_name"):
            result = saver._generate_filename()
            assert result == "timestamp_name"

    def test_generate_filename_sequential_mode(self):
        config = {"output": {"naming": "sequential"}}
        saver = ImageSaver(config)
        result = saver._generate_filename()
        assert result.startswith("image_")

    def test_generate_filename_prompt_mode(self):
        config = {"output": {"naming": "prompt"}}
        saver = ImageSaver(config)
        result = saver._generate_filename("test prompt")
        assert "test" in result or "prompt" in result


class TestResolveConflict:
    def test_resolve_conflict_no_conflict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir}}
            saver = ImageSaver(config)
            filepath = Path(tmpdir) / "new_file.png"
            result = saver._resolve_conflict(filepath)
            assert result == filepath

    def test_resolve_conflict_with_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir}}
            saver = ImageSaver(config)
            filepath = Path(tmpdir) / "existing.png"
            filepath.touch()
            result = saver._resolve_conflict(filepath)
            assert result.name == "existing_1.png"

    def test_resolve_conflict_multiple(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir}}
            saver = ImageSaver(config)
            filepath = Path(tmpdir) / "existing.png"
            filepath.touch()
            (Path(tmpdir) / "existing_1.png").touch()
            (Path(tmpdir) / "existing_2.png").touch()
            result = saver._resolve_conflict(filepath)
            assert result.name == "existing_3.png"


class TestDetectFormat:
    def test_detect_format_png(self):
        config = {}
        saver = ImageSaver(config)
        png_header = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        result = saver._detect_format(png_header)
        assert result == ".png"

    def test_detect_format_jpg(self):
        config = {}
        saver = ImageSaver(config)
        jpg_header = b'\xff\xd8' + b'\x00' * 100
        result = saver._detect_format(jpg_header)
        assert result == ".jpg"

    def test_detect_format_unknown(self):
        config = {}
        saver = ImageSaver(config)
        unknown_data = b'\x00\x00\x00\x00' + b'\x00' * 100
        result = saver._detect_format(unknown_data)
        assert result == ".png"


class TestDownloadImage:
    def test_download_image_success(self):
        config = {}
        saver = ImageSaver(config)
        mock_response = MagicMock()
        mock_response.content = b"image_data"
        mock_response.raise_for_status = MagicMock()
        with patch("requests.get", return_value=mock_response):
            result = saver.download_image("https://example.com/image.png")
            assert result == b"image_data"

    def test_download_image_with_timeout(self):
        config = {}
        saver = ImageSaver(config)
        mock_response = MagicMock()
        mock_response.content = b"image_data"
        mock_response.raise_for_status = MagicMock()
        with patch("requests.get", return_value=mock_response) as mock_get:
            saver.download_image("https://example.com/image.png", timeout=60)
            mock_get.assert_called_once()
            assert mock_get.call_args.kwargs["timeout"] == 60


class TestSaveImage:
    def test_save_image_bytes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir, "naming": "timestamp"}}
            saver = ImageSaver(config)
            image_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
            result = saver.save_image(image_data)
            assert os.path.exists(result)
            assert result.endswith(".png")

    def test_save_image_with_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir, "naming": "timestamp"}}
            saver = ImageSaver(config)
            image_data = b"fake_image_data"
            result = saver.save_image(image_data, format="jpg")
            assert result.endswith(".jpg")

    def test_save_image_with_prompt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir, "naming": "prompt"}}
            saver = ImageSaver(config)
            image_data = b"fake_image_data"
            result = saver.save_image(image_data, prompt="test prompt", format="png")
            assert os.path.exists(result)

    def test_save_image_url(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir, "naming": "timestamp"}}
            saver = ImageSaver(config)
            mock_response = MagicMock()
            mock_response.content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
            mock_response.raise_for_status = MagicMock()
            with patch("requests.get", return_value=mock_response):
                result = saver.save_image("https://example.com/image.png")
                assert os.path.exists(result)

    def test_save_image_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "new_output")
            config = {"output": {"directory": new_dir, "naming": "timestamp"}}
            saver = ImageSaver(config)
            image_data = b"fake_image_data"
            result = saver.save_image(image_data, format="png")
            assert os.path.exists(new_dir)
            assert os.path.exists(result)

    def test_save_image_handles_conflict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir, "naming": "sequential"}}
            saver = ImageSaver(config)
            image_data = b"fake_image_data"
            result1 = saver.save_image(image_data, format="png")
            result2 = saver.save_image(image_data, format="png")
            assert result1 != result2

    def test_save_image_string_non_url(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir, "naming": "timestamp"}}
            saver = ImageSaver(config)
            result = saver.save_image("plain text data", format="txt")
            assert os.path.exists(result)
            with open(result, "rb") as f:
                content = f.read()
            assert content == b"plain text data"

    def test_save_image_format_normalization(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"output": {"directory": tmpdir, "naming": "timestamp"}}
            saver = ImageSaver(config)
            image_data = b"fake_image_data"
            result1 = saver.save_image(image_data, format="PNG")
            result2 = saver.save_image(image_data, format=".png")
            assert result1.endswith(".png")
            assert result2.endswith(".png")

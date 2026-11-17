#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "skill-money-case.content-package.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


validator = load_module("validate_package", ROOT / "scripts" / "validate_package.py")
discovery = load_module("discover_input", ROOT / "scripts" / "discover_input.py")


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_realistic_seven_platform_fixture_is_valid(self):
        errors, warnings = validator.validate(self.payload)
        self.assertEqual(errors, [])
        self.assertEqual(len(self.payload["platforms"]), 7)
        self.assertTrue(any("uncertain evidence" in warning for warning in warnings))

    def test_publisher_export_keeps_four_platform_copy(self):
        exported = validator.publisher_package(self.payload)
        self.assertEqual(exported["xhsTitle"], self.payload["platforms"]["xiaohongshu"]["title"])
        self.assertEqual(exported["douyinTopics"], ["AI工具", "AISkill", "数字产品", "经验产品化"])
        self.assertEqual(exported["wechatTags"], ["AI工具", "AISkill", "数字产品"])
        self.assertEqual(exported["douyinDescription"], "")
        self.assertEqual(exported["wechatShortTitle"], "卖Skill别只看收入")
        self.assertFalse(exported["cover"]["uploadCustomCover"])

    def test_preview_contains_all_seven_platforms_and_complete_copy(self):
        preview = validator.render_preview(self.payload)
        for heading in ("小红书", "抖音", "B站", "视频号", "X", "YouTube", "公众号"):
            self.assertIn(heading, preview)
        self.assertIn(self.payload["platforms"]["xiaohongshu"]["body"], preview)
        self.assertIn(self.payload["platforms"]["wechat_channels"]["description"], preview)
        self.assertIn(self.payload["platforms"]["wechat_official"]["body"], preview)
        self.assertNotIn("视频从……展开", preview)

    def test_preview_topics_are_hash_prefixed_and_space_separated(self):
        preview = validator.render_preview(self.payload)
        self.assertIn("#AI工具 #AISkill #数字产品 #经验产品化", preview)
        self.assertNotIn("#AI工具、", preview)

    def test_douyin_preview_has_no_body(self):
        preview = validator.render_preview(self.payload)
        douyin_section = preview.split("## 2. 抖音", 1)[1].split("## 3. B站", 1)[0]
        self.assertNotIn("正文", douyin_section)
        self.assertIn(self.payload["platforms"]["douyin"]["title"], douyin_section)

    def test_cli_preview_output_creates_single_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "sample_七平台内容预览.md"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "validate_package.py"), str(FIXTURE), "--preview-output", str(output)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.is_file())
            self.assertIn("# 七平台内容预览", output.read_text(encoding="utf-8"))
            self.assertEqual([path.name for path in Path(tmp).iterdir()], [output.name])

    def test_overlong_xiaohongshu_title_fails(self):
        self.payload["platforms"]["xiaohongshu"]["title"] = "这是一个明显超过二十个字符而且不应该通过检查的小红书标题"
        errors, _ = validator.validate(self.payload)
        self.assertTrue(any("xiaohongshu title" in error for error in errors))

    def test_douyin_body_fails(self):
        self.payload["platforms"]["douyin"]["body"] = "这里不应该有正文"
        errors, _ = validator.validate(self.payload)
        self.assertIn("douyin must not contain body; output title and topics only", errors)

    def test_topics_require_hash_prefix_and_reject_dunhao(self):
        self.payload["platforms"]["xiaohongshu"]["topics"] = ["AI工具、AISkill"]
        errors, _ = validator.validate(self.payload)
        self.assertTrue(any("must begin with #" in error for error in errors))
        self.assertTrue(any("must not contain 、" in error for error in errors))

    def test_wechat_channels_requires_structured_long_description(self):
        self.payload["platforms"]["wechat_channels"]["description"] = "太短"
        errors, _ = validator.validate(self.payload)
        self.assertTrue(any("structured long introduction" in error for error in errors))

    def test_discovery_accepts_video_and_finds_single_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            video = folder / "demo.mp4"
            video.write_bytes(b"not-a-real-container")
            script = folder / "口播稿.md"
            script.write_text("测试语料", encoding="utf-8")
            result = discovery.discover(video)
            self.assertEqual(result["scriptCandidates"], [str(script.resolve())])
            self.assertFalse(result["needsUserChoice"])

    def test_srt_entry_finds_same_stem_video_and_parses_timeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            video = folder / "demo.mp4"
            video.write_bytes(b"not-a-real-container")
            subtitle = folder / "demo.srt"
            subtitle.write_text(
                "1\n00:00:00,000 --> 00:00:01,500\n第一句\n\n"
                "2\n00:00:01,500 --> 00:00:03,250\n第二句\n",
                encoding="utf-8",
            )
            result = discovery.discover_source(subtitle)
            self.assertEqual(result["inputType"], "video+subtitle")
            self.assertEqual(result["videoPath"], str(video.resolve()))
            self.assertEqual(result["exactTranscript"], str(subtitle.resolve()))
            self.assertEqual(result["transcriptStats"]["cueCount"], 2)
            self.assertEqual(result["transcriptStats"]["durationSeconds"], 3.25)
            self.assertTrue(result["publisherReady"])

    def test_srt_only_still_allows_content_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            subtitle = Path(tmp) / "solo.srt"
            subtitle.write_text("1\n00:00:00,000 --> 00:00:01,000\n只有字幕\n", encoding="utf-8")
            result = discovery.discover_source(subtitle)
            self.assertEqual(result["inputType"], "subtitle-only")
            self.assertIsNone(result["videoPath"])
            self.assertFalse(result["publisherReady"])


if __name__ == "__main__":
    unittest.main()

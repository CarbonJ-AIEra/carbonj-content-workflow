#!/usr/bin/env python3
"""Validate a CarbonJ content package and render its final Markdown preview."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PLATFORMS = {"xiaohongshu", "douyin", "bilibili", "wechat_channels", "x", "youtube", "wechat_official"}
EVIDENCE_STATUSES = {"verified", "attributed", "uncertain"}
RISKY_PHRASES = ("全网第一", "百分百", "保证赚钱", "轻松赚钱", "躺赚", "人人都能")


def clean_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        text = str(item).strip().lstrip("#").strip()
        if text and text not in result:
            result.append(text)
    return result


def validate_hashtag_list(value, prefix: str, errors: list[str], minimum: int = 0, maximum: int | None = None) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{prefix} must be an array")
        return []
    raw = [str(item).strip() for item in value if str(item).strip()]
    if len(raw) < minimum or (maximum is not None and len(raw) > maximum):
        bound = f"{minimum}-{maximum}" if maximum is not None else f"at least {minimum}"
        errors.append(f"{prefix} requires {bound} items")
    for index, item in enumerate(raw):
        if not item.startswith("#") or item == "#":
            errors.append(f"{prefix}[{index}] must begin with #")
        if "、" in item:
            errors.append(f"{prefix}[{index}] must not contain 、")
    return clean_list(raw)


def require_text(obj: dict, key: str, prefix: str, errors: list[str]) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{prefix}.{key} is required")
        return ""
    return value.strip()


def validate(payload: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if payload.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")

    source = payload.get("source")
    if not isinstance(source, dict):
        errors.append("source is required")
        source = {}
    video_path = str(source.get("videoPath", "")).strip()
    transcript_path = str(source.get("transcriptPath", "")).strip()
    if not video_path and not transcript_path:
        errors.append("source requires videoPath or transcriptPath")

    brief = payload.get("contentBrief")
    if not isinstance(brief, dict):
        errors.append("contentBrief is required")
        brief = {}
    for key in ("subject", "audience", "painPoint", "outcome"):
        require_text(brief, key, "contentBrief", errors)
    evidence = brief.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("contentBrief.evidence requires at least one item")
        evidence = []
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            errors.append(f"contentBrief.evidence[{index}] must be an object")
            continue
        require_text(item, "claim", f"contentBrief.evidence[{index}]", errors)
        require_text(item, "source", f"contentBrief.evidence[{index}]", errors)
        if item.get("status") not in EVIDENCE_STATUSES:
            errors.append(f"contentBrief.evidence[{index}].status is invalid")

    platforms = payload.get("platforms")
    if not isinstance(platforms, dict):
        errors.append("platforms is required")
        platforms = {}
    missing = PLATFORMS - set(platforms)
    if missing:
        errors.append("missing platforms: " + ", ".join(sorted(missing)))

    xhs = platforms.get("xiaohongshu", {})
    xhs_title = require_text(xhs, "title", "platforms.xiaohongshu", errors)
    xhs_body = require_text(xhs, "body", "platforms.xiaohongshu", errors)
    xhs_topics = validate_hashtag_list(xhs.get("topics"), "platforms.xiaohongshu.topics", errors, minimum=1)
    xhs_keywords = clean_list(xhs.get("searchKeywords"))
    if len(xhs_title) > 20:
        errors.append(f"xiaohongshu title is {len(xhs_title)}/20")
    if not xhs_keywords:
        errors.append("xiaohongshu searchKeywords require at least 1 item")
    elif xhs_title and not any(keyword.lower() in xhs_title.lower() for keyword in xhs_keywords):
        errors.append("xiaohongshu title must contain at least one search keyword")
    if xhs_body and not 160 <= len(xhs_body) <= 320:
        warnings.append(f"xiaohongshu body is {len(xhs_body)} characters; target 160-320 around 200")
    searchable = (xhs_title + " " + xhs_body).lower()
    if len(xhs_keywords) >= 2 and sum(keyword.lower() in searchable for keyword in xhs_keywords) < 2:
        warnings.append("xiaohongshu copy covers fewer than two configured search keywords")

    douyin = platforms.get("douyin", {})
    douyin_title = require_text(douyin, "title", "platforms.douyin", errors)
    douyin_body = str(douyin.get("body", "")).strip()
    douyin_topics = validate_hashtag_list(douyin.get("topics"), "platforms.douyin.topics", errors, minimum=1, maximum=5)
    if len(douyin_title) > 30:
        errors.append(f"douyin title is {len(douyin_title)}/30")
    if douyin_body:
        errors.append("douyin must not contain body; output title and topics only")

    bilibili = platforms.get("bilibili", {})
    bilibili_title = require_text(bilibili, "title", "platforms.bilibili", errors)
    bilibili_description = require_text(bilibili, "description", "platforms.bilibili", errors)
    bilibili_tags = validate_hashtag_list(bilibili.get("tags"), "platforms.bilibili.tags", errors, minimum=1, maximum=10)
    if len(bilibili_title) > 80:
        errors.append(f"bilibili title is {len(bilibili_title)}/80")

    channels = platforms.get("wechat_channels", {})
    channels_short_title = require_text(channels, "shortTitle", "platforms.wechat_channels", errors)
    require_text(channels, "coreTheory", "platforms.wechat_channels", errors)
    channels_description = require_text(channels, "description", "platforms.wechat_channels", errors)
    channels_tags = validate_hashtag_list(channels.get("hashtags"), "platforms.wechat_channels.hashtags", errors, minimum=1)
    if len(channels_short_title) > 16:
        warnings.append(f"wechat_channels shortTitle is {len(channels_short_title)} characters; keep it concise")
    paragraphs = [line.strip() for line in channels_description.splitlines() if line.strip() and not line.strip().startswith("#")]
    if channels_description and (len(channels_description) < 120 or len(paragraphs) < 3):
        errors.append("wechat_channels description must be a structured long introduction with at least 3 parts and 120 characters")

    x_obj = platforms.get("x", {})
    x_post = require_text(x_obj, "post", "platforms.x", errors)
    validate_hashtag_list(x_obj.get("hashtags", []), "platforms.x.hashtags", errors)
    youtube = platforms.get("youtube", {})
    require_text(youtube, "title", "platforms.youtube", errors)
    require_text(youtube, "description", "platforms.youtube", errors)
    if not clean_list(youtube.get("keywords")):
        errors.append("youtube keywords require at least 1 item")
    validate_hashtag_list(youtube.get("hashtags", []), "platforms.youtube.hashtags", errors)
    if not isinstance(youtube.get("chapters", []), list):
        errors.append("youtube.chapters must be an array")

    official = platforms.get("wechat_official", {})
    require_text(official, "title", "platforms.wechat_official", errors)
    require_text(official, "digest", "platforms.wechat_official", errors)
    official_body = require_text(official, "body", "platforms.wechat_official", errors)
    if not clean_list(official.get("keywords")):
        errors.append("wechat_official keywords require at least 1 item")

    searchable_text = json.dumps(platforms, ensure_ascii=False)
    for phrase in RISKY_PHRASES:
        if phrase in searchable_text:
            warnings.append(f"review risky phrase: {phrase}")
    if x_post and x_post in {xhs_body, bilibili_description, official_body}:
        warnings.append("X post exactly duplicates another platform body")
    if any(item.get("status") == "uncertain" for item in evidence if isinstance(item, dict)):
        warnings.append("contentBrief contains uncertain evidence; keep it out of final copy or qualify it")
    return errors, warnings


def publisher_package(payload: dict) -> dict:
    p = payload["platforms"]
    video_path = str(payload["source"].get("videoPath", "")).strip()
    if not video_path:
        raise ValueError("publisher output requires source.videoPath")
    return {
        "title": p["bilibili"]["title"],
        "videoPath": video_path,
        "xhsTitle": p["xiaohongshu"]["title"],
        "xiaohongshuBody": p["xiaohongshu"]["body"],
        "xhsTopics": clean_list(p["xiaohongshu"]["topics"]),
        "douyinTitle": p["douyin"]["title"],
        "douyinDescription": "",
        "douyinTopics": clean_list(p["douyin"]["topics"]),
        "bilibiliTitle": p["bilibili"]["title"],
        "bilibiliDescription": p["bilibili"]["description"],
        "bilibiliTags": clean_list(p["bilibili"]["tags"]),
        "wechatTitle": p["wechat_channels"]["shortTitle"],
        "wechatShortTitle": p["wechat_channels"]["shortTitle"],
        "wechatDescription": p["wechat_channels"]["description"],
        "wechatTags": clean_list(p["wechat_channels"]["hashtags"]),
        "cover": {
            "uploadCustomCover": False,
            "vertical3x4Path": "",
            "horizontal4x3Path": "",
        },
    }


def display_hashtags(value) -> str:
    """Render normalized hashtags with spaces and no Chinese enumeration comma."""
    return " ".join(f"#{item}" for item in clean_list(value))


def display_keywords(value) -> str:
    return " / ".join(clean_list(value))


def display_chapters(value) -> str:
    if not isinstance(value, list) or not value:
        return "未提供可靠章节时间点"
    lines: list[str] = []
    for item in value:
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            timestamp = str(item.get("time") or item.get("timestamp") or item.get("start") or "").strip()
            title = str(item.get("title") or item.get("label") or "").strip()
            text = " ".join(part for part in (timestamp, title) if part)
        else:
            text = str(item).strip()
        if text:
            lines.append(text)
    return "\n".join(lines) if lines else "未提供可靠章节时间点"


def render_preview(payload: dict) -> str:
    """Render all seven platforms as complete, reader-friendly Markdown."""
    p = payload["platforms"]
    xhs = p["xiaohongshu"]
    douyin = p["douyin"]
    bilibili = p["bilibili"]
    channels = p["wechat_channels"]
    x_obj = p["x"]
    youtube = p["youtube"]
    official = p["wechat_official"]

    sections = [
        "# 七平台内容预览",
        "## 1. 小红书",
        "### 搜索标题",
        xhs["title"].strip(),
        "### 正文",
        xhs["body"].strip(),
        "### 话题",
        display_hashtags(xhs["topics"]),
        "## 2. 抖音",
        "### 标题",
        douyin["title"].strip(),
        "### 话题",
        display_hashtags(douyin["topics"]),
        "## 3. B站",
        "### 标题",
        bilibili["title"].strip(),
        "### 简介",
        bilibili["description"].strip(),
        "### 标签",
        display_hashtags(bilibili["tags"]),
        "## 4. 视频号",
        "### 短标题",
        channels["shortTitle"].strip(),
        "### 核心理论",
        channels["coreTheory"].strip(),
        "### 结构化简介",
        channels["description"].strip(),
        "### 话题",
        display_hashtags(channels["hashtags"]),
        "## 5. X",
        "### 正文",
        x_obj["post"].strip(),
        "### Hashtags",
        display_hashtags(x_obj.get("hashtags", [])),
        "## 6. YouTube",
        "### 标题",
        youtube["title"].strip(),
        "### 简介",
        youtube["description"].strip(),
        "### 章节",
        display_chapters(youtube.get("chapters", [])),
        "### 关键词",
        display_keywords(youtube["keywords"]),
        "### Hashtags",
        display_hashtags(youtube.get("hashtags", [])),
        "## 7. 公众号",
        "### 标题",
        official["title"].strip(),
        "### 摘要",
        official["digest"].strip(),
        "### 正文",
        official["body"].strip(),
        "### 关键词",
        display_keywords(official["keywords"]),
    ]
    return "\n\n".join(sections) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package")
    parser.add_argument("--preview-output")
    parser.add_argument("--publisher-output")
    args = parser.parse_args()
    package_path = Path(args.package).expanduser().resolve()
    try:
        payload = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    errors, warnings = validate(payload)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.preview_output:
        preview_path = Path(args.preview_output).expanduser().resolve()
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        preview_path.write_text(render_preview(payload), encoding="utf-8")
        print(f"PREVIEW: {preview_path}")
    if args.publisher_output:
        output_path = Path(args.publisher_output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            exported = publisher_package(payload)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        output_path.write_text(json.dumps(exported, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"PUBLISHER_PACKAGE: {output_path}")
    print("VALID: carbonj-content-design schemaVersion 1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

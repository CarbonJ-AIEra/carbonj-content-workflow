#!/usr/bin/env python3
"""Resolve video and subtitle pairs from either a video or subtitle entry path."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}
SUBTITLE_EXTENSIONS = {".srt", ".ass"}


def duration_seconds(video: Path) -> float | None:
    if not shutil.which("ffprobe"):
        return None
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        return round(float(result.stdout.strip()), 3) if result.returncode == 0 else None
    except ValueError:
        return None


def unique_paths(paths: list[Path]) -> list[str]:
    seen: set[Path] = set()
    output: list[str] = []
    for path in paths:
        resolved = path.resolve()
        if resolved.is_file() and resolved not in seen:
            seen.add(resolved)
            output.append(str(resolved))
    return output


def srt_seconds(timestamp: str) -> float:
    hours, minutes, remainder = timestamp.split(":")
    seconds, milliseconds = remainder.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000


def inspect_srt(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    timestamp_pattern = re.compile(
        r"(?m)^(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})"
    )
    matches = list(timestamp_pattern.finditer(text))
    content_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.isdigit() or "-->" in stripped:
            continue
        content_lines.append(re.sub(r"<[^>]+>", "", stripped))
    clean_text = "".join(content_lines)
    return {
        "cueCount": len(matches),
        "durationSeconds": round(srt_seconds(matches[-1].group(2)), 3) if matches else None,
        "textCharacters": len(clean_text),
        "preview": clean_text[:160],
    }


def video_candidates_for_subtitle(subtitle: Path) -> list[str]:
    stem = subtitle.stem.removesuffix("_subtitled")
    direct = [subtitle.parent / f"{stem}{extension}" for extension in (".mp4", ".mov", ".m4v")]
    return unique_paths(direct)


def discover(video: Path, transcript: Path | None = None) -> dict:
    video = video.expanduser().resolve()
    if not video.is_file():
        raise ValueError(f"video not found: {video}")
    if video.suffix.lower() not in VIDEO_EXTENSIONS:
        raise ValueError(f"unsupported video extension: {video.suffix}")

    if transcript:
        transcript = transcript.expanduser().resolve()
        if not transcript.is_file():
            raise ValueError(f"transcript not found: {transcript}")
        transcript_candidates = [transcript]
    else:
        parent = video.parent
        stem = video.stem
        transcript_candidates = [
            parent / f"{stem}.srt", parent / f"{stem}.ass",
            parent / f"{stem}_subtitled.srt", parent / f"{stem}_subtitled.ass",
        ]
        transcript_candidates.extend(sorted(parent.glob("*_subtitled.srt")))
        transcript_candidates.extend(sorted(parent.glob("*_subtitled.ass")))

    script_candidates = sorted(video.parent.glob("*.md")) + sorted(video.parent.glob("*.txt"))
    transcripts = unique_paths(transcript_candidates)
    scripts = unique_paths(script_candidates)
    exact = [p for p in transcripts if Path(p).stem in {video.stem, f"{video.stem}_subtitled"}]

    transcript_path = exact[0] if len(exact) == 1 else None
    stats = inspect_srt(Path(transcript_path)) if transcript_path and Path(transcript_path).suffix.lower() == ".srt" else None
    return {
        "inputType": "video+subtitle" if transcript_path else "video-only",
        "videoPath": str(video),
        "videoStem": video.stem,
        "durationSeconds": duration_seconds(video),
        "exactTranscript": transcript_path,
        "transcriptCandidates": transcripts,
        "transcriptStats": stats,
        "videoCandidates": [str(video)],
        "scriptCandidates": scripts,
        "needsUserChoice": not exact and len(transcripts) + len(scripts) != 1,
        "publisherReady": True,
    }


def discover_source(source: Path, video: Path | None = None, transcript: Path | None = None) -> dict:
    source = source.expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"input not found: {source}")
    suffix = source.suffix.lower()
    if suffix in VIDEO_EXTENSIONS:
        return discover(source, transcript)
    if suffix not in SUBTITLE_EXTENSIONS:
        raise ValueError(f"unsupported input extension: {source.suffix}")

    if video:
        video = video.expanduser().resolve()
        if not video.is_file() or video.suffix.lower() not in VIDEO_EXTENSIONS:
            raise ValueError(f"video not found or unsupported: {video}")
        videos = [str(video)]
    else:
        videos = video_candidates_for_subtitle(source)
    exact_video = videos[0] if len(videos) == 1 else None
    parent = source.parent
    scripts = unique_paths(sorted(parent.glob("*.md")) + sorted(parent.glob("*.txt")))
    stats = inspect_srt(source) if suffix == ".srt" else None
    return {
        "inputType": "video+subtitle" if exact_video else "subtitle-only",
        "videoPath": exact_video,
        "videoStem": Path(exact_video).stem if exact_video else source.stem.removesuffix("_subtitled"),
        "durationSeconds": duration_seconds(Path(exact_video)) if exact_video else None,
        "exactTranscript": str(source),
        "transcriptCandidates": [str(source)],
        "transcriptStats": stats,
        "videoCandidates": videos,
        "scriptCandidates": scripts,
        "needsUserChoice": len(videos) > 1,
        "publisherReady": bool(exact_video),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input")
    parser.add_argument("--video")
    parser.add_argument("--transcript")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        if args.input:
            payload = discover_source(
                Path(args.input),
                Path(args.video) if args.video else None,
                Path(args.transcript) if args.transcript else None,
            )
        elif args.video:
            payload = discover(Path(args.video), Path(args.transcript) if args.transcript else None)
        else:
            parser.error("provide --input or --video")
    except ValueError as exc:
        parser.error(str(exc))
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).expanduser().resolve().write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

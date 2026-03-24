#!/usr/bin/env python3
import argparse
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = SKILL_DIR / "output"
TRANSCRIBE_PY = SKILL_DIR / "scripts" / "transcribe.py"


def run(cmd, *, cwd=None, capture=True):
    print("+", " ".join(shlex.quote(str(x)) for x in cmd), flush=True)
    result = subprocess.run(
        [str(x) for x in cmd],
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=capture,
    )
    if result.returncode != 0:
        if capture:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    return result


def ffprobe_duration(path: Path) -> float:
    result = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path,
    ])
    return float(result.stdout.strip())


def choose_prefix(video_id: str) -> str:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    safe_id = video_id or "video"
    return f"{stamp}-{safe_id}"


def ensure_dependencies():
    for cmd in ["yt-dlp", "ffmpeg", "ffprobe", "uv"]:
        result = subprocess.run(["bash", "-lc", f"command -v {shlex.quote(cmd)} >/dev/null 2>&1"])
        if result.returncode != 0:
            raise SystemExit(f"Missing required command: {cmd}")



def main():
    parser = argparse.ArgumentParser(description="Download audio with yt-dlp and transcribe it with FunASR")
    parser.add_argument("url", help="Video URL")
    parser.add_argument("-o", "--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory")
    parser.add_argument("-l", "--language", default="auto", choices=["auto", "zh", "en", "ja", "ko", "yue"])
    parser.add_argument("--chunk-size", type=int, default=30)
    parser.add_argument("--long-threshold", type=int, default=300, help="Use --long when audio duration >= this many seconds")
    args = parser.parse_args()

    ensure_dependencies()

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    meta = json.loads(run([
        "yt-dlp", "--dump-single-json", "--no-playlist", args.url
    ]).stdout)
    title = meta.get("title") or "video"
    video_id = meta.get("id") or "video"
    prefix = choose_prefix(video_id)

    audio_path = outdir / f"{prefix}.%(ext)s"
    downloaded = run([
        "yt-dlp",
        "-x",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "--no-playlist",
        "-o", str(audio_path),
        args.url,
    ])

    wav_path = outdir / f"{prefix}.wav"
    if not wav_path.exists():
        matches = sorted(outdir.glob(f"{prefix}.*"))
        wav_candidates = [p for p in matches if p.suffix.lower() == ".wav"]
        if wav_candidates:
            wav_path = wav_candidates[0]
        else:
            print(downloaded.stdout)
            raise SystemExit(f"Downloaded audio not found for prefix {prefix}")

    duration = ffprobe_duration(wav_path)
    transcript_path = outdir / f"{prefix}.transcript.txt"
    metadata_path = outdir / f"{prefix}.metadata.json"

    transcribe_cmd = [
        "uv", "run", str(TRANSCRIBE_PY), str(wav_path),
        "-o", str(transcript_path),
        "-l", args.language,
        "--chunk-size", str(args.chunk_size),
    ]
    if duration >= args.long_threshold:
        transcribe_cmd.append("--long")

    run(transcribe_cmd, cwd=SKILL_DIR, capture=False)

    payload = {
        "url": args.url,
        "title": title,
        "video_id": video_id,
        "duration_seconds": duration,
        "audio_path": str(wav_path),
        "transcript_path": str(transcript_path),
        "used_long_mode": duration >= args.long_threshold,
        "language": args.language,
        "chunk_size": args.chunk_size,
    }
    metadata_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== DONE ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

---
name: ytdlp-asr-funasr
description: Download audio from a video URL with yt-dlp and transcribe it with FunASR. Use when the user shares a YouTube/Bilibili/other yt-dlp-supported video link and wants the spoken content, transcript, summary, subtitles, or a "watch this video" style analysis based on actual audio instead of page text.
---

# yt-dlp + FunASR transcript

Turn a video URL into text: download audio with `yt-dlp`, transcribe it with FunASR, then summarize or answer questions from the transcript.

## Workflow

1. Run `scripts/url_to_transcript.py` with the target URL.
2. Read the generated `*.metadata.json` first to confirm title, paths, duration, and whether long-audio mode was used.
3. Read `*.transcript.txt` and use that text for summaries, Q&A, timestamps, and note extraction.
4. If the user needs visual details, use a separate video-frame workflow; do not pretend an audio-only transcript includes visual analysis.

## Quick usage

```bash
uv run {skillDir}/scripts/url_to_transcript.py "https://www.youtube.com/watch?v=..."
```

Common options:

```bash
# Force language
uv run {skillDir}/scripts/url_to_transcript.py URL -l zh

# Custom output directory
uv run {skillDir}/scripts/url_to_transcript.py URL -o ./output

# Adjust long-audio behavior
uv run {skillDir}/scripts/url_to_transcript.py URL --long-threshold 180 --chunk-size 20
```

## Output files

Default output directory: `{skillDir}/output/`

- `TIMESTAMP-VIDEOID.wav`: extracted audio
- `TIMESTAMP-VIDEOID.transcript.txt`: transcript text
- `TIMESTAMP-VIDEOID.metadata.json`: metadata (title, duration, paths, long mode)

Always inspect metadata before picking the transcript file.

## Environment

Required external commands:

- `uv`
- `yt-dlp`
- `ffmpeg`
- `ffprobe`

Python dependencies are managed by `pyproject.toml` and installed automatically by `uv run`.

## Runtime details

- `yt-dlp --dump-single-json` is used first to get title and video ID.
- Output names use `timestamp + video_id` to avoid collisions.
- Audio is downloaded as WAV for reliable transcription.
- Long audio automatically adds `--long` when duration exceeds `--long-threshold`.
- Transcription is handled by `scripts/transcribe.py` in the same skill.

## Failure handling

### yt-dlp fails

Check whether `yt-dlp` exists:

```bash
command -v yt-dlp
```

If the site is throttling or requires a newer extractor, inspect stderr and update `yt-dlp`.

### FunASR import fails

Install dependencies inside the skill directory:

```bash
uv sync
```

Then retry:

```bash
uv run {skillDir}/scripts/transcribe.py AUDIO.wav -o out.txt
```

### Output too long

Prefer summarizing the transcript instead of pasting the whole file. Quote only the relevant passages when needed.

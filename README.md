# ytdlp-asr-funasr

一个可直接放进 OpenClaw / Codex 工作区使用的 Skill：

- 用 `yt-dlp` 下载 YouTube / Bilibili / 其他受支持站点的音频
- 用 FunASR (SenseVoiceSmall) 转文字
- 输出 transcript + metadata，方便后续总结、问答、做字幕

## 安装

### 方式 1：直接克隆

```bash
git clone https://github.com/Enter-tainer/ytdlp-asr-funasr.git
mkdir -p ~/.openclaw/workspace/skills
cp -R ytdlp-asr-funasr/skill ~/.openclaw/workspace/skills/ytdlp-asr-funasr
cd ~/.openclaw/workspace/skills/ytdlp-asr-funasr
uv sync
```

### 方式 2：用 GitHub 一行安装

```bash
mkdir -p ~/.openclaw/workspace/skills/ytdlp-asr-funasr
curl -L https://github.com/Enter-tainer/ytdlp-asr-funasr/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 -C ~/.openclaw/workspace/skills/ytdlp-asr-funasr ytdlp-asr-funasr-main/skill
cd ~/.openclaw/workspace/skills/ytdlp-asr-funasr
uv sync
```

## 系统依赖

需要先装好：

- `uv`
- `yt-dlp`
- `ffmpeg`（同时提供 `ffprobe`）

Ubuntu / Debian 示例：

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg yt-dlp
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 用法

```bash
cd ~/.openclaw/workspace/skills/ytdlp-asr-funasr
uv run scripts/url_to_transcript.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

输出默认在：

```text
output/
```

包含：

- `*.wav`
- `*.transcript.txt`
- `*.metadata.json`

## OpenClaw 触发说明

把 `skill/SKILL.md` 和 `skill/scripts/*` 放到工作区的：

```text
<workspace>/skills/ytdlp-asr-funasr/
```

然后开启新会话即可被自动触发。

## 许可证

MIT

# ytdlp-asr-funasr

一个兼容 [vercel-labs/skills](https://github.com/vercel-labs/skills) 安装方式的 Agent Skill：

- 用 `yt-dlp` 下载 YouTube / Bilibili / 其他受支持站点的音频
- 用 FunASR (SenseVoiceSmall) 转文字
- 输出 transcript + metadata，方便后续总结、问答、做字幕

## 安装

### 方式 1：像 Vercel Skills 那样安装（推荐）

安装到 OpenClaw：

```bash
npx skills add Enter-tainer/ytdlp-asr-funasr -a openclaw
```

安装到 Codex：

```bash
npx skills add Enter-tainer/ytdlp-asr-funasr -a codex
```

安装到所有检测到的 agent：

```bash
npx skills add Enter-tainer/ytdlp-asr-funasr
```

列出仓库里的 skill：

```bash
npx skills add Enter-tainer/ytdlp-asr-funasr --list
```

### 方式 2：直接克隆

```bash
git clone https://github.com/Enter-tainer/ytdlp-asr-funasr.git
mkdir -p ~/.openclaw/workspace/skills
cp -R ytdlp-asr-funasr/skills/ytdlp-asr-funasr ~/.openclaw/workspace/skills/ytdlp-asr-funasr
cd ~/.openclaw/workspace/skills/ytdlp-asr-funasr
uv sync
```

安装完成后，在目标 skill 目录里执行一次 `uv sync`，让 FunASR 依赖就位。

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

把 `skills/ytdlp-asr-funasr/` 放到工作区的：

```text
<workspace>/skills/ytdlp-asr-funasr/
```

然后开启新会话即可被自动触发。

## 许可证

MIT

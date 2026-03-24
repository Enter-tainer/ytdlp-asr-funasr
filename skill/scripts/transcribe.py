#!/usr/bin/env python3
"""
FunASR 语音转文字脚本
支持长音频自动切片处理
"""
import argparse
import os
import sys
import time
import math
from pathlib import Path

def ensure_model():
    """确保模型已加载（从已配置的环境中导入）"""
    try:
        from funasr import AutoModel
        return AutoModel
    except ImportError:
        print("❌ 错误: 未找到 FunASR 依赖")
        print("请先在当前 skill 目录运行 uv sync")
        sys.exit(1)

def format_time(seconds):
    """将秒数转换为 HH:MM:SS 格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def transcribe_file(audio_path, model=None, language="auto", chunk_size=30):
    """
    转录单个音频文件
    
    Args:
        audio_path: 音频文件路径
        model: 预加载的模型实例（可选）
        language: 语言代码 (zh/en/ja/ko/yue/auto)
        chunk_size: 切片大小（秒），用于长音频
    
    Returns:
        dict: 包含 text 和 segments 的结果
    """
    AutoModel = ensure_model()
    
    # 加载模型（如果未提供）
    if model is None:
        print(f"⏳ 加载模型...")
        start = time.time()
        model = AutoModel(
            model="iic/SenseVoiceSmall",
            device="cpu",
            disable_update=True,
        )
        print(f"✅ 模型加载完成 ({time.time()-start:.2f}s)")
    
    print(f"🎙️ 识别: {audio_path}")
    
    # 获取音频时长
    try:
        import torchaudio
        # 兼容不同版本的 torchaudio
        try:
            info = torchaudio.info(audio_path)
            if hasattr(info, 'num_frames'):
                duration = info.num_frames / info.sample_rate
            elif hasattr(info, 'sample_rate') and isinstance(info, tuple):
                # 某些版本返回 (sample_rate, num_frames)
                duration = info[1] / info[0]
            else:
                duration = None
        except TypeError:
            # torchaudio 2.0+ 版本
            from torchaudio import backend
            info = torchaudio.info(audio_path)
            duration = info.num_frames / info.sample_rate
        if duration:
            print(f"   音频时长: {format_time(duration)}")
    except Exception as e:
        duration = None
        print(f"   音频时长: 未知")
    
    # 执行识别
    start = time.time()
    
    kwargs = {"input": audio_path}
    if language != "auto":
        kwargs["language"] = language
    
    result = model.generate(**kwargs)
    elapsed = time.time() - start
    
    text = result[0]["text"] if result else ""
    
    # 提取实际文本（移除标签）
    clean_text = text
    for tag in ["<|zh|>", "<|en|>", "<|ja|>", "<|ko|>", "<|yue|>", 
                "<|NEUTRAL|>", "<|HAPPY|>", "<|SAD|>", "<|ANGRY|>",
                "<|Speech|>", "<|woitn|>"]:
        clean_text = clean_text.replace(tag, "")
    
    rtf = elapsed / duration if duration else 0
    print(f"   识别耗时: {elapsed:.2f}s (RTF: {rtf:.3f})")
    print(f"   识别结果: {clean_text[:100]}{'...' if len(clean_text) > 100 else ''}")
    
    return {
        "text": clean_text.strip(),
        "raw_text": text,
        "duration": duration,
        "elapsed": elapsed,
        "rtf": rtf,
    }

def transcribe_long_audio(audio_path, output_path=None, language="auto", chunk_size=30):
    """
    转录长音频（自动切片处理）
    
    Args:
        audio_path: 音频文件路径
        output_path: 输出文本文件路径（可选）
        language: 语言代码
        chunk_size: 每个切片的长度（秒）
    """
    import tempfile
    import subprocess
    
    AutoModel = ensure_model()
    
    print(f"\n{'='*60}")
    print(f"🎬 长音频转录")
    print(f"{'='*60}")
    print(f"文件: {audio_path}")
    print(f"切片大小: {chunk_size}秒")
    
    # 加载模型
    print(f"\n⏳ 加载模型...")
    start = time.time()
    model = AutoModel(
        model="iic/SenseVoiceSmall",
        device="cpu",
        disable_update=True,
    )
    print(f"✅ 模型加载完成 ({time.time()-start:.2f}s)")
    
    # 获取音频信息
    import soundfile as sf
    try:
        info = sf.info(audio_path)
        duration = info.duration
        sample_rate = info.samplerate
    except Exception:
        # Fallback to torchaudio if soundfile fails
        import torchaudio
        try:
            info = torchaudio.info(audio_path)
            if hasattr(info, 'num_frames'):
                duration = info.num_frames / info.sample_rate
                sample_rate = info.sample_rate
            elif hasattr(info, 'sample_rate') and isinstance(info, tuple):
                duration = info[1] / info[0]
                sample_rate = info[0]
            else:
                duration, sample_rate = None, 16000
        except TypeError:
            from torchaudio import backend
            info = torchaudio.info(audio_path)
            duration = info.num_frames / info.sample_rate
            sample_rate = info.sample_rate
    
    print(f"\n📊 音频信息:")
    print(f"   时长: {format_time(duration)}")
    print(f"   采样率: {sample_rate}Hz")
    
    # 计算切片
    num_chunks = math.ceil(duration / chunk_size)
    print(f"   切片数: {num_chunks}")
    
    # 逐段识别
    full_text = []
    total_elapsed = 0
    
    print(f"\n🔄 开始识别...")
    for i in range(num_chunks):
        start_sec = i * chunk_size
        end_sec = min((i + 1) * chunk_size, duration)
        
        print(f"\n   切片 {i+1}/{num_chunks} [{format_time(start_sec)} - {format_time(end_sec)}]")
        
        # 提取切片
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # 使用 ffmpeg 提取切片
            cmd = [
                "ffmpeg", "-y", "-i", audio_path,
                "-ss", str(start_sec),
                "-t", str(end_sec - start_sec),
                "-ar", "16000", "-ac", "1",
                tmp_path
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            
            # 识别
            result = transcribe_file(tmp_path, model=model, language=language)
            chunk_text = result["text"]
            total_elapsed += result["elapsed"]
            
            # 添加时间戳
            timestamp = format_time(start_sec)
            full_text.append(f"[{timestamp}] {chunk_text}")
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    # 合并结果
    final_text = "\n".join(full_text)
    
    print(f"\n{'='*60}")
    print(f"✅ 识别完成!")
    print(f"   总耗时: {total_elapsed:.2f}s")
    print(f"   平均RTF: {total_elapsed/duration:.3f}")
    print(f"{'='*60}")
    
    # 保存结果
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# 语音转文字结果\n\n")
            f.write(f"源文件: {audio_path}\n")
            f.write(f"时长: {format_time(duration)}\n")
            f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write(final_text)
        print(f"\n💾 结果已保存: {output_path}")
    
    return final_text

def main():
    parser = argparse.ArgumentParser(description="FunASR 语音转文字")
    parser.add_argument("audio", help="音频文件路径")
    parser.add_argument("-o", "--output", help="输出文本文件路径")
    parser.add_argument("-l", "--language", default="auto", 
                       choices=["auto", "zh", "en", "ja", "ko", "yue"],
                       help="语言 (默认: auto)")
    parser.add_argument("--chunk-size", type=int, default=30,
                       help="长音频切片大小(秒) (默认: 30)")
    parser.add_argument("--long", action="store_true",
                       help="启用长音频模式（自动切片）")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.audio):
        print(f"❌ 错误: 文件不存在: {args.audio}")
        sys.exit(1)
    
    if args.long:
        # 长音频模式
        result = transcribe_long_audio(
            args.audio, 
            output_path=args.output,
            language=args.language,
            chunk_size=args.chunk_size
        )
    else:
        # 普通模式
        result = transcribe_file(args.audio, language=args.language)
        
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result["text"])
            print(f"\n💾 结果已保存: {args.output}")

if __name__ == "__main__":
    main()

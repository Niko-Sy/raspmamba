import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from pydub import AudioSegment

def export_mp3(parent, temp_wav_path):
    """
    将当前MIDI导出为MP3格式。
    参数:
        parent: 父窗口（用于弹窗）
        temp_wav_path: 已生成的WAV文件路径
    """
    if not temp_wav_path or not os.path.exists(temp_wav_path):
        QMessageBox.warning(parent, "导出失败", "请先打开或生成MIDI文件并播放一次！", QMessageBox.StandardButton.Ok)
        return

    if not check_ffmpeg():
        show_ffmpeg_tip(parent)
        return

    file_path, _ = QFileDialog.getSaveFileName(parent, "导出为MP3", "", "MP3文件 (*.mp3)")
    if not file_path:
        return
    if not file_path.lower().endswith('.mp3'):
        file_path += '.mp3'
    try:
        audio = AudioSegment.from_wav(temp_wav_path)
        audio.export(file_path, format="mp3")
        QMessageBox.information(parent, "导出成功", f"MP3已保存到:\n{file_path}", QMessageBox.StandardButton.Ok)
    except Exception as e:
        QMessageBox.critical(parent, "导出失败", f"导出MP3时出错:\n{str(e)}", QMessageBox.StandardButton.Ok)

def export_wav(parent, temp_wav_path):
    """
    另存为WAV格式（辅助功能）。
    """
    if not temp_wav_path or not os.path.exists(temp_wav_path):
        QMessageBox.warning(parent, "导出失败", "请先打开或生成MIDI文件并播放一次！", QMessageBox.StandardButton.Ok)
        return

    file_path, _ = QFileDialog.getSaveFileName(parent, "导出为WAV", "", "WAV文件 (*.wav)")
    if not file_path:
        return
    if not file_path.lower().endswith('.wav'):
        file_path += '.wav'
    try:
        # 直接复制临时WAV
        import shutil
        shutil.copy(temp_wav_path, file_path)
        QMessageBox.information(parent, "导出成功", f"WAV已保存到:\n{file_path}", QMessageBox.StandardButton.Ok)
    except Exception as e:
        QMessageBox.critical(parent, "导出失败", f"导出WAV时出错:\n{str(e)}", QMessageBox.StandardButton.Ok)

def check_ffmpeg():
    """
    检查ffmpeg是否可用，pydub导出mp3需要ffmpeg支持。
    """
    from pydub.utils import which
    return which("ffmpeg") is not None

def show_ffmpeg_tip(parent):
    """
    如果未检测到ffmpeg，弹窗提示用户。
    """
    QMessageBox.warning(
        parent,
        "缺少ffmpeg",
        "导出MP3需要安装ffmpeg。\n请访问 https://ffmpeg.org/ 下载并配置环境变量。",
        QMessageBox.StandardButton.Ok
    )

def preview_mp3(temp_wav_path):
    """
    简单预览WAV（或MP3）文件，调用系统播放器。
    """
    if not temp_wav_path or not os.path.exists(temp_wav_path):
        return
    import subprocess, sys
    if sys.platform.startswith('win'):
        os.startfile(temp_wav_path)
    elif sys.platform.startswith('darwin'):
        subprocess.call(['open', temp_wav_path])
    else:
        subprocess.call(['xdg-open', temp_wav_path])

def get_audio_duration(audio_path):
    """
    获取音频文件时长（秒）。
    """
    try:
        audio = AudioSegment.from_file(audio_path)
        return audio.duration_seconds
    except Exception:
        return None

def convert_wav_to_mp3(wav_path, mp3_path):
    """
    直接转换WAV为MP3，不弹窗。
    """
    try:
        audio = AudioSegment.from_wav(wav_path)
        audio.export(mp3_path, format="mp3")
        return True
    except Exception:
        return False

def get_audio_bitrate(audio_path):
    """
    获取音频比特率（kbps）。
    """
    try:
        audio = AudioSegment.from_file(audio_path)
        return audio.frame_rate
    except Exception:
        return None
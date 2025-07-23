from PyQt5.QtWidgets import QMessageBox
import miditoolkit
import os

def show_midi_info(parent, midi_path):
    """
    弹窗显示MIDI文件的详细信息。
    参数:
        parent: 父窗口（用于弹窗）
        midi_path: MIDI文件路径
    """
    # 文件存在性检查
    if not midi_path or not os.path.exists(midi_path):
        QMessageBox.critical(parent, "文件错误", "未找到MIDI文件，请先选择或生成MIDI文件。", QMessageBox.StandardButton.Ok)
        return

    # 文件格式检查
    if not midi_path.lower().endswith('.mid') and not midi_path.lower().endswith('.midi'):
        QMessageBox.critical(parent, "文件格式错误", "请选择MIDI格式文件（.mid/.midi）。", QMessageBox.StandardButton.Ok)
        return

    try:
        midi = miditoolkit.MidiFile(midi_path)
    except Exception as e:
        QMessageBox.critical(parent, "读取失败", f"无法读取MIDI文件:\n{str(e)}", QMessageBox.StandardButton.Ok)
        return

    info = []
    info.append(f"文件名: {os.path.basename(midi_path)}")
    info.append(f"文件路径: {midi_path}")
    info.append(f"格式类型: {midi.type}")
    info.append(f"Ticks Per Beat: {midi.ticks_per_beat}")
    info.append(f"音轨数: {len(midi.instruments)}")
    info.append(f"总音符数: {sum(len(track.notes) for track in midi.instruments)}")
    info.append(f"总控制器事件数: {sum(len(track.control_changes) for track in midi.instruments)}")
    info.append(f"总节拍事件数: {len(midi.tempo_changes)}")
    info.append(f"总拍号事件数: {len(midi.time_signature_changes)}")
    info.append(f"总调号事件数: {len(midi.key_signature_changes)}")
    info.append(f"总歌词事件数: {sum(len(track.lyrics) for track in midi.instruments)}")
    info.append(f"总marker事件数: {len(midi.markers)}")
    try:
        end_time = midi.get_end_time()
        info.append(f"总长度（秒）: {end_time:.2f}")
    except Exception:
        info.append("总长度（秒）: 计算失败")

    # 显示每个音轨的详细信息
    for idx, track in enumerate(midi.instruments):
        info.append(f"\n音轨{idx+1}:")
        info.append(f"  名称: {track.name if track.name else '(无)'}")
        info.append(f"  程序号(乐器): {track.program}")
        info.append(f"  是否鼓组: {'是' if track.is_drum else '否'}")
        info.append(f"  音符数: {len(track.notes)}")
        info.append(f"  控制器事件数: {len(track.control_changes)}")
        info.append(f"  歌词数: {len(track.lyrics)}")
        # 检查音符范围
        if track.notes:
            min_pitch = min(n.pitch for n in track.notes)
            max_pitch = max(n.pitch for n in track.notes)
            info.append(f"  音高范围: {min_pitch} ~ {max_pitch}")
            min_vel = min(n.velocity for n in track.notes)
            max_vel = max(n.velocity for n in track.notes)
            info.append(f"  力度范围: {min_vel} ~ {max_vel}")
        else:
            info.append("  无音符")
        # 检查控制器类型
        cc_types = set(cc.number for cc in track.control_changes)
        if cc_types:
            info.append(f"  控制器类型: {sorted(list(cc_types))}")
        # 检查歌词内容
        if track.lyrics:
            info.append(f"  部分歌词: {', '.join(l.text for l in track.lyrics[:3])} ...")

    # 显示节拍信息
    if midi.tempo_changes:
        info.append("\n节拍变化:")
        for t in midi.tempo_changes:
            try:
                bpm = 60_000_000 / t.tempo
            except Exception:
                bpm = "未知"
            info.append(f"  时间: {t.time}，BPM: {bpm}")

    # 显示拍号信息
    if midi.time_signature_changes:
        info.append("\n拍号变化:")
        for ts in midi.time_signature_changes:
            info.append(f"  时间: {ts.time}，拍号: {ts.numerator}/{ts.denominator}")

    # 显示调号信息
    if midi.key_signature_changes:
        info.append("\n调号变化:")
        for ks in midi.key_signature_changes:
            info.append(f"  时间: {ks.time}，调号: {ks.key_number}")

    # 检查是否有空音轨
    empty_tracks = [i+1 for i, tr in enumerate(midi.instruments) if len(tr.notes) == 0]
    if empty_tracks:
        info.append(f"\n警告: 以下音轨无音符: {empty_tracks}")

    # 检查是否有超长音符
    for idx, tr in enumerate(midi.instruments):
        for n in tr.notes:
            if n.end - n.start > midi.ticks_per_beat * 16:
                info.append(f"\n警告: 音轨{idx+1}存在超长音符，起止tick: {n.start}-{n.end}")

    # 检查是否有重叠音符
    for idx, tr in enumerate(midi.instruments):
        notes = sorted(tr.notes, key=lambda n: n.start)
        for i in range(1, len(notes)):
            if notes[i].start < notes[i-1].end:
                info.append(f"\n警告: 音轨{idx+1}存在重叠音符，tick: {notes[i-1].start}-{notes[i-1].end} 与 {notes[i].start}-{notes[i].end}")
                break

    # 检查是否有异常BPM
    if midi.tempo_changes:
        bpms = [60_000_000 / t.tempo for t in midi.tempo_changes if t.tempo > 0]
        if bpms and (min(bpms) < 30 or max(bpms) > 300):
            info.append(f"\n警告: 存在异常BPM，范围: {min(bpms):.2f} ~ {max(bpms):.2f}")

    # 检查是否有异常拍号
    if midi.time_signature_changes:
        for ts in midi.time_signature_changes:
            if ts.numerator > 12 or ts.denominator > 16:
                info.append(f"\n警告: 存在异常拍号: {ts.numerator}/{ts.denominator}")

    # 检查是否有marker
    if midi.markers:
        info.append("\nMarkers:")
        for m in midi.markers[:5]:
            info.append(f"  {m.text} @ {m.time}")

    # 检查是否有meta文本
    if hasattr(midi, "text_events") and midi.text_events:
        info.append("\nMeta文本事件:")
        for t in midi.text_events[:5]:
            info.append(f"  {t.text} @ {t.time}")

    # 检查是否有sysex事件
    if hasattr(midi, "sysex_events") and midi.sysex_events:
        info.append(f"\n系统独占事件数: {len(midi.sysex_events)}")

    # 最终弹窗
    QMessageBox.information(parent, "MIDI文件信息", "\n".join(info), QMessageBox.StandardButton.Ok)
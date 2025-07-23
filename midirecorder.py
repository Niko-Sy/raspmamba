import time
import rtmidi
import mido
from mido import MidiFile, MidiTrack, Message
from threading import Lock
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MidiRecorder:
    """
    一个用于从 MIDI 输入设备录制 MIDI 事件并导出为 MIDI 文件的类。
    """
    def __init__(self, ticks_per_beat=480):
        """
        初始化 MidiRecorder。
        参数:
            ticks_per_beat (int): MIDI 文件中每拍的刻度数。
        """
        self.midiin = rtmidi.MidiIn()
        self.recording = False
        self.start_time = 0  # 录制开始的系统时间
        self.events = []  # 存储 (相对时间, MIDI 消息字节) 元组
        self.lock = Lock()  # 用于线程安全的事件列表访问
        self.ticks_per_beat = ticks_per_beat
        self.export_bpm = 120  # 导出时使用的 BPM，默认为 120

    def list_input_ports(self):
        """
        列出所有可用的 MIDI 输入端口。
        返回:
            list: 可用输入端口名称的列表。
        """
        return self.midiin.get_ports(encoding="auto")

    def start_recording(self, port_index=0):
        """
        开始从指定的 MIDI 输入端口录制。
        参数:
            port_index (int): 要打开的 MIDI 输入端口的索引。
        """
        if self.recording:
            logging.warning("录制已在进行中。")
            return

        ports = self.midiin.get_ports()
        if not ports:
            logging.warning("无可用输入端口，尝试开启虚拟端口。")
            try:
                self.midiin.open_virtual_port("My Virtual Input")
            except Exception as e:
                logging.error(f"无法开启虚拟端口: {e}")
                return
        elif port_index >= len(ports) or port_index < 0:
            logging.error(f"无效的端口索引: {port_index}。可用端口数量: {len(ports)}")
            return
        else:
            try:
                self.midiin.open_port(port_index)
            except Exception as e:
                logging.error(f"无法打开端口 {port_index}: {e}")
                return

        self.recording = True
        self.start_time = time.time()
        self.events = []
        # 设置回调函数
        self.midiin.set_callback(self._midi_callback)
        logging.info(f"开始录制，端口: {ports[port_index] if ports else '虚拟端口'}")

    def _midi_callback(self, event, data=None):
        """
        MIDI 事件回调函数。
        参数:
            event (tuple): 包含 MIDI 消息字节和 delta_time 的元组。
            data (any): 用户数据（未使用）。
        注意：rtmidi 的 delta_time 是相对于上一个事件的时间。
        为了简化，这里仍使用 time.time() 计算相对录制开始的时间。
        更精确的实现需要累积 delta_time 并转换为 MIDI ticks。
        """
        message, delta_time_rtmidi = event # delta_time_rtmidi 是 rtmidi 提供的相对时间
        
        if self.recording:
            # 计算相对于录制开始的精确时间戳
            current_relative_time = time.time() - self.start_time 
            with self.lock:
                self.events.append((current_relative_time, message))
            # logging.debug(f"录制事件: {message} @ {current_relative_time:.4f}s")

    def stop_recording(self):
        """
        停止录制并关闭 MIDI 端口。
        """
        if self.recording:
            self.recording = False
            self.midiin.cancel_callback()
            self.midiin.close_port()
            logging.info("录制已停止，MIDI 端口已关闭。")
        else:
            logging.info("当前没有进行中的录制。")

    def set_export_bpm(self, bpm):
        """
        设置导出 MIDI 文件时使用的 BPM。
        参数:
            bpm (int): 每分钟节拍数。
        """
        if 20 <= bpm <= 300: # 常用 BPM 范围
            self.export_bpm = bpm
            logging.info(f"导出 BPM 已设置为: {self.export_bpm}")
        else:
            logging.warning(f"无效的 BPM 值: {bpm}。BPM 应在 20 到 300 之间。")

    def export_to_midi(self, filename=None):
        """
        将录制的 MIDI 事件导出为 MIDI 文件。
        参数:
            filename (str, optional): 导出 MIDI 文件的路径。如果为 None，则不保存文件。
        返回:
            MidiFile or None: 导出的 MidiFile 对象，如果无录制内容则返回 None。
        """
        if not self.events:
            logging.info("无录制内容可导出！")
            return None

        mid = MidiFile(ticks_per_beat=self.ticks_per_beat)
        track = MidiTrack()
        mid.tracks.append(track)

        last_time = 0  # 上一个事件的相对时间 (秒)
        # 根据设定的 BPM 计算 tempo (微秒/拍)
        tempo = mido.bpm2tempo(self.export_bpm)

        # 对事件按时间排序，确保顺序正确
        sorted_events = sorted(self.events, key=lambda x: x[0])

        for event_time, message_bytes in sorted_events:
            delta_seconds = event_time - last_time
            
            # 将秒数转换为 MIDI 刻度，并四舍五入以减少精度损失
            # 确保 delta_ticks 至少为 0，避免负时间
            delta_ticks = max(0, int(mido.second2tick(delta_seconds, self.ticks_per_beat, tempo) + 0.5))
            
            try:
                msg = Message.from_bytes(message_bytes)
                # mido 消息的 time 参数是 delta ticks
                track.append(msg.copy(time=delta_ticks))
                last_time = event_time
            except Exception as e:
                logging.error(f"跳过无效 MIDI 消息: {message_bytes}, 错误: {e}")

        if filename:
            try:
                mid.save(filename)
                logging.info(f"已导出 MIDI 文件到: {filename}")
            except Exception as e:
                logging.error(f"保存 MIDI 文件失败: {e}")
                return None
        
        return mid

    def close(self):
        """
        显式关闭录音器，释放所有资源。
        推荐在应用程序关闭时调用此方法。
        """
        self.stop_recording()
        if self.midiin:
            self.midiin.close_port()
            del self.midiin
        logging.info("MidiRecorder 资源已清理。")

    def __del__(self):
        """
        析构函数，作为备用清理机制。
        推荐显式调用 close() 方法。
        """
        self.close()

# 示例用法 (仅用于测试 MidiRecorder 类，不包含 GUI 逻辑)
if __name__ == "__main__":
    recorder = MidiRecorder(ticks_per_beat=480)

    # 列出可用输入端口
    ports = recorder.list_input_ports()
    print("可用输入端口:", ports)

    if not ports:
        print("警告：没有检测到 MIDI 输入设备。请连接设备或确保驱动已安装。")
        print("将尝试使用虚拟端口进行录制。")
        port_to_open = -1 # 尝试打开虚拟端口
    else:
        print(f"选择端口 0 ({ports[0]}) 进行录制。")
        port_to_open = 0

    # 开始录制
    recorder.start_recording(port_index=port_to_open)
    print("录制中... 按 Ctrl+C 停止")

    try:
        # 录制 10 秒
        time.sleep(10)
    except KeyboardInterrupt:
        print("\n用户中断录制。")
    finally:
        # 停止录制
        recorder.stop_recording()
        print("录制结束。")

        # 设置导出 BPM
        recorder.set_export_bpm(100) # 尝试以 100 BPM 导出

        # 导出 MIDI 文件
        output_midi_file = "my_recording_updated.mid"
        exported_midi = recorder.export_to_midi(output_midi_file)

        if exported_midi:
            print(f"成功导出 MIDI 文件: {output_midi_file}")
            print(f"导出 MIDI 文件包含 {len(exported_midi.tracks[0].notes)} 个音符事件。")
        else:
            print("MIDI 文件导出失败或无录制内容。")
        
        # 显式清理资源
        recorder.close()
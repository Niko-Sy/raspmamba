import time
import rtmidi
import mido
from mido import MidiFile, MidiTrack, Message
from threading import Lock

class MidiRecorder:
    def __init__(self, ticks_per_beat=480):
        self.midiin = rtmidi.MidiIn()  # ✅ 正确类名
        self.recording = False
        self.start_time = 0
        self.events = []
        self.lock = Lock()
        self.ticks_per_beat = ticks_per_beat

    def list_input_ports(self):
        return self.midiin.get_ports(encoding="auto")

    def start_recording(self, port_index=0):
        if not self.recording:
            self.recording = True
            self.start_time = time.time()
            self.events = []

            # 设置回调函数
            self.midiin.set_callback(self._midi_callback)

            ports = self.midiin.get_ports()
            if ports:
                self.midiin.open_port(0)
            else:
                print("警告：无可用输入端口，开启虚拟端口。")
                self.midiin.open_virtual_port("My Virtual Input")

    def _midi_callback(self, event, data=None):
        """回调函数格式需匹配库的要求"""
        message, delta_time = event
        if self.recording:
            with self.lock:
                self.events.append((time.time() - self.start_time, message))

    def stop_recording(self):
        if self.recording:
            self.recording = False
            self.midiin.cancel_callback()
            self.midiin.close_port()

    def export_to_midi(self):
        if not self.events:
            print("无录制内容！")
            return

        mid = MidiFile(ticks_per_beat=self.ticks_per_beat)
        track = MidiTrack()
        mid.tracks.append(track)

        last_time = 0
        for event in sorted(self.events, key=lambda x: x[0]):
            current_time = event[0]
            delta_seconds = current_time - last_time
            delta_ticks = int(mido.second2tick(delta_seconds, self.ticks_per_beat, mido.bpm2tempo(120)))
            message = event[1]

            try:
                msg = Message.from_bytes(message)
                track.append(msg.copy(time=delta_ticks))
                last_time = current_time
            except Exception as e:
                print(f"跳过无效消息: {message}, 错误: {e}")
            mid.save("/home/pi/Desktop/final_codes/output.mid")
        return mid
        # mid.save(filename)
        # print(f"已导出到 {filename}")

    def __del__(self):
        self.stop_recording()

if __name__ == "__main__":
    recorder = MidiRecorder()

    # 列出可用输入端口
    print("可用输入端口:", recorder.list_input_ports())

    # 开始录制（默认选第一个端口）
    recorder.start_recording()
    print("录制中... 按Ctrl+C停止")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        recorder.stop_recording()
        print("录制结束")

    # 导出MIDI文件
    recorder.export_to_midi("my_recording.mid")

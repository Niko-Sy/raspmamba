import os
from PyQt5 import QtCore, QtGui, QtWidgets
from miditoolkit import MidiFile
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsRectItem, QGraphicsView, QGraphicsLineItem, QMessageBox, QFileDialog
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush
import pygame
import pygame.midi
import time
import tempfile
from midi2audio import FluidSynth
from pathlib import Path
from midirecorder import MidiRecorder
from rollview import PianoRollView

recorder = MidiRecorder()
class Ui_MainWindow(object):
    def __init__(self):
        self.graphicsView = None
        self.current_midi = None
        self.midi_file_path = None
        self.is_playing = False
        self.is_recording = False
        self.midi_duration = 0
        self.current_time = 0
        
        self.update_timer_progress = QtCore.QTimer()
        self.update_timer_progress.timeout.connect(self.update_playback_progress)
        self.update_timer_recorder = QtCore.QTimer()
        self.update_timer_recorder.timeout.connect(self.update_recorder_progress)
        self.midi_events = []
        self.input_ports=recorder.list_input_ports()
        self.selected_port=0
        # print(self.input_ports)
        
        self.newfile = "./output/output.mid"
        self.soundfont_path = "./soundfont/GeneralUser-GS.sf2"
        self.fluidsynth_path = "./fluidsynth-2.4.3/bin/fluidsynth.exe"

    def setupUi(self, MainWindow):
        MainWindow.setObjectName('Mainwindow')
        MainWindow.resize(802, 527)
        MainWindow.setStyleSheet("")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.columnView = QtWidgets.QColumnView(self.centralwidget)
        self.columnView.setGeometry(QtCore.QRect(0, 0, 801, 621))
        self.columnView.setStyleSheet("background-color:rgb(197, 197, 197);")
        self.columnView.setObjectName("columnView")
        self.verticalSlider = QtWidgets.QSlider(self.centralwidget)
        self.verticalSlider.setGeometry(QtCore.QRect(700, 65, 31, 254))
        self.verticalSlider.setMaximum(100)
        self.verticalSlider.setProperty("value", 50)
        self.verticalSlider.setOrientation(QtCore.Qt.Vertical)
        self.verticalSlider.setObjectName("verticalSlider")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(695, 330, 41, 21))
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(675, 40, 81, 20))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.verticalSlider_2 = QtWidgets.QSlider(self.centralwidget)
        self.verticalSlider_2.setGeometry(QtCore.QRect(630, 65, 31, 254))
        self.verticalSlider_2.setMouseTracking(False)
        self.verticalSlider_2.setMaximum(100)
        self.verticalSlider_2.setProperty("value", 50)
        self.verticalSlider_2.setTracking(True)
        self.verticalSlider_2.setOrientation(QtCore.Qt.Vertical)
        self.verticalSlider_2.setObjectName("verticalSlider_2")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(625, 330, 41, 21))
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(614, 40, 61, 20))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.label_4.setFont(font)
        self.label_4.setFrameShadow(QtWidgets.QFrame.Plain)
        self.label_4.setTextFormat(QtCore.Qt.AutoText)
        self.label_4.setAlignment(QtCore.Qt.AlignCenter)
        self.label_4.setWordWrap(True)
        self.label_4.setIndent(-1)
        self.label_4.setOpenExternalLinks(False)
        self.label_4.setObjectName("label_4")
        # self.graphicsView = PianoRollView(self.centralwidget)
        # self.graphicsView.setGeometry(QtCore.QRect(30, 20, 561, 291))
        # self.graphicsView.setStyleSheet("border-radius:10px;\nbackground-color: rgb(232, 232, 232)")
        # self.graphicsView.setObjectName("graphicsView")
        self.graphicsView = PianoRollView(self.centralwidget)
        self.graphicsView.setGeometry(QtCore.QRect(30, 20, 561, 291))
        self.graphicsView.setObjectName("graphicsView")
        
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(39, 390, 111, 42))
        font = QtGui.QFont()
        font.setFamily("楷体")
        font.setPointSize(10)
        font.setItalic(False)
        self.pushButton.setFont(font)
        self.pushButton.setStyleSheet("background-color: rgba(170, 0, 0,200);\n"
                                      "color: rgb(255, 255, 255);\n"
                                      "border-radius:10px;\n"
                                      "border:1px solid #000000;\n"
                                      "font: 10pt \"楷体\";\n"
                                      "font-weight:900;\n"
                                      "height:50px;")
        self.pushButton.setAutoDefault(False)
        self.pushButton.setObjectName("pushButton")
        
        self.pushButton_3 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_3.setGeometry(QtCore.QRect(590, 390, 171, 42))
        self.pushButton_3.setStyleSheet("""
    QPushButton {
        background-color: #efefef;
        color: rgb(0,0,0);
        border-radius:20px;
        border:1px solid #000000;
        font: 10pt \"楷体\";
        
    }  
    QPushButton:pressed {
        background-color: #eaeaea;
    }""")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../final_codes/toright.png"), QtGui.QIcon.Normal,
                       QtGui.QIcon.Off)
        self.pushButton_3.setIcon(icon)
        self.pushButton_3.setIconSize(QtCore.QSize(32, 32))
        self.pushButton_3.setObjectName("pushButton_3")
        
        self.pushButton_4 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_4.setEnabled(True)
        self.pushButton_4.setGeometry(QtCore.QRect(215, 390, 91, 42))
        self.pushButton_4.setStyleSheet("QPushButton {\n"
                                        "                height:36px;border-radius:18px;background-color: #eaeaea;\n"
                                        "    \n"
                                        "            }\n"
                                        "            QPushButton:pressed {background-color: #f0f0f0;}")
        icon = QtGui.QIcon.fromTheme("media-playback-start")
        self.pushButton_4.setIcon(icon)
        self.pushButton_4.setIconSize(QtCore.QSize(24, 24))
        self.pushButton_4.setObjectName("pushButton_4")
        
        self.pushButton_6 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_6.setGeometry(QtCore.QRect(315, 390, 91, 42))
        self.pushButton_6.setStyleSheet("QPushButton {\n"
                                        "                height:36px;border-radius:18px;background-color: #eaeaea;\n"
                                        "    \n"
                                        "            }\n"
                                        "            QPushButton:pressed {background-color: #f0f0f0;}")
        icon = QtGui.QIcon.fromTheme("media-playback-stop")
        self.pushButton_6.setIcon(icon)
        self.pushButton_6.setIconSize(QtCore.QSize(24, 24))
        self.pushButton_6.setObjectName("pushButton_6")
        
        self.label_6 = QtWidgets.QLabel(self.centralwidget)
        self.label_6.setGeometry(QtCore.QRect(50, 342, 140, 20))
        self.label_6.setAlignment(QtCore.Qt.AlignLeft)
        self.label_6.setObjectName("label_6")
        
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(40, 322, 541, 53))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalSlider = QtWidgets.QSlider(self.verticalLayoutWidget)
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider.setMouseTracking(False)
        self.horizontalSlider.setMaximum(1000)
        self.horizontalSlider.setSingleStep(1)
        self.horizontalSlider.setPageStep(20)
        self.horizontalSlider.setTracking(True)
        self.horizontalSlider.setObjectName("horizontalSlider")
        self.verticalLayout.addWidget(self.horizontalSlider)
        self.label_5 = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label_5.setAlignment(QtCore.Qt.AlignCenter)
        self.label_5.setObjectName("label_5")
        self.verticalLayout.addWidget(self.label_5)
        
        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setEnabled(False)
        self.progressBar.setGeometry(QtCore.QRect(587, 450, 181, 21))
        self.progressBar.setAutoFillBackground(False)
        self.progressBar.setStyleSheet("border-radius:10px;background-color:#efefef;")
        self.progressBar.setProperty("value", 10)
        self.progressBar.setAlignment(QtCore.Qt.AlignCenter)
        self.progressBar.setTextVisible(True)
        self.progressBar.setObjectName("progressBar")
        
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setGeometry(QtCore.QRect(280, 340, 131, 20))
        self.label_5.setObjectName("label_5")
        
        MainWindow.setCentralWidget(self.centralwidget)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 802, 31))
        self.menuBar.setStyleSheet("background-color:rgb(220,220,220);")
        self.menuBar.setObjectName("menuBar")
        self.menuTools = QtWidgets.QMenu(self.menuBar)
        self.menuTools.setEnabled(True)
        self.menuTools.setGeometry(QtCore.QRect(317, 201, 200, 231))
        self.menuTools.setStyleSheet("")
        self.menuTools.setToolTipsVisible(False)
        self.menuTools.setObjectName("menuTools")
        self.menuTrack = QtWidgets.QMenu(self.menuBar)
        self.menuTrack.setObjectName("menuTrack")
        self.update_track_menu()  # 初始化为空音轨菜单
        self.menuTool = QtWidgets.QMenu(self.menuBar)
        self.menuTool.setObjectName("menuTool")
        self.menuAbout = QtWidgets.QMenu(self.menuBar)
        self.menuAbout.setObjectName("menuAbout")
        self.menuHelp = QtWidgets.QMenu(self.menuBar)
        self.menuHelp.setObjectName("menuHelp")
        
        MainWindow.setMenuBar(self.menuBar)
        self.actionNew_file = QtWidgets.QAction(MainWindow)
        self.actionNew_file.setObjectName("actionNew_file")
        self.actionOpen_file = QtWidgets.QAction(MainWindow)
        self.actionOpen_file.setObjectName("actionOpen_file")
        self.actionSave_file = QtWidgets.QAction(MainWindow)
        self.actionSave_file.setObjectName("actionSave_file")
        self.actionSave_file_as = QtWidgets.QAction(MainWindow)
        self.actionSave_file_as.setObjectName("actionSaveas_file")
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionExit_2 = QtWidgets.QAction(MainWindow)
        self.actionExit_2.setObjectName("actionExit_2")
        self.actionExit_3 = QtWidgets.QAction(MainWindow)
        self.actionExit_3.setObjectName("actionExit_3")
        #self.actionTrack_0 = QtWidgets.QAction(MainWindow)
        #self.actionTrack_0.setObjectName("actionTrack_0")
        self.action1 = QtWidgets.QAction(MainWindow)
        self.action1.setObjectName("action1")
        
        self.menuTools.addAction(self.actionNew_file)
        self.menuTools.addAction(self.actionOpen_file)
        self.menuTools.addAction(self.actionSave_file)
        self.menuTools.addAction(self.actionSave_file_as)
        self.menuTools.addAction(self.actionExit)
        self.menuTools.addAction(self.actionExit_3)
        #self.menuTrack.addAction(self.actionTrack_0)
        self.menuTool.addAction(self.action1)
        
        self.menuBar.addAction(self.menuTools.menuAction())
        self.menuBar.addAction(self.menuTrack.menuAction())
        self.menuBar.addAction(self.menuTool.menuAction())
        self.menuBar.addAction(self.menuAbout.menuAction())
        self.menuBar.addAction(self.menuHelp.menuAction())
        
        self.retranslateUi(MainWindow)
        self.horizontalSlider.setEnabled(False)
        self.progressBar.setVisible(False)
        self.verticalSlider.valueChanged['int'].connect(self.label.setNum)
        self.verticalSlider_2.valueChanged['int'].connect(self.label_3.setNum)
        self.pushButton_3.clicked.connect(self.progressBar.reset)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
        self.actionNew_file.triggered.connect(self.new_file)
        self.actionSave_file.triggered.connect(self.save_file)
        self.actionOpen_file.triggered.connect(self.open_midi_file)
        self.actionSave_file_as.triggered.connect(self.save_file_as)
        self.actionExit.triggered.connect(self.close_file)
        self.pushButton.clicked.connect(self.toggle_record)
        self.pushButton_4.clicked.connect(self.toggle_play_pause)
        self.pushButton_6.clicked.connect(self.stop_playback)
        self.horizontalSlider.sliderMoved.connect(self.on_slider_moved)
        self.horizontalSlider.sliderPressed.connect(self.on_slider_pressed)
        self.horizontalSlider.sliderReleased.connect(self.seek_playback)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "古韵调新"))
        self.label.setText(_translate("MainWindow", "50"))
        self.label_2.setText(_translate("MainWindow", "音量"))
        self.label_3.setText(_translate("MainWindow", "50"))
        self.label_4.setText(_translate("MainWindow", "融合度"))
        self.pushButton.setText(_translate("MainWindow", "开始录制"))
        self.pushButton_3.setText(_translate("MainWindow", "AI生成"))
        self.pushButton_4.setText(_translate("MainWindow", "播放"))
        self.pushButton_6.setText(_translate("MainWindow", "停止"))
        self.label_5.setText(_translate("MainWindow", "00:00 / 00:00"))
        self.label_6.setText(_translate("MainWindow", "请打开midi文件"))
        self.menuTools.setTitle(_translate("MainWindow", "  文件  "))
        self.menuTrack.setTitle(_translate("MainWindow", "  设备串口  "))
        self.menuTool.setTitle(_translate("MainWindow", "  工具  "))
        self.menuAbout.setTitle(_translate("MainWindow", "  关于 "))
        self.menuHelp.setTitle(_translate("MainWindow", "   帮助  "))
        self.actionNew_file.setText(_translate("MainWindow", "新建文件(N)"))
        self.actionOpen_file.setText(_translate("MainWindow", "打开文件(O)"))
        self.actionSave_file.setText(_translate("MainWindow", "保存文件(S)"))
        self.actionSave_file_as.setText(_translate("MainWindow", "另存为文件"))
        self.actionExit.setText(_translate("MainWindow", "关闭文件"))
        self.actionExit_2.setText(_translate("MainWindow", "关闭程序"))
        self.actionExit_3.setText(_translate("MainWindow", "关闭程序"))
        #self.actionTrack_0.setText(_translate("MainWindow", "Track 0"))
        self.action1.setText(_translate("MainWindow", "音色"))

    def new_file(self):
        """新建文件操作"""
        # 检查当前是否有未保存的修改
        if hasattr(self, 'current_midi') and self.current_midi:
            reply = QMessageBox.question(
                None,
                '新建文件',
                '当前文件可能有未保存的修改，是否继续?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # 创建新的空MIDI文件
        self.current_midi = MidiFile()
        self.current_midi.ticks_per_beat = 480  # 设置默认ticks per beat
        self.midi_file_path = None  # 新文件尚未保存，没有路径
        
        # 更新UI状态
        self.label_6.setText("未命名文件")
        self.label_5.setText("00:00 / 00:00")
        self.horizontalSlider.setValue(0)
        
        self.graphicsView.set_midi_data(self.current_midi)
        # self.graphicsView.clear_notes()
        # self.graphicsView._draw_piano_background()
        
        # 停止当前播放
        if self.is_playing:
            self.stop_playback()

    def save_file(self):
        """保存文件操作"""
        if not hasattr(self, 'current_midi') or not self.current_midi:
            QMessageBox.warning(
                None,
                "保存失败",
                "没有可保存的内容",
                QMessageBox.StandardButton.Ok
            )
            return False
        
        # 如果是新文件，转为另存为操作
        if not self.midi_file_path:
            return self.save_file_as()
        
        try:
            # 保存到当前文件路径
            self.current_midi.dump(self.midi_file_path)
            
            QMessageBox.information(
                None,
                "保存成功",
                f"文件已保存到:\n{self.midi_file_path}",
                QMessageBox.StandardButton.Ok
            )
            return True
        except Exception as e:
            QMessageBox.critical(
                None,
                "保存失败",
                f"保存文件时出错:\n{str(e)}",
                QMessageBox.StandardButton.Ok
            )
            return False

    def save_file_as(self):
        """另存为文件操作"""
        if not hasattr(self, 'current_midi') or not self.current_midi:
            QMessageBox.warning(
                None,
                "保存失败",
                "没有可保存的内容",
                QMessageBox.StandardButton.Ok
            )
            return False
        
        # 获取保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            None,
            "保存MIDI文件",
            "",
            "MIDI文件 (*.mid *.midi);;所有文件 (*)"
        )
        
        if not file_path:  # 用户取消了保存
            return False
        
        # 确保文件扩展名正确
        if not file_path.lower().endswith(('.mid', '.midi')):
            file_path += '.mid'
        
        try:
            # 保存文件
            self.current_midi.dump(file_path)
            self.midi_file_path = file_path  # 更新当前文件路径
            self.label_6.setText(Path(file_path).name)  # 更新显示的文件名
            
            QMessageBox.information(
                None,
                "保存成功",
                f"文件已保存到:\n{file_path}",
                QMessageBox.StandardButton.Ok
            )
            return True
        except Exception as e:
            QMessageBox.critical(
                None,
                "保存失败",
                f"保存文件时出错:\n{str(e)}",
                QMessageBox.StandardButton.Ok
            )
            return False
    def close_file(self):
        """关闭当前MIDI文件"""
        # 检查是否有未保存的修改（示例，可根据实际需求实现修改检测）
        if self.check_unsaved_changes():
            reply = QMessageBox.question(
                None,
                "未保存的修改",
                "当前文件有未保存的修改，是否保存？",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                if not self.save_file():  # 如果保存失败或用户取消
                    return False
            elif reply == QMessageBox.StandardButton.Cancel:
                return False
        
        # 重置所有状态
        self._reset_midi_state()
        return True

    def check_unsaved_changes(self):
        """检查是否有未保存的修改（示例逻辑）"""
        # 这里可以添加实际修改检测逻辑
        # 示例：如果当前是新创建未保存的文件，则认为有修改
        return (hasattr(self, 'current_midi') and (self.midi_file_path is None))

    def _reset_midi_state(self):
        """重置所有MIDI相关状态"""
        # 停止播放
        if self.is_playing:
            self.stop_playback()
        
        # 清除当前文件
        self.current_midi = None
        self.midi_file_path = None
        
        # 重置UI
        self.label_6.setText("请打开MIDI文件")
        self.label_5.setText("00:00 / 00:00")
        self.horizontalSlider.setValue(0)
        self.horizontalSlider.setEnabled(False)
        
        self.graphicsView.clear_scene()
        # self.graphicsView.clear_notes()
        # self.graphicsView._draw_piano_background()
        
        # 删除临时文件
        if hasattr(self, 'temp_wav_path') and os.path.exists(self.temp_wav_path):
            try:
                os.remove(self.temp_wav_path)
                del self.temp_wav_path
            except Exception as e:
                print(f"删除临时文件失败: {str(e)}")
    def exit_application(self):
        """安全关闭整个应用程序"""
        # 1. 检查是否有未保存的修改
        if self.check_unsaved_changes():
            reply = QMessageBox.question(
                None,
                "未保存的修改",
                "当前文件有未保存的修改，是否保存？",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                if not self.save_file():  # 保存失败或用户取消
                    return False
            elif reply == QMessageBox.StandardButton.Cancel:
                return False
        
        # 2. 清理资源
        self._cleanup_resources()
        
        # 3. 关闭窗口
        QtCore.QCoreApplication.quit()
        return True

    def _cleanup_resources(self):
        """清理所有资源"""
        # 停止播放
        if self.is_playing:
            self.stop_playback()
        
        # 停止录音（如果正在录音）
        if hasattr(self, 'is_recording') and self.is_recording:
            recorder.stop_recording()
        
        # 删除临时文件
        if hasattr(self, 'temp_wav_path') and os.path.exists(self.temp_wav_path):
            try:
                os.remove(self.temp_wav_path)
            except Exception as e:
                print(f"删除临时文件失败: {str(e)}")
        
        # 关闭MIDI设备
        if hasattr(self, 'midiin') and self.midiin:
            self.midiin.close_port()
        
        # 关闭Pygame
        pygame.mixer.quit()
    def open_midi_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Open MIDI File", "", "MIDI Files (*.mid *.midi)")
        if not file_path:
            return
        try:
        # 尝试加载文件（检测是否损坏）
            self.current_midi = MidiFile(file_path)
            # 验证基本结构
            if not hasattr(self.current_midi, 'instruments'):
                raise ValueError("无效的MIDI结构：缺少音轨数据")
            # 验证ticks_per_beat是否有效
            if self.current_midi.ticks_per_beat <= 0:
                raise ValueError(f"无效的ticks_per_beat值: {self.current_midi.ticks_per_beat}")
            # 验证音符数据
            for track in self.current_midi.instruments:
                for note in track.notes:
                    if not (0 <= note.pitch <= 127):
                        raise ValueError(f"无效的音高值: {note.pitch}")
                    if note.start > note.end:
                        raise ValueError(f"音符起止时间错误: start={note.start}, end={note.end}")
        except Exception as e:
            # 文件损坏时的错误处理
            error_msg = f"文件损坏或格式不支持:\n{str(e)}\n\n文件路径: {file_path}"
            QMessageBox.critical(
                None,
                "文件错误",
                error_msg,
                QMessageBox.StandardButton.Ok
            )
            # 重置状态
            self.current_midi = None
            self.midi_file_path = None
            self.label_6.setText("请打开MIDI文件")
            return
        # 文件加载成功后的处理
        try:
            self.midi_file_path = file_path
            file_name = Path(file_path).name 
            self.label_6.setText(file_name)
            self.midi_duration = self.get_midi_duration()
            self.graphicsView.set_midi_data(self.current_midi)
            self.horizontalSlider.setEnabled(True)
        except Exception as e:
            # 文件损坏时的错误处理
            error_msg = f"文件损坏或格式不支持:\n{str(e)}\n\n文件路径: {file_path}"
            QMessageBox.critical(
                None,
                "文件错误",
                error_msg,
                QMessageBox.StandardButton.Ok
            )
            # 重置状态
            self.current_midi = None
            self.midi_file_path = None
            self.label_6.setText("请打开MIDI文件")
            return
        # 转换临时WAV文件
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                temp_wav_path = temp_wav.name
            self.midi_to_wav(file_path, temp_wav_path)
            self.temp_wav_path = temp_wav_path
        except Exception as e:
            QMessageBox.warning(
                None,
                "音频转换失败",
                f"无法生成预览音频:\n{str(e)}",
                QMessageBox.StandardButton.Ok
            )
    def open_midi(self,filepath):
        file_path=filepath
        if not file_path:
            return
        try:
        # 尝试加载文件（检测是否损坏）
            self.current_midi = MidiFile(file_path)
            # 验证基本结构
            if not hasattr(self.current_midi, 'instruments'):
                raise ValueError("无效的MIDI结构：缺少音轨数据")
            # 验证ticks_per_beat是否有效
            if self.current_midi.ticks_per_beat <= 0:
                raise ValueError(f"无效的ticks_per_beat值: {self.current_midi.ticks_per_beat}")
            # 验证音符数据
            for track in self.current_midi.instruments:
                for note in track.notes:
                    if not (0 <= note.pitch <= 127):
                        raise ValueError(f"无效的音高值: {note.pitch}")
                    if note.start > note.end:
                        raise ValueError(f"音符起止时间错误: start={note.start}, end={note.end}")
        except Exception as e:
            # 文件损坏时的错误处理
            error_msg = f"文件损坏或格式不支持:\n{str(e)}\n\n文件路径: {file_path}"
            QMessageBox.critical(
                None,
                "文件错误",
                error_msg,
                QMessageBox.StandardButton.Ok
            )
            # 重置状态
            self.current_midi = None
            self.midi_file_path = None
            self.label_6.setText("请打开MIDI文件")
            return
        # 文件加载成功后的处理
        try:
            self.midi_file_path = file_path
            file_name = Path(file_path).name 
            self.label_6.setText(file_name)
            self.midi_duration = self.get_midi_duration()
            self.graphicsView.change_timescale(self.midi_duration)
            self.graphicsView.draw_midi(self.current_midi)
            self.horizontalSlider.setEnabled(True)
        except Exception as e:
            # 文件损坏时的错误处理
            error_msg = f"文件损坏或格式不支持:\n{str(e)}\n\n文件路径: {file_path}"
            QMessageBox.critical(
                None,
                "文件错误",
                error_msg,
                QMessageBox.StandardButton.Ok
            )
            # 重置状态
            self.current_midi = None
            self.midi_file_path = None
            self.label_6.setText("请打开MIDI文件")
            return
        # 转换临时WAV文件
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                temp_wav_path = temp_wav.name
            self.midi_to_wav(file_path, temp_wav_path)
            self.temp_wav_path = temp_wav_path
        except Exception as e:
            QMessageBox.warning(
                None,
                "音频转换失败",
                f"无法生成预览音频:\n{str(e)}",
                QMessageBox.StandardButton.Ok
            )
    # def _delayed_update(self):
    #     if self.current_midi:
    #         # 将滑块范围映射到0.1-2.0倍缩放
    #         min_scale = 0.2
    #         max_scale = 2.0
    #         slider_range = self.horizontalSlider.maximum() - self.horizontalSlider.minimum()
    #         normalized = self.horizontalSlider.value() / slider_range
    #         self.graphicsView.time_scale = min_scale + (max_scale - min_scale) * normalized
    #         self.graphicsView.draw_midi(self.current_midi)
    # def update_time(self, value):
    #     print("update_time",value)
    #     midi_time = self.midi_duration

    #     print(value/100*midi_time)
    #     current_time=value/1000*midi_time
    #     minute = midi_time // 60
    #     second = midi_time - minute * 60
    #     current_minute = int(current_time // 60)
    #     current_second = int(current_time - current_minute * 60+0.5)
    #     print(f"{current_minute:02d}:{current_second:02d} / {minute:02d}:{second:02d}")
    #     self.label_5.setText(f"{current_minute:02d}:{current_second:02d} / {minute:02d}:{second:02d}")

    def get_midi_duration(self):
        try:
            if not hasattr(self, 'current_midi') or not self.current_midi:
                return 0
            midi = self.current_midi
            ticks_per_beat = max(midi.ticks_per_beat, 1)  # 防零
            # 获取所有事件的结束时间
            end_times = []
            for track in midi.instruments:
                if hasattr(track, 'notes') and track.notes:
                    end_times.extend(note.end for note in track.notes)
            if not end_times:
                return 0
            last_tick = max(end_times)
            # 处理 tempo（带验证）
            def is_valid_tempo(t):
                bpm = 60_000_000 / t
                return 20 <= bpm <= 300  # 合理音乐BPM范围
            tempo = 500000  # 默认120BPM
            if hasattr(midi, 'tempo_changes') and midi.tempo_changes:
                raw_tempo = midi.tempo_changes[0].tempo
                tempo = raw_tempo if is_valid_tempo(raw_tempo) else tempo
            # 计算时长（秒）
            total_beats = last_tick / ticks_per_beat
            duration = total_beats * (tempo / 1_000_000)
            minute = int(duration // 60)
            second = int(duration - minute * 60)
            self.label_5.setText(f"00:00 / {minute:02d}:{second:02d}")
            return int(max(duration, 0))

        except Exception as e:
            print(f"计算错误: {str(e)}")
            return 0
    
    def midi_to_wav(self,midi_file_path, output_wav_path):
    # 使用fluidsynth将MIDI转换为WAV
        fs = FluidSynth(
                    sound_font=self.soundfont_path,
                    # executable=self.fluidsynth_path
                )
        fs.midi_to_audio(midi_file_path, output_wav_path)
        
        print(f"已成功将 {midi_file_path} 转换为 {output_wav_path}")
        
    def toggle_play_pause(self):
        if not self.midi_file_path:
            return
        if self.is_playing:
            # 暂停播放
            pygame.mixer.music.pause()
            self.current_time += time.time() - self.playback_start_time
            self.is_playing = False
            self.pushButton_4.setText("播放")
            self.update_timer_progress.stop()
        else:
            # 开始/恢复播放
            if self.current_time >= self.midi_duration:
                self.current_time = 0

            if self.current_time == 0:
                pygame.mixer.music.load(self.temp_wav_path)
                pygame.mixer.music.play()
                
            else:
                pygame.mixer.music.unpause()
                
            self.is_playing = True
            self.pushButton_4.setText("暂停")
            self.playback_start_time = time.time()
            self.update_timer_progress.start(100)
    def stop_playback(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.current_time = 0
        self.pushButton_4.setText("播放")
        self.horizontalSlider.setValue(0)
        self.label_5.setText("00:00 / 00:00")
        self.graphicsView.update_time(0)
        self.update_timer_progress.stop()
        # self.graphicsView.update_time(0)

    def on_slider_pressed(self):
        """当滑块被按下时，停止进度更新定时器"""
        self.is_slider_pressed = True
        if self.is_playing:
            self.update_timer_progress.stop()
            
    
    def on_slider_moved(self, value):
        if self.is_playing and self.is_slider_pressed:
            # self.toggle_play_pause()
            self.update_timer_progress.stop()
            current_pos = (value / 1000) * self.midi_duration
            current_sec = int(current_pos)
            total_sec = int(self.midi_duration)
            self.label_5.setText(
                f"{current_sec // 60:02d}:{current_sec % 60:02d} / "
                f"{total_sec // 60:02d}:{total_sec % 60:02d}"
            )
            self.graphicsView.update_time(int((current_pos / self.midi_duration) * 1000))
            
            # self.toggle_play_pause()

        else:
            current_pos = (value / 1000) * self.midi_duration
            current_sec = int(current_pos)
            total_sec = int(self.midi_duration)
            self.label_5.setText(
                f"{current_sec // 60:02d}:{current_sec % 60:02d} / "
                f"{total_sec // 60:02d}:{total_sec % 60:02d}"
            )
            self.graphicsView.update_time(int((current_pos / self.midi_duration) * 1000))
            # self.toggle_play_pause()
      
    def update_playback_progress(self):
        if self.is_playing:
            current_time = time.time()
            elapsed = current_time - self.playback_start_time
            current_pos = self.current_time + elapsed

            if current_pos >= self.midi_duration:
                self.stop_playback()
                return

            # 更新进度条
            
            progress = int((current_pos / self.midi_duration) * 1000)
            self.graphicsView.update_time(progress)
            self.horizontalSlider.setValue(progress)

            # 更新时间显示
            current_sec = int(current_pos)
            total_sec = int(self.midi_duration)
            self.label_5.setText(
                f"{current_sec // 60:02d}:{current_sec % 60:02d} / "
                f"{total_sec // 60:02d}:{total_sec % 60:02d}"
            )

            # 更新钢琴卷帘指示线
            # self.graphicsView.update_time(current_pos)

    def seek_playback(self):
        # self.update_timer_progress.start()
        if not self.midi_file_path:
            return
        value = self.horizontalSlider.value()
        seek_time = (value / 1000) * self.midi_duration

        if self.is_playing:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(self.temp_wav_path)
            try:
                pygame.mixer.music.play(start=seek_time)
            except pygame.error:
                try:
                    pygame.mixer.music.set_pos(seek_time)
                except pygame.error:
                    pygame.mixer.music.play()
            self.playback_start_time = time.time() - seek_time
            self.update_timer_progress.start()
            self.is_slider_pressed = False
        else:
            self.current_time = seek_time
            pygame.mixer.music.load(self.temp_wav_path)
            try:
                pygame.mixer.music.play(start=seek_time)
            except pygame.error:
                try:
                    pygame.mixer.music.set_pos(seek_time)
                except pygame.error:
                    pygame.mixer.music.play()
            self.is_playing=True
            self.pushButton_4.setText("暂停")
            self.playback_start_time = time.time()
            self.update_timer_progress.start(100)
        self.graphicsView.update_time(int((seek_time / self.midi_duration) * 1000))
    
    def toggle_record(self):
        if self.is_recording:
            recorder.stop_recording()
            self.is_recording = False
            current_midi=recorder.export_to_midi()
            print(current_midi)
            if current_midi is None:
                QMessageBox.critical(
                    None, 
                    "录制错误", 
                    f"无录制内容!", 
                    QMessageBox.StandardButton.Ok
                )
                self.pushButton.setText("开始录制")
                self.pushButton.setStyleSheet("background-color: rgba(170, 0, 0,200);\n"
                                          "color: rgb(255, 255, 255);\n"
                                          "border-radius:10px;\n"
                                          "border:1px solid #000000;\n"
                                          "font: 10pt \"楷体\";\n"
                                          "font-weight:900;\n"
                                          "height:50px;")
                self.update_timer_recorder.stop()
                
                return
            else:
                self.current_midi=current_midi
                self.open_midi("/home/pi/Desktop/final_codes/output.mid")
                self.save_file_as()
                self.pushButton.setText("开始录制")
                self.pushButton.setStyleSheet("background-color: rgba(170, 0, 0,200);\n"
                                          "color: rgb(255, 255, 255);\n"
                                          "border-radius:10px;\n"
                                          "border:1px solid #000000;\n"
                                          "font: 10pt \"楷体\";\n"
                                          "font-weight:900;\n"
                                          "height:50px;")
                self.update_timer_recorder.stop()
        else:
            ports=recorder.list_input_ports()
            if len(ports)<1:
                print('no ports')
                QMessageBox.critical(
                    None, 
                    "MIDI错误", 
                    f"无可用midi设备!", 
                    QMessageBox.StandardButton.Ok
                )
            else:
                self.recording_start_time=time.time()
                recorder.start_recording(self.selected_port)
                self.is_recording = True
                self.pushButton.setText("停止录制")
                self.pushButton.setStyleSheet("color: rgb(255, 255, 255);\n"
                                      "border-radius:10px;\n"
                                      "border:1px solid #000000;\n"
                                      "font: 10pt \"楷体\";\n"
                                      "font-weight:900;\n"
                                      "height:50px;\n"
                                      "background-color: rgb(0, 170, 0);")
                self.update_timer_recorder.start(100)
    
    def update_recorder_progress(self):
        if self.is_recording:
            current_time=time.time()-self.recording_start_time
            minutes=int(current_time // 60)
            seconds=int(current_time%60)
            self.label_5.setText(f'00:00 / {minutes:02d}:{seconds:02d}')
    
    def update_track_menu(self):
    
        self.menuTrack.clear()
        # 如果没有音轨，添加一个默认项
        if not self.input_ports:
            default_action = QtWidgets.QAction("无音轨", self.menuTrack)
            default_action.setEnabled(False)
            self.menuTrack.addAction(default_action)
            return
        # 添加音轨项
        for i, track_name in enumerate(self.input_ports):
            action = QtWidgets.QAction(f"输入 {i}: {track_name}", self.menuTrack)
            action.setData(i)  # 存储音轨索引
            action.triggered.connect(lambda checked, idx=i: self.on_track_selected(idx))
            self.menuTrack.addAction(action)
    def on_track_selected(self, port_index):
        self.selected_port=port_index
        print(port_index)
    # ... [rest of the methods remain the same as they don't contain PyQt-specific code]
    # All the other methods (new_file, save_file, etc.) remain unchanged since they don't contain PyQt-specific code
    # that needs conversion between PyQt5 and PyQt6
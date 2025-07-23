import miditoolkit
from miditoolkit import MidiFile, Instrument, Note
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem, QMenu
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QTransform, QKeySequence
from PyQt5 import QtCore, QtGui

''' 
这是一个钢琴卷帘视图类，用于显示和编辑 MIDI 音符。
经过重构以获得高性能的渲染和流畅的编辑体验。
'''

class PianoRollView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing) # 启用抗锯齿，使图形更平滑
        self.setDragMode(QGraphicsView.ScrollHandDrag) # 初始设置为拖拽移动视图模式
        self.setStyleSheet("border-radius:10px; background-color: rgb(232, 232, 232)")

        # 时间指示器（播放头）
        self.time_indicator = QGraphicsLineItem()
        # 初始设置一个基准宽度，后续会根据缩放动态调整
        self.base_indicator_width = 2 # 基准指示线宽度（像素）
        self.time_indicator.setPen(QPen(QtCore.Qt.red, self.base_indicator_width)) # 设置为红色，初始宽度
        self.time_indicator.setZValue(10) # 确保指示器在最上层
        self.scene.addItem(self.time_indicator)

        self.note_items = []  # 存储所有音符的 QGraphicsRectItem 实例

        # --- 钢琴卷帘参数 ---
        # 【重构核心】: 移除了手动的 time_scale。现在场景坐标系是固定的：
        # 场景X坐标的1个单位 = 1个MIDI tick。
        # 场景Y坐标的1个单位 = 1个音高单位。
        # 缩放完全由 QGraphicsView 的变换矩阵处理，性能极高。
        self.base_key_height = 15  # 在场景坐标中，每个音高（琴键）的基准高度
        self.zoom_factor = 1.2 # 每次滚轮事件的缩放系数

        # --- 编辑相关属性 ---
        self.current_midi = None # 当前加载的 MIDI 文件对象
        self.editing_mode = 'select'  # 当前模式: 'select' (选择/移动), 'add_note' (添加音符), 'resize_note_end' (调整音符长度)
        self.selected_notes_items = [] # 存储当前选中的 QGraphicsRectItem
        self.selected_miditoolkit_notes = [] # 存储当前选中的 miditoolkit.Note 对象
        self.clipboard_notes = [] # 用于复制/粘贴的剪贴板

        #用于高效拖动/调整大小的属性
        self.drag_start_pos = None      # 鼠标按下时的场景坐标
        self.resizing_note_item = None  # 正在调整大小的音符图形项
        # 存储拖动/调整大小前，音符的原始状态，用于计算最终变化
        self.drag_notes_original_state = {} # 格式: {note_item: {'start': tick, 'pitch': pitch, 'end': tick}}

        self.scene.selectionChanged.connect(self._on_selection_changed) # 连接场景选择变化信号
        self.setMouseTracking(True) # 启用鼠标跟踪以实时更新光标样式

    def set_midi_data(self, midi_file):
        """
        设置要显示和编辑的MIDI数据。
        参数:
            midi_file (miditoolkit.MidiFile): 要加载的 MIDI 文件对象。
        """
        self.current_midi = midi_file
        self.draw_midi(self.current_midi)
        self.fit_to_view() # 【新增】: 加载后自动缩放以适应视图

    def fit_to_view(self):
        """
        调整视图缩放，使整个乐曲在水平方向上完整可见，并设置一个合理的垂直缩放。
        这有助于解决音乐长度过长导致音符过细的问题。
        """
        if not self.note_items:
            # 如果没有音符，设置一个默认的场景矩形，并调整时间指示器
            # 默认显示 C2 (36) 到 C7 (96) 的范围
            default_min_pitch = 36
            default_max_pitch = 96
            default_scene_y_top = (127 - default_max_pitch) * self.base_key_height
            default_scene_y_bottom = (127 - default_min_pitch) * self.base_key_height
            self.setSceneRect(0, default_scene_y_top, 1000, default_scene_y_bottom - default_scene_y_top)
            self.time_indicator.setLine(0, 0, 0, self.sceneRect().height())
            return

        # 获取场景中所有图形项的边界矩形
        items_rect = self.scene.itemsBoundingRect()
        # 添加一些边距，以便看得更清楚
        items_rect.adjust(-50, -self.base_key_height * 2, 50, self.base_key_height * 2)

        # 计算水平方向的适配比例
        view_width = self.viewport().width()
        if view_width > 0 and items_rect.width() > 0:
            horizontal_scale = view_width / items_rect.width()
        else:
            horizontal_scale = 1.0 # 默认比例

        # 计算垂直方向的适配比例，目标是让每个琴键在屏幕上至少有 min_on_screen_key_height 像素高
        view_height = self.viewport().height()
        # 确保目标场景高度是 draw_midi 已经设置的实际场景高度
        target_scene_height = self.scene.sceneRect().height() 

        if view_height > 0 and target_scene_height > 0:
            min_on_screen_key_height = 5.0 # 每个琴键在屏幕上至少显示的像素高度
            # 计算适配整个垂直范围的缩放比例
            vertical_scale_to_fit = view_height / target_scene_height
            # 计算确保最小琴键高度的缩放比例
            vertical_scale_min_key_height = min_on_screen_key_height / self.base_key_height
            # 取两者中的较大值，以确保音符既能尽可能地适应视图，又不会过小
            vertical_scale = max(vertical_scale_to_fit, vertical_scale_min_key_height)
        else:
            vertical_scale = 1.0

        # 重置当前变换，以便应用新的缩放
        self.setTransform(QTransform())

        # 应用计算出的缩放
        new_transform = QTransform()
        new_transform.scale(horizontal_scale, vertical_scale)
        self.setTransform(new_transform)

        # 居中视图内容
        if items_rect.isValid():
            center_y_in_scene = items_rect.center().y()
            center_x_in_scene = items_rect.center().x()
        else:
            center_y_in_scene = self.sceneRect().center().y()
            center_x_in_scene = self.sceneRect().center().x()

        self.centerOn(center_x_in_scene, center_y_in_scene)



    def clear_scene(self):
        """清除场景中的所有音乐元素（音符、背景等）。"""
        # 从场景中移除所有音符图形项
        for item in self.note_items:
            self.scene.removeItem(item)
        
        # 清除背景元素（线条和琴键阴影）
        for item in self.scene.items():
            if isinstance(item, (QGraphicsLineItem, QGraphicsRectItem)) and item not in self.note_items:
                 if item != self.time_indicator: # 不要移除时间指示器
                    self.scene.removeItem(item)

        self.note_items.clear()
        self.selected_notes_items.clear()
        self.selected_miditoolkit_notes.clear()

    def wheelEvent(self, event):
        """
        处理鼠标滚轮事件以进行缩放。
        默认进行水平缩放（时间轴），按住 Shift 键时进行垂直缩放（音高）。
        """
        zoom_in_factor = self.zoom_factor
        zoom_out_factor = 1 / zoom_in_factor

        zoom_x = 1.0
        zoom_y = 1.0

        # 判断滚轮方向
        if event.angleDelta().y() > 0: # 向上滚动
            zoom_x = zoom_in_factor
            zoom_y = zoom_in_factor
        else: # 向下滚动
            zoom_x = zoom_out_factor
            zoom_y = zoom_out_factor

        # 如果按住 Shift 键，则只进行垂直缩放
        if event.modifiers() & QtCore.Qt.ShiftModifier:
            zoom_x = 1.0 # 不进行水平缩放
        else:
            zoom_y = 1.0 # 不进行垂直缩放 (除非按住 Shift 键)

        # 获取鼠标光标下的场景坐标点作为缩放的中心
        anchor_point = self.mapToScene(event.pos())
        
        # 创建一个变换矩阵，围绕锚点进行缩放
        transform = QTransform().translate(anchor_point.x(), anchor_point.y()).scale(zoom_x, zoom_y).translate(-anchor_point.x(), -anchor_point.y())
        self.setTransform(transform, combine=True) # 应用变换

    def update_time(self, position):
        """
        根据播放进度（0-1000 范围）更新时间指示器的位置。
        参数:
            position (int): 0-1000 范围内的播放进度值。
        """
        if self.current_midi and self.current_midi.ticks_per_beat > 0:
            total_ticks = self.current_midi.max_tick # 获取 MIDI 文件的总 tick 数
            
            if total_ticks > 0:
                current_tick = (position / 1000.0) * total_ticks # 将进度转换为场景中的 tick 坐标
                
                # 获取当前视图的水平缩放比例
                current_scale_x = self.transform().m11()
                # 根据缩放比例动态调整指示线的宽度
                # 确保宽度至少为 1 像素，并随着缩放比例的减小而增大
                dynamic_width = max(1, int(self.base_indicator_width / current_scale_x))
                self.time_indicator.setPen(QPen(QtCore.Qt.red, dynamic_width))

                # 获取当前可见的场景矩形范围
                visible_rect = self.mapToScene(self.viewport().rect()).boundingRect()
                
                # 调整时间指示器线，使其跨越当前可见的垂直高度
                self.time_indicator.setLine(current_tick, visible_rect.top(), current_tick, visible_rect.bottom())

                # 可选: 滚动视图以保持播放头可见 (如果播放头超出当前视图范围)
                if not visible_rect.contains(QtCore.QPointF(current_tick, visible_rect.center().y())):
                     # 滚动以水平居中播放头
                    self.centerOn(current_tick, visible_rect.center().y())

                self.viewport().update() # 更新视图
        else:
            # 如果没有 MIDI 数据，将指示器隐藏或重置
            self.time_indicator.setLine(0, 0, 0, 0)
            self.time_indicator.setPen(QPen(QtCore.Qt.red, self.base_indicator_width)) # 恢复默认宽度
            self.viewport().update()

    def draw_midi(self, midi):
        """
        将MIDI文件中的音符绘制到钢琴卷帘上。
        参数:
            midi (miditoolkit.MidiFile): 要绘制的 MIDI 文件对象。
        """
        self.clear_scene() # 清除现有场景内容
        self._draw_piano_background() # 绘制钢琴卷帘背景

        if not midi:
            return

        self.current_midi = midi
        max_tick = 0 # 记录最大 tick 值，用于设置场景宽度
        min_pitch = 127 # 记录最低音高
        max_pitch = 0 # 记录最高音高

        for instrument in midi.instruments:
            # 鼓组使用不同颜色，其他乐器使用另一种颜色
            color = QColor(200, 50, 50, 180) if instrument.is_drum else QColor(30, 100, 200, 180)
            
            for note in instrument.notes:
                # 【重构核心】: 场景坐标直接从MIDI数据映射，不再乘以 time_scale。
                # X 坐标直接对应 MIDI tick
                x = note.start
                # Y 坐标通过音高和基准琴键高度计算 (127 - pitch 是因为 Y 轴向下，音高越高 Y 值越小)
                y = (127 - note.pitch) * self.base_key_height
                # 宽度直接对应音符持续的 tick 数量
                w = note.end - note.start
                # 高度为基准琴键高度
                h = self.base_key_height

                rect = QGraphicsRectItem(x, y, w, h) # 创建音符的矩形图形项
                rect.setBrush(QBrush(color)) # 设置填充颜色
                rect.setPen(QPen(QColor(50,50,50), 0.5)) # 设置边框

                rect.setFlag(QGraphicsRectItem.ItemIsSelectable) # 使音符可被选中
                
                # 在图形项中存储对原始 miditoolkit 对象的引用
                rect.midi_note = note
                rect.midi_instrument = instrument
                
                self.scene.addItem(rect) # 将音符添加到场景
                self.note_items.append(rect) # 存储音符图形项
                max_tick = max(max_tick, note.end) # 更新最大 tick
                min_pitch = min(min_pitch, note.pitch) # 更新最低音高
                max_pitch = max(max_pitch, note.pitch) # 更新最高音高

        # 处理没有音符或音高范围过窄的情况，设置一个默认的显示范围
        if not self.note_items:
            # 默认显示 C2 (36) 到 C7 (96) 的范围
            effective_min_pitch = 36
            effective_max_pitch = 96
        else:
            # 在实际音高范围的基础上增加一些填充，例如上下各一个八度
            effective_min_pitch = max(0, min_pitch - 12) 
            effective_max_pitch = min(127, max_pitch + 12)

        # 计算场景 Y 坐标的顶部和底部，基于有效音高范围
        scene_y_top = (127 - effective_max_pitch) * self.base_key_height
        scene_y_bottom = (127 - effective_min_pitch) * self.base_key_height
        
        # 设置场景的矩形范围 (x, y, width, height)
        # x: 0 (从时间轴起点开始)
        # y: 计算出的场景顶部 Y 坐标
        # width: 最大 tick 值加上几拍的填充 (例如 4 拍)
        # height: 场景底部 Y 坐标减去场景顶部 Y 坐标
        self.scene.setSceneRect(0, scene_y_top, max_tick + midi.ticks_per_beat * 4, scene_y_bottom - scene_y_top)

        # 调整时间指示器线，使其跨越新的场景矩形高度
        self.time_indicator.setLine(self.time_indicator.line().x1(), self.scene.sceneRect().top(),
                                    self.time_indicator.line().x1(), self.scene.sceneRect().bottom())


    def _draw_piano_background(self):
        """(已废弃) 绘制钢琴卷帘的背景（琴键通道和分割线）。"""
        # # 这个函数现在只在完全重绘时调用一次。
        # black_notes_pitches = {1, 3, 6, 8, 10} # 黑键对应的音高模 12 的值
        
        # # 绘制一个足够宽的背景，以避免在平移时需要重绘
        # # 宽度设置为一个非常大的值，场景矩形会对其进行裁剪
        # generous_width = 1000000 

        # for pitch in range(128): # 遍历所有 128 个 MIDI 音高
        #     y = (127 - pitch) * self.base_key_height # 计算当前音高在场景中的 Y 坐标
            
        #     # 为黑键通道绘制灰色背景
        #     if (pitch % 12) in black_notes_pitches:
        #         rect = QGraphicsRectItem(0, y, generous_width, self.base_key_height) # 创建背景矩形
        #         rect.setBrush(QBrush(QColor(210, 210, 210))) # 设置灰色填充
        #         rect.setPen(QPen(QtCore.Qt.transparent)) # 无边框
        #         rect.setZValue(-10) # 确保背景在音符后面
        #         self.scene.addItem(rect)

        #     # 绘制水平分割线
        #     line = QGraphicsLineItem(0, y, generous_width, y) # 创建水平线
        #     line.setPen(QPen(QColor(180, 180, 180), 0.5)) # 设置线的颜色和宽度
        #     line.setZValue(-9) # 确保线在背景之上，音符之下
        #     self.scene.addItem(line)
        pass

    def _view_pos_to_midi_coords(self, view_pos):
        """
        将视图坐标（像素）转换为MIDI坐标（tick 和 pitch）。
        参数:
            view_pos (QtCore.QPoint): 视图中的像素位置。
        返回:
            tuple: (midi_time, midi_pitch) 转换后的 MIDI 时间 (tick) 和音高。
        """
        scene_pos = self.mapToScene(view_pos) # 将视图坐标映射到场景坐标
        
        # 【重构核心】: 由于场景坐标系固定，转换变得非常简单。
        midi_time = int(scene_pos.x()) # 场景 X 坐标直接对应 MIDI tick
        midi_pitch = 127 - int(scene_pos.y() / self.base_key_height) # 场景 Y 坐标转换为 MIDI 音高
        
        # 确保值在有效范围内
        midi_pitch = max(0, min(127, midi_pitch))
        midi_time = max(0, midi_time)
        return midi_time, midi_pitch

    def _on_selection_changed(self):
        """当场景中的选择发生变化时，更新内部的选中音符列表。"""
        self.selected_notes_items = [item for item in self.scene.selectedItems() if hasattr(item, 'midi_note')]
        self.selected_miditoolkit_notes = [item.midi_note for item in self.selected_notes_items]

    def _is_on_note_edge(self, note_item, scene_pos, edge_tolerance=10):
        """
        检查鼠标位置是否在音符图形项的右边缘，用于调整大小。
        参数:
            note_item (QGraphicsRectItem): 音符的图形项。
            scene_pos (QtCore.QPointF): 鼠标在场景中的位置。
            edge_tolerance (int): 边缘检测的像素容差。
        返回:
            bool: 如果鼠标在音符右边缘附近，则为 True。
        """
        # 将视图中的像素容差转换为场景坐标单位
        pixel_width_in_scene = self.mapToScene(edge_tolerance, 0).x() - self.mapToScene(0, 0).x()
        rect = note_item.rect()
        item_scene_pos = note_item.scenePos()
        # 检查鼠标的场景 X 坐标是否接近图形项在场景中的右边缘
        return abs(scene_pos.x() - (item_scene_pos.x() + rect.width())) < pixel_width_in_scene

    def _select_items_for_notes(self, midi_notes):
        """
        根据给定的 miditoolkit.Note 对象列表，选中对应的图形项。
        参数:
            midi_notes (list): miditoolkit.Note 对象的列表。
        """
        self.scene.clearSelection() # 清除当前所有选择
        for item in self.note_items:
            if hasattr(item, 'midi_note') and item.midi_note in midi_notes:
                item.setSelected(True) # 选中对应的图形项

    def mousePressEvent(self, event):
        """处理鼠标按下事件。"""
        scene_pos = self.mapToScene(event.pos()) # 鼠标按下时的场景坐标
        items_at_pos = self.items(event.pos()) # 鼠标位置下的所有图形项
        # 获取最顶层的音符图形项
        top_item = next((item for item in items_at_pos if isinstance(item, QGraphicsRectItem) and hasattr(item, 'midi_note')), None)

        self.drag_start_pos = scene_pos # 记录拖拽起始位置

        if event.button() == QtCore.Qt.LeftButton: # 左键按下
            if self.editing_mode == 'add_note': # 如果是添加音符模式
                midi_time, midi_pitch = self._view_pos_to_midi_coords(event.pos())
                self._add_new_note_interactively(midi_time, midi_pitch) # 添加新音符
                self.set_editing_mode('select') # 添加后自动返回选择模式
            
            elif self.editing_mode == 'select': # 如果是选择模式
                if top_item: # 如果点击了音符
                    # 优先检查是否点击了边缘以调整大小
                    if self._is_on_note_edge(top_item, scene_pos):
                        self.setDragMode(QGraphicsView.NoDrag) # 【状态管理】禁用视图拖动
                        self.set_editing_mode('resize_note_end') # 进入调整大小模式
                        self.resizing_note_item = top_item # 记录正在调整大小的音符
                        self._select_items_for_notes([top_item.midi_note]) # 只选中当前调整的音符
                    # 否则，是移动/选择操作
                    else:
                        self.setDragMode(QGraphicsView.NoDrag) # 【状态管理】禁用视图拖动
                        self.set_editing_mode('move_note') # 进入移动音符模式
                        # 处理选择逻辑 (Ctrl/Cmd 用于多选)
                        if not (event.modifiers() & QtCore.Qt.ControlModifier):
                            if not top_item.isSelected(): # 如果未按 Ctrl 且当前音符未选中，则清除其他选择
                                self.scene.clearSelection()
                        top_item.setSelected(not top_item.isSelected()) # 切换音符的选中状态
                        
                        # 【性能优化】存储所有选中音符的原始状态，用于拖动计算
                        self.drag_notes_original_state.clear()
                        for item in self.selected_notes_items:
                            note = item.midi_note
                            self.drag_notes_original_state[item] = {'start': note.start, 'pitch': note.pitch, 'end': note.end}
                else:
                    # 点击了空白处，清除选择并允许平移视图
                    self.scene.clearSelection()
                    self.setDragMode(QGraphicsView.ScrollHandDrag) # 恢复视图拖动模式
                    super().mousePressEvent(event) # 将事件传递给父类以处理视图拖动
        
        elif event.button() == QtCore.Qt.RightButton: # 右键按下
            if top_item: # 如果点击了音符
                self._show_note_context_menu(top_item, event.globalPos()) # 显示音符上下文菜单
            else:
                super().mousePressEvent(event) # 将事件传递给父类

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件。"""
        if not self.drag_start_pos: # 如果没有拖拽起始点，则调用父类方法
            super().mouseMoveEvent(event)
            return

        scene_pos = self.mapToScene(event.pos()) # 当前鼠标在场景中的位置

        if event.buttons() & QtCore.Qt.LeftButton: # 如果左键被按下并移动
            # 【重构核心】: 高效地移动/调整视觉项，不进行任何重绘。
            if self.editing_mode == 'move_note' and self.selected_notes_items: # 移动音符模式
                delta_x = scene_pos.x() - self.drag_start_pos.x() # X 轴位移
                delta_y = scene_pos.y() - self.drag_start_pos.y() # Y 轴位移
                
                # 将 Y 轴位移转换为音高变化（Y 轴向下，音高向上，所以是负号）
                delta_pitch = -round(delta_y / self.base_key_height)

                # 移动所有选中的图形项
                for item in self.selected_notes_items:
                    original_state = self.drag_notes_original_state[item]
                    # 计算新的视觉位置 (基于原始位置和位移)
                    new_start_pos = original_state['start'] + delta_x
                    new_pitch_pos_y = ((127 - (original_state['pitch'] + delta_pitch)) * self.base_key_height)
                    # 使用 setPos 进行高效的视觉移动 (相对于其原始位置的偏移量)
                    item.setPos(new_start_pos - original_state['start'], new_pitch_pos_y - ((127-original_state['pitch'])*self.base_key_height))

            elif self.editing_mode == 'resize_note_end' and self.resizing_note_item: # 调整音符长度模式
                note = self.resizing_note_item.midi_note
                # 确保音符有最小长度 (例如 10 ticks)
                new_end_tick = max(note.start + 10, int(scene_pos.x()))
                
                # 只更新图形项的宽度，非常轻量
                rect = self.resizing_note_item.rect()
                rect.setWidth(new_end_tick - note.start)
                self.resizing_note_item.setRect(rect)

        # 实时更新光标样式
        elif self.editing_mode == 'select':
            top_item = self.itemAt(event.pos()) # 获取鼠标位置下的最顶层图形项
            if top_item and hasattr(top_item, 'midi_note') and self._is_on_note_edge(top_item, self.mapToScene(event.pos())):
                 self.setCursor(QtCore.Qt.SizeHorCursor) # 如果在音符右边缘，显示水平调整大小光标
            else:
                 self.unsetCursor() # 否则，恢复默认光标
        
        super().mouseMoveEvent(event) # 调用父类方法处理其他移动事件

    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件。"""
        # 【重构核心】: 在鼠标释放时，才将视觉上的变化提交到底层数据模型。
        if event.button() == QtCore.Qt.LeftButton: # 左键释放
            scene_pos = self.mapToScene(event.pos()) # 鼠标释放时的场景坐标
            
            if self.editing_mode == 'move_note' and self.selected_notes_items: # 移动音符模式
                delta_x = scene_pos.x() - self.drag_start_pos.x() # X 轴总位移
                delta_y = scene_pos.y() - self.drag_start_pos.y() # Y 轴总位移
                delta_ticks = int(round(delta_x)) # 将 X 轴位移四舍五入为整数 tick
                delta_pitch = -round(delta_y / self.base_key_height) # 将 Y 轴位移四舍五入为整数音高变化

                for item in self.selected_notes_items:
                    original_state = self.drag_notes_original_state[item] # 获取音符的原始状态
                    note = item.midi_note
                    duration = original_state['end'] - original_state['start'] # 保持音符时长不变

                    # 更新数据模型中的音符起始和结束时间
                    note.start = max(0, original_state['start'] + delta_ticks)
                    note.end = note.start + duration
                    # 更新数据模型中的音符音高
                    note.pitch = max(0, min(127, original_state['pitch'] + delta_pitch))
                
                # 操作结束后进行一次重绘，以确保视觉与数据完全同步
                self.draw_midi(self.current_midi)
                self._select_items_for_notes(self.selected_miditoolkit_notes) # 重新选中音符

            elif self.editing_mode == 'resize_note_end' and self.resizing_note_item: # 调整音符长度模式
                note = self.resizing_note_item.midi_note
                new_end_tick = max(note.start + 10, int(scene_pos.x())) # 确保音符有最小长度
                # 更新数据模型中的音符结束时间
                note.end = new_end_tick

                # 操作结束后进行一次重绘
                self.draw_midi(self.current_midi)
                self._select_items_for_notes([note]) # 重新选中被调整的音符
        
        # 重置状态
        self.set_editing_mode('select') # 恢复为选择模式
        self.setDragMode(QGraphicsView.ScrollHandDrag) # 【状态管理】恢复视图拖动
        self.unsetCursor() # 恢复默认光标
        self.drag_start_pos = None # 清除拖拽起始位置
        self.resizing_note_item = None # 清除正在调整大小的音符
        self.drag_notes_original_state.clear() # 清除原始状态数据
        
        super().mouseReleaseEvent(event) # 调用父类方法处理其他释放事件

    # --- 音符操作方法 (逻辑基本不变, 但现在受益于高效的后端) ---

    def _add_new_note_interactively(self, start_tick, pitch):
        """
        在用户点击的位置添加一个新音符。
        参数:
            start_tick (int): 音符的起始 tick。
            pitch (int): 音符的音高。
        """
        if not self.current_midi:
            # 如果没有当前 MIDI 文件，则创建一个新的空 MIDI 文件
            self.current_midi = MidiFile(ticks_per_beat=480)
            new_instrument = Instrument(program=0, is_drum=False, name='新乐器')
            self.current_midi.instruments.append(new_instrument)
            
        default_duration = self.current_midi.ticks_per_beat # 默认持续时间为一拍
        new_note = Note(pitch=pitch, velocity=100, start=start_tick, end=start_tick + default_duration)
        
        # 将音符添加到第一个乐器（或将来可选的乐器）
        target_instrument = self.current_midi.instruments[0]
        target_instrument.notes.append(new_note)
        target_instrument.notes.sort(key=lambda x: x.start) # 保持音符按开始时间排序
        
        self.draw_midi(self.current_midi) # 重绘以显示新音符
        self._select_items_for_notes([new_note]) # 自动选中新添加的音符

    def delete_selected_notes(self):
        """删除所有选中的音符。"""
        if not self.selected_miditoolkit_notes or not self.current_midi:
            return

        notes_to_delete = list(self.selected_miditoolkit_notes) # 复制一份待删除音符列表
        for note in notes_to_delete:
            for instrument in self.current_midi.instruments:
                if note in instrument.notes:
                    instrument.notes.remove(note) # 从乐器中移除音符
                    break
        
        self.draw_midi(self.current_midi) # 删除后重绘

    def quantize_selected_notes(self, subdivision_ticks=120):
        """
        量化选中音符的开始时间 (默认量化到 16 分音符，即 120 ticks)。
        参数:
            subdivision_ticks (int): 量化网格的 tick 间隔。
        """
        if not self.selected_miditoolkit_notes: return

        for note in self.selected_miditoolkit_notes:
            duration = note.end - note.start # 保持音符时长不变
            # 将开始时间吸附到最近的量化网格
            new_start = round(note.start / subdivision_ticks) * subdivision_ticks
            note.start = int(new_start)
            note.end = int(new_start + duration)
        
        self.draw_midi(self.current_midi) # 量化后重绘
        self._select_items_for_notes(self.selected_miditoolkit_notes) # 重新选中音符

    def copy_selected_notes(self):
        """复制选中的音符到内部剪贴板。"""
        self.clipboard_notes = [note.copy() for note in self.selected_miditoolkit_notes] # 复制音符对象

    def paste_notes(self):
        """从剪贴板粘贴音符。"""
        if not self.clipboard_notes or not self.current_midi.instruments: return

        # 粘贴到当前视图的左边缘位置
        visible_scene_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        paste_time = max(0, int(visible_scene_rect.left())) # 粘贴的起始时间点
        
        # 找到剪贴板中最早的音符开始时间，以它为基准进行对齐
        if not self.clipboard_notes: return
        first_note_time = min(n.start for n in self.clipboard_notes)
        time_offset = paste_time - first_note_time # 计算时间偏移量

        newly_pasted_notes = [] # 存储新粘贴的音符
        target_instrument = self.current_midi.instruments[0] # 目标乐器 (第一个乐器)

        for note_copy in self.clipboard_notes:
            new_note = note_copy.copy() # 复制音符
            duration = new_note.end - new_note.start # 获取原始音符时长
            new_note.start = new_note.start + time_offset # 应用时间偏移
            new_note.end = new_note.start + duration # 更新结束时间
            
            target_instrument.notes.append(new_note) # 将新音符添加到目标乐器
            newly_pasted_notes.append(new_note)
        
        target_instrument.notes.sort(key=lambda x: x.start) # 保持排序
        self.draw_midi(self.current_midi) # 粘贴后重绘
        self._select_items_for_notes(newly_pasted_notes) # 选中新粘贴的音符

    def adjust_selected_notes_velocity(self, delta_velocity):
        """
        调整选中音符的力度。
        参数:
            delta_velocity (int): 力度的变化量。
        """
        if not self.selected_miditoolkit_notes: return
        
        for note in self.selected_miditoolkit_notes:
            note.velocity = max(1, min(127, note.velocity + delta_velocity)) # 调整力度，限制在 1-127 之间
        # 注意：如果需要根据力度改变颜色，需要调用重绘
        # self.draw_midi(self.current_midi)
        # self._select_items_for_notes(self.selected_miditoolkit_notes)

    def _show_note_context_menu(self, clicked_item, global_pos):
        """
        显示音符的右键上下文菜单。
        参数:
            clicked_item (QGraphicsRectItem): 被点击的音符图形项。
            global_pos (QtCore.QPoint): 鼠标的全局屏幕坐标。
        """
        # 在显示菜单前，确保被点击的音符是选中的
        if not clicked_item.isSelected():
            self._select_items_for_notes([clicked_item.midi_note])

        menu = QMenu(self) # 创建上下文菜单
        delete_action = menu.addAction("删除")
        quantize_action = menu.addAction("量化 (1/16)")
        velocity_up_action = menu.addAction("力度 +10")
        velocity_down_action = menu.addAction("力度 -10")
        
        action = menu.exec_(global_pos) # 显示菜单并等待用户选择

        # 根据用户选择执行相应操作
        if action == delete_action: self.delete_selected_notes()
        elif action == quantize_action: self.quantize_selected_notes()
        elif action == velocity_up_action: self.adjust_selected_notes_velocity(10)
        elif action == velocity_down_action: self.adjust_selected_notes_velocity(-10)

    def set_editing_mode(self, mode):
        """
        设置当前的编辑模式并更新光标样式。
        参数:
            mode (str): 编辑模式 ('select', 'add_note', 'move_note', 'resize_note_end')。
        """
        self.editing_mode = mode
        if mode == 'add_note':
            self.setCursor(QtCore.Qt.CrossCursor) # 添加音符时显示十字光标
        else:
            self.unsetCursor() # 其他模式恢复默认光标

    def keyPressEvent(self, event):
        """
        处理键盘快捷键。
        参数:
            event (QtGui.QKeyEvent): 键盘事件。
        """
        if event.key() == QtCore.Qt.Key_Delete or event.key() == QtCore.Qt.Key_Backspace:
            self.delete_selected_notes() # 删除选中音符
        # 使用标准的 QKeySequence，可以更好地兼容不同操作系统 (例如 macOS 上的 Cmd+C)
        elif event.matches(QKeySequence.Copy):
            self.copy_selected_notes() # 复制选中音符
        elif event.matches(QKeySequence.Cut):
            self.copy_selected_notes() # 复制并删除
            self.delete_selected_notes()
        elif event.matches(QKeySequence.Paste):
            self.paste_notes() # 粘贴音符
        elif event.matches(QKeySequence.SelectAll):
             # 全选所有音符
             all_notes = [note for i in self.current_midi.instruments for note in i.notes]
             self._select_items_for_notes(all_notes)
        elif event.key() == QtCore.Qt.Key_Q:
            self.quantize_selected_notes() # 量化选中音符
        else:
            super().keyPressEvent(event) # 调用父类方法处理其他按键事件
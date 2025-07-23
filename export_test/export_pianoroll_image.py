from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtCore import QRect

def export_pianoroll_image(parent, graphics_view):
    """
    导出钢琴卷帘图为PNG图片。
    参数:
        parent: 父窗口（用于弹窗）
        graphics_view: QGraphicsView对象（显示钢琴卷帘图）
    """
    if graphics_view is None:
        QMessageBox.warning(parent, "导出失败", "未找到钢琴卷帘图视图。", QMessageBox.StandardButton.Ok)
        return

    file_path, _ = QFileDialog.getSaveFileName(parent, "导出钢琴卷帘图", "", "PNG图片 (*.png)")
    if not file_path:
        return
    if not file_path.lower().endswith('.png'):
        file_path += '.png'

    # 截取当前graphics_view内容为图片
    pixmap = graphics_view.grab()
    if pixmap.save(file_path, "PNG"):
        QMessageBox.information(parent, "导出成功", f"图片已保存到:\n{file_path}", QMessageBox.StandardButton.Ok)
    else:
        QMessageBox.critical(parent, "导出失败", "保存图片时出错。", QMessageBox.StandardButton.Ok)

def export_pianoroll_fullscene(parent, graphics_view):
    """
    导出完整场景（全部内容，不仅仅是可见区域）为PNG图片。
    """
    if graphics_view is None or graphics_view.scene() is None:
        QMessageBox.warning(parent, "导出失败", "未找到钢琴卷帘图场景。", QMessageBox.StandardButton.Ok)
        return

    file_path, _ = QFileDialog.getSaveFileName(parent, "导出完整钢琴卷帘图", "", "PNG图片 (*.png)")
    if not file_path:
        return
    if not file_path.lower().endswith('.png'):
        file_path += '.png'

    scene = graphics_view.scene()
    rect = scene.sceneRect()
    image = QImage(int(rect.width()), int(rect.height()), QImage.Format_ARGB32)
    image.fill(0xFFFFFFFF)
    painter = QPainter(image)
    scene.render(painter, QRect(0, 0, int(rect.width()), int(rect.height())), rect)
    painter.end()
    if image.save(file_path, "PNG"):
        QMessageBox.information(parent, "导出成功", f"完整图片已保存到:\n{file_path}", QMessageBox.StandardButton.Ok)
    else:
        QMessageBox.critical(parent, "导出失败", "保存完整图片时出错。", QMessageBox.StandardButton.Ok)

def preview_pianoroll_image(image_path):
    """
    调用系统图片查看器预览导出的钢琴卷帘图。
    """
    import os, sys, subprocess
    if not image_path or not os.path.exists(image_path):
        return
    if sys.platform.startswith('win'):
        os.startfile(image_path)
    elif sys.platform.startswith('darwin'):
        subprocess.call(['open', image_path])
    else:
        subprocess.call(['xdg-open', image_path])

def get_pianoroll_image_size(graphics_view):
    """
    获取当前钢琴卷帘图图片的像素尺寸。
    """
    if graphics_view is None:
        return None
    pixmap = graphics_view.grab()
    return pixmap.width(), pixmap.height()

def export_pianoroll_jpeg(parent, graphics_view):
    """
    导出钢琴卷帘图为JPEG图片。
    """
    if graphics_view is None:
        QMessageBox.warning(parent, "导出失败", "未找到钢琴卷帘图视图。", QMessageBox.StandardButton.Ok)
        return

    file_path, _ = QFileDialog.getSaveFileName(parent, "导出钢琴卷帘图", "", "JPEG图片 (*.jpg *.jpeg)")
    if not file_path:
        return
    if not (file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg')):
        file_path += '.jpg'

    pixmap = graphics_view.grab()
    if pixmap.save(file_path, "JPEG"):
        QMessageBox.information(parent, "导出成功", f"图片已保存到:\n{file_path}", QMessageBox.StandardButton.Ok)
    else:
        QMessageBox.critical(parent, "导出失败", "保存图片时出错。", QMessageBox.StandardButton.Ok)
"""截图工具 - 全屏遮罩 + 框选区域"""
import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QGuiApplication, QCursor


class ScreenshotOverlay(QWidget):
    """全屏半透明遮罩，用户拖拽选择截图区域"""

    captured = pyqtSignal(QPixmap, QRect)  # 截图结果 + 区域

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        self._origin = QPoint()
        self._current = QPoint()
        self._selecting = False
        self._full_screenshot = None

    def start(self):
        """开始截图：先截全屏（支持多显示器），然后显示遮罩"""
        # 计算所有屏幕的总区域
        screens = QGuiApplication.screens()
        if not screens:
            return

        # 合并所有屏幕的几何区域
        total = screens[0].geometry()
        for s in screens[1:]:
            total = total.united(s.geometry())

        # 截取整个虚拟桌面
        primary = QGuiApplication.primaryScreen()
        self._full_screenshot = primary.grabWindow(0, total.x(), total.y(), total.width(), total.height())
        self._offset = total.topLeft()  # 记录偏移量

        self.setGeometry(total)
        self.showFullScreen()
        self.activateWindow()

    def paintEvent(self, event):
        if self._full_screenshot is None:
            return

        p = QPainter(self)
        # 画全屏截图
        p.drawPixmap(0, 0, self._full_screenshot)
        # 暗色遮罩
        p.fillRect(self.rect(), QColor(0, 0, 0, 100))

        if self._selecting and not self._origin.isNull():
            rect = QRect(self._origin, self._current).normalized()
            if rect.width() > 2 and rect.height() > 2:
                # 选中区域显示原图（亮色）
                p.drawPixmap(rect, self._full_screenshot, rect)
                # 选框边框
                p.setPen(QPen(QColor(99, 102, 241), 2))
                p.drawRect(rect)

                # 尺寸提示
                size_text = f"{rect.width()} x {rect.height()}"
                p.setPen(QColor(255, 255, 255))
                p.drawText(rect.left(), rect.top() - 6, size_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.pos()
            self._current = event.pos()
            self._selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._selecting:
            self._selecting = False
            rect = QRect(self._origin, event.pos()).normalized()

            if rect.width() > 5 and rect.height() > 5 and self._full_screenshot:
                cropped = self._full_screenshot.copy(rect)
                self.hide()
                self.captured.emit(cropped, rect)
            else:
                self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()

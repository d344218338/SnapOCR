"""高亮工具 - 在截图上画框高亮，其余区域变暗"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QApplication,
    QFileDialog,
)
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QPixmap, QImage, QPainterPath, QCursor,
)


class HighlightCanvas(QWidget):
    """画布：在图片上画高亮框"""

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self._original = pixmap
        self._boxes = []          # 已完成的框 [QRect, ...]
        self._current_box = None  # 正在画的框
        self._origin = QPoint()
        self._drawing = False
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.setMinimumSize(200, 200)

    def set_pixmap(self, pixmap: QPixmap):
        self._original = pixmap
        self._boxes.clear()
        self.update()

    def paintEvent(self, event):
        if self._original is None:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 计算缩放，让图片适配画布
        scale = min(self.width() / self._original.width(),
                    self.height() / self._original.height())
        w = int(self._original.width() * scale)
        h = int(self._original.height() * scale)
        x0 = (self.width() - w) // 2
        y0 = (self.height() - h) // 2
        self._draw_rect = QRect(x0, y0, w, h)

        # 画原图
        p.drawPixmap(self._draw_rect, self._original)

        all_boxes = list(self._boxes)
        if self._current_box:
            all_boxes.append(self._current_box)

        if all_boxes:
            # 暗色遮罩覆盖整张图
            p.fillRect(self._draw_rect, QColor(0, 0, 0, 150))

            # 在高亮框位置恢复原图
            for box in all_boxes:
                img_box = self._widget_to_image_rect(box)
                if img_box.isValid():
                    dest = self._image_to_widget_rect(img_box)
                    p.drawPixmap(dest, self._original, img_box)

            # 画框边框
            p.setPen(QPen(QColor(99, 102, 241), 2, Qt.PenStyle.SolidLine))
            for box in all_boxes:
                p.drawRect(box.normalized())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.pos()
            self._drawing = True

    def mouseMoveEvent(self, event):
        if self._drawing:
            self._current_box = QRect(self._origin, event.pos()).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._drawing:
            self._drawing = False
            if self._current_box and self._current_box.width() > 3 and self._current_box.height() > 3:
                self._boxes.append(self._current_box)
            self._current_box = None
            self.update()

    def undo_last(self):
        """撤销最后一个框"""
        if self._boxes:
            self._boxes.pop()
            self.update()

    def clear_boxes(self):
        """清除所有框"""
        self._boxes.clear()
        self.update()

    def get_result_pixmap(self) -> QPixmap:
        """生成最终结果图：高亮区域正常，其余变暗"""
        if self._original is None:
            return QPixmap()

        result = self._original.copy()
        p = QPainter(result)

        if self._boxes:
            # 先画暗色遮罩
            p.fillRect(result.rect(), QColor(0, 0, 0, 150))

            # 在框位置恢复原图
            for box in self._boxes:
                img_box = self._widget_to_image_rect(box)
                if img_box.isValid():
                    p.drawPixmap(img_box, self._original, img_box)

            # 画框边框
            p.setPen(QPen(QColor(99, 102, 241), 3))
            for box in self._boxes:
                img_box = self._widget_to_image_rect(box)
                if img_box.isValid():
                    p.drawRect(img_box)

        p.end()
        return result

    def _widget_to_image_rect(self, widget_rect: QRect) -> QRect:
        """将画布坐标转为原图坐标"""
        if not hasattr(self, '_draw_rect') or self._draw_rect.width() == 0:
            return QRect()

        dr = self._draw_rect
        sx = self._original.width() / dr.width()
        sy = self._original.height() / dr.height()

        x = int((widget_rect.x() - dr.x()) * sx)
        y = int((widget_rect.y() - dr.y()) * sy)
        w = int(widget_rect.width() * sx)
        h = int(widget_rect.height() * sy)

        return QRect(x, y, w, h).normalized().intersected(self._original.rect())

    def _image_to_widget_rect(self, img_rect: QRect) -> QRect:
        """将原图坐标转为画布坐标"""
        if not hasattr(self, '_draw_rect') or self._original.width() == 0:
            return QRect()

        dr = self._draw_rect
        sx = dr.width() / self._original.width()
        sy = dr.height() / self._original.height()

        x = int(img_rect.x() * sx) + dr.x()
        y = int(img_rect.y() * sy) + dr.y()
        w = int(img_rect.width() * sx)
        h = int(img_rect.height() * sy)

        return QRect(x, y, w, h)


class HighlightWindow(QWidget):
    """高亮编辑窗口"""

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SnapOCR - 高亮标注")
        self.setMinimumSize(700, 500)
        self.setStyleSheet("""
            QWidget { background: #0f0f13; }
            QPushButton {
                background: #1e1e2a; color: #c0c0d0; border: 1px solid #2a2a35;
                border-radius: 8px; padding: 8px 20px; font-size: 13px;
            }
            QPushButton:hover { background: #2a2a38; border-color: #4a4a60; }
            QPushButton#primary {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6366f1,stop:1 #8b5cf6);
                color: white; border: none; font-weight: bold;
            }
            QLabel { color: #8888a0; font-size: 13px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        hint = QLabel("在图片上拖拽画框 → 框内正常显示，框外变暗，突出重点区域")
        layout.addWidget(hint)

        self.canvas = HighlightCanvas(pixmap)
        layout.addWidget(self.canvas, 1)

        btn_row = QHBoxLayout()
        btn_undo = QPushButton("撤销上一个框")
        btn_undo.clicked.connect(self.canvas.undo_last)
        btn_row.addWidget(btn_undo)

        btn_clear = QPushButton("清除所有框")
        btn_clear.clicked.connect(self.canvas.clear_boxes)
        btn_row.addWidget(btn_clear)

        btn_row.addStretch()

        btn_copy = QPushButton("复制结果到剪贴板")
        btn_copy.setObjectName("primary")
        btn_copy.clicked.connect(self._copy_result)
        btn_row.addWidget(btn_copy)

        btn_save = QPushButton("保存为图片")
        btn_save.clicked.connect(self._save_result)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

        # 窗口大小适配图片
        img_w = min(pixmap.width() + 40, 1200)
        img_h = min(pixmap.height() + 100, 800)
        self.resize(max(img_w, 700), max(img_h, 500))

    def _copy_result(self):
        result = self.canvas.get_result_pixmap()
        QApplication.clipboard().setPixmap(result)

    def _save_result(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存高亮图片", "", "PNG (*.png);;JPEG (*.jpg)")
        if path:
            result = self.canvas.get_result_pixmap()
            result.save(path)

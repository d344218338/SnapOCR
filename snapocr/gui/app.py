"""SnapOCR 主应用 - 截图OCR + 翻译 + 高亮"""
import sys
import os
import threading
from io import BytesIO

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QComboBox, QSystemTrayIcon,
    QMenu, QSplitter, QFrame, QFileDialog, QScrollArea,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QBuffer
from PyQt6.QtGui import (
    QIcon, QPixmap, QAction, QFont, QColor, QPainter, QPainterPath,
    QLinearGradient, QImage, QGuiApplication,
)

from snapocr.gui.screenshot import ScreenshotOverlay
from snapocr.gui.highlight import HighlightWindow


STYLE = """
* { font-family: "Microsoft YaHei", "Segoe UI", sans-serif; }
QMainWindow { background: #0f0f13; }
QLabel { color: #c0c0d0; }
QLabel#title { color: #fff; font-size: 20px; font-weight: bold; }
QLabel#subtitle { color: #6b6b80; font-size: 13px; }
QTextEdit {
    background: #1a1a24; color: #e0e0ee; border: 1px solid #2a2a35;
    border-radius: 10px; padding: 12px; font-size: 14px;
    selection-background-color: #6366f1;
}
QPushButton {
    background: #1e1e2a; color: #c0c0d0; border: 1px solid #2a2a35;
    border-radius: 8px; padding: 10px 20px; font-size: 13px;
}
QPushButton:hover { background: #2a2a38; border-color: #4a4a60; }
QPushButton#primary {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6366f1,stop:1 #8b5cf6);
    color: white; border: none; font-weight: bold;
}
QPushButton#primary:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #5558e6,stop:1 #7c4fe0);
}
QPushButton#danger {
    background: #3a1520; color: #ef4444; border: 1px solid #5a2030;
}
QComboBox {
    background: #1a1a24; color: #e0e0ee; border: 1px solid #2a2a35;
    border-radius: 8px; padding: 8px 14px; font-size: 13px;
}
QComboBox QAbstractItemView {
    background: #1a1a24; color: #e0e0ee; border: 1px solid #2a2a35;
    selection-background-color: #6366f1;
}
QScrollBar:vertical {
    background: transparent; width: 8px;
}
QScrollBar::handle:vertical {
    background: #2a2a35; border-radius: 4px; min-height: 40px;
}
"""


class Signals(QObject):
    ocr_done = pyqtSignal(str, list)     # text, items
    translate_done = pyqtSignal(str)
    status = pyqtSignal(str)
    error = pyqtSignal(str)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SnapOCR - 截图OCR工具")
        self.setMinimumSize(800, 560)
        self.resize(900, 620)

        self.signals = Signals()
        self._ocr_engine = None
        self._translator = None
        self._last_pixmap = None
        self._last_items = []

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # 顶部标题 + 按钮
        top = QHBoxLayout()
        title = QLabel("SnapOCR")
        title.setObjectName("title")
        top.addWidget(title)

        subtitle = QLabel("  免费截图OCR · 翻译 · 高亮标注")
        subtitle.setObjectName("subtitle")
        top.addWidget(subtitle)

        top.addStretch()

        self.btn_screenshot = QPushButton("截图识别  (F4)")
        self.btn_screenshot.setObjectName("primary")
        self.btn_screenshot.clicked.connect(self.start_screenshot)
        top.addWidget(self.btn_screenshot)

        self.btn_table = QPushButton("表格识别")
        self.btn_table.clicked.connect(self.start_table_ocr)
        top.addWidget(self.btn_table)

        self.btn_highlight = QPushButton("高亮标注")
        self.btn_highlight.clicked.connect(self.start_highlight)
        top.addWidget(self.btn_highlight)

        self.btn_file = QPushButton("从文件识别")
        self.btn_file.clicked.connect(self.ocr_from_file)
        top.addWidget(self.btn_file)

        layout.addLayout(top)

        # 中间：图片预览 + 文字结果
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：截图预览
        left_frame = QFrame()
        left_frame.setStyleSheet("QFrame { background: #16161d; border: 1px solid #2a2a35; border-radius: 10px; }")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(12, 12, 12, 12)

        self.preview_label = QLabel("截图预览\n\n按 F4 或点击「截图识别」开始")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("color: #55556a; font-size: 14px; border: none;")
        self.preview_label.setMinimumSize(300, 200)
        self.preview_label.setScaledContents(False)
        left_layout.addWidget(self.preview_label)

        splitter.addWidget(left_frame)

        # 右侧：OCR 结果
        right_frame = QFrame()
        right_frame.setStyleSheet("QFrame { background: #16161d; border: 1px solid #2a2a35; border-radius: 10px; }")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(12, 12, 12, 12)

        self.result_text = QTextEdit()
        self.result_text.setPlaceholderText("OCR 识别结果将显示在这里...")
        right_layout.addWidget(self.result_text)

        # 翻译区域
        translate_row = QHBoxLayout()
        translate_row.addWidget(QLabel("翻译为："))
        self.lang_combo = QComboBox()
        langs = [("English", "en"), ("中文", "zh"), ("日本語", "ja"),
                 ("한국어", "ko"), ("Français", "fr"), ("Deutsch", "de")]
        for name, code in langs:
            self.lang_combo.addItem(name, code)
        translate_row.addWidget(self.lang_combo)

        btn_translate = QPushButton("翻译")
        btn_translate.clicked.connect(self.translate_text)
        translate_row.addWidget(btn_translate)
        translate_row.addStretch()
        right_layout.addLayout(translate_row)

        self.translate_text_edit = QTextEdit()
        self.translate_text_edit.setPlaceholderText("翻译结果...")
        self.translate_text_edit.setMaximumHeight(150)
        right_layout.addWidget(self.translate_text_edit)

        splitter.addWidget(right_frame)
        splitter.setSizes([400, 500])
        layout.addWidget(splitter, 1)

        # 底部状态栏 + 操作按钮
        bottom = QHBoxLayout()

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #55556a; font-size: 12px;")
        bottom.addWidget(self.status_label)

        bottom.addStretch()

        btn_copy = QPushButton("复制文字")
        btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(self.result_text.toPlainText()))
        bottom.addWidget(btn_copy)

        btn_copy_img = QPushButton("复制截图")
        btn_copy_img.clicked.connect(self._copy_screenshot)
        bottom.addWidget(btn_copy_img)

        layout.addLayout(bottom)

        # 信号连接
        self.signals.ocr_done.connect(self._on_ocr_done)
        self.signals.translate_done.connect(self._on_translate_done)
        self.signals.status.connect(self._on_status)
        self.signals.error.connect(self._on_error)

        # 截图工具
        self.screenshot_overlay = ScreenshotOverlay()
        self.screenshot_overlay.captured.connect(self._on_screenshot)

        # 全局快捷键
        self._setup_hotkeys()

        # 高亮窗口
        self._highlight_window = None

    def _setup_hotkeys(self):
        try:
            from pynput import keyboard
            def on_press(key):
                try:
                    if key == keyboard.Key.f4:
                        QTimer.singleShot(0, self.start_screenshot)
                except Exception:
                    pass
            self._hotkey_listener = keyboard.Listener(on_press=on_press)
            self._hotkey_listener.daemon = True
            self._hotkey_listener.start()
        except Exception:
            pass

    def start_screenshot(self):
        """开始截图"""
        self.hide()
        QTimer.singleShot(200, self.screenshot_overlay.start)

    def _on_screenshot(self, pixmap: QPixmap, rect):
        """截图完成"""
        self._last_pixmap = pixmap
        self._update_preview(pixmap)
        self.show()
        self.raise_()

        # 后台 OCR
        self._run_ocr(pixmap)

    def _update_preview(self, pixmap: QPixmap):
        scaled = pixmap.scaled(
            self.preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    def _run_ocr(self, pixmap: QPixmap, table_mode=False):
        self.signals.status.emit("正在识别...")
        self.result_text.setPlainText("")

        def worker():
            try:
                if self._ocr_engine is None:
                    from snapocr.core.ocr_engine import OCREngine
                    self._ocr_engine = OCREngine()

                # QPixmap -> PIL Image
                img = self._qpixmap_to_pil(pixmap)

                if table_mode:
                    text = self._ocr_engine.recognize_table(img)
                    items = []
                else:
                    items = self._ocr_engine.recognize(img)
                    text = "\n".join(item["text"] for item in items)

                self.signals.ocr_done.emit(text, items)
            except Exception as e:
                self.signals.error.emit(str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _qpixmap_to_pil(self, pixmap: QPixmap):
        from PIL import Image
        buffer = QBuffer()
        buffer.open(QBuffer.OpenModeFlag.ReadWrite)
        pixmap.save(buffer, "PNG")
        data = buffer.data().data()
        buffer.close()
        return Image.open(BytesIO(data))

    def _on_ocr_done(self, text, items):
        self._last_items = items
        self.result_text.setPlainText(text)
        count = len(text.replace("\n", "").replace(" ", ""))
        self.signals.status.emit(f"识别完成 - {count} 字")

    def start_table_ocr(self):
        """表格识别模式"""
        if self._last_pixmap:
            self._run_ocr(self._last_pixmap, table_mode=True)
        else:
            self.signals.status.emit("请先截图")

    def start_highlight(self):
        """打开高亮标注窗口"""
        if self._last_pixmap:
            self._highlight_window = HighlightWindow(self._last_pixmap)
            self._highlight_window.show()
        else:
            self.signals.status.emit("请先截图")

    def ocr_from_file(self):
        """从文件识别"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "",
            "图片 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*)")
        if path:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self._last_pixmap = pixmap
                self._update_preview(pixmap)
                self._run_ocr(pixmap)

    def translate_text(self):
        """翻译识别结果"""
        text = self.result_text.toPlainText().strip()
        if not text:
            return

        target = self.lang_combo.currentData()
        self.signals.status.emit("正在翻译...")
        self.translate_text_edit.setPlainText("")

        def worker():
            try:
                if self._translator is None:
                    from snapocr.core.translator import Translator
                    self._translator = Translator()
                result = self._translator.translate(text, target)
                self.signals.translate_done.emit(result)
            except Exception as e:
                self.signals.error.emit(f"翻译失败: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def _on_translate_done(self, text):
        self.translate_text_edit.setPlainText(text)
        self.signals.status.emit("翻译完成")

    def _on_status(self, msg):
        self.status_label.setText(msg)

    def _on_error(self, msg):
        self.status_label.setText(f"出错: {msg}")
        self.status_label.setStyleSheet("color: #ef4444; font-size: 12px;")
        QTimer.singleShot(5000, lambda: self.status_label.setStyleSheet("color: #55556a; font-size: 12px;"))

    def _copy_screenshot(self):
        if self._last_pixmap:
            QApplication.clipboard().setPixmap(self._last_pixmap)

    def closeEvent(self, event):
        event.ignore()
        self.hide()


class SnapOCRApp:
    """主应用 - 系统托盘 + 全局快捷键"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName("SnapOCR")
        self.app.setStyleSheet(STYLE)

        self.window = MainWindow()
        self._create_tray()

    def _create_tray(self):
        self.tray = QSystemTrayIcon()

        px = QPixmap(32, 32)
        px.fill(QColor(0, 0, 0, 0))
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, 32, 32)
        grad.setColorAt(0, QColor(99, 102, 241))
        grad.setColorAt(1, QColor(139, 92, 246))
        path = QPainterPath()
        path.addRoundedRect(0, 0, 32, 32, 8, 8)
        p.fillPath(path, grad)
        p.setPen(QColor(255, 255, 255))
        p.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "S")
        p.end()
        self.tray.setIcon(QIcon(px))
        self.tray.setToolTip("SnapOCR - 截图OCR工具")

        self.tray.activated.connect(self._tray_activated)

        menu = QMenu()
        menu.setStyleSheet(
            "QMenu { background: #1e1e2a; color: #c0c0d0; border: 1px solid #2a2a35; padding: 4px; }"
            "QMenu::item { padding: 8px 20px; border-radius: 4px; }"
            "QMenu::item:selected { background: #6366f1; color: white; }"
        )

        act_show = QAction("打开主界面", menu)
        act_show.triggered.connect(self._show)
        menu.addAction(act_show)

        act_screenshot = QAction("截图识别  [F4]", menu)
        act_screenshot.triggered.connect(self.window.start_screenshot)
        menu.addAction(act_screenshot)

        act_highlight = QAction("高亮标注", menu)
        act_highlight.triggered.connect(self.window.start_highlight)
        menu.addAction(act_highlight)

        menu.addSeparator()

        act_quit = QAction("退出", menu)
        act_quit.triggered.connect(self._quit)
        menu.addAction(act_quit)

        self.tray.setContextMenu(menu)
        self.tray.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show()

    def _show(self):
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def _quit(self):
        self.tray.hide()
        self.app.quit()

    def run(self):
        self.window.show()
        self.tray.showMessage(
            "SnapOCR 已启动",
            "按 F4 截图识别，关闭窗口缩到托盘",
            QSystemTrayIcon.MessageIcon.Information, 2000,
        )
        return self.app.exec()


def run_gui():
    app = SnapOCRApp()
    sys.exit(app.run())


if __name__ == "__main__":
    run_gui()

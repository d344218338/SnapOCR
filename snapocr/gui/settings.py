"""设置对话框"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QCheckBox, QComboBox, QSpinBox,
    QPushButton, QFormLayout, QGroupBox, QColorDialog, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from snapocr.core.config import load_config, save_config, DEFAULT_CONFIG


DIALOG_STYLE = """
QDialog { background: #0f0f13; }
QTabWidget::pane { background: #16161d; border: 1px solid #2a2a35; border-radius: 8px; }
QTabBar::tab {
    background: #1a1a24; color: #8080a0; padding: 10px 24px;
    border: 1px solid #2a2a35; border-bottom: none;
    border-top-left-radius: 8px; border-top-right-radius: 8px;
    margin-right: 2px; font-size: 13px;
}
QTabBar::tab:selected { background: #16161d; color: #e0e0ee; border-bottom: 2px solid #6366f1; }
QTabBar::tab:hover { color: #c0c0d0; }
QGroupBox {
    color: #c0c0d0; font-size: 14px; font-weight: bold;
    border: 1px solid #2a2a35; border-radius: 8px;
    margin-top: 16px; padding: 16px 12px 12px 12px;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
QLabel { color: #c0c0d0; font-size: 13px; }
QLineEdit, QSpinBox {
    background: #1a1a24; color: #e0e0ee; border: 1px solid #2a2a35;
    border-radius: 6px; padding: 8px 12px; font-size: 13px;
}
QLineEdit:focus, QSpinBox:focus { border-color: #6366f1; }
QComboBox {
    background: #1a1a24; color: #e0e0ee; border: 1px solid #2a2a35;
    border-radius: 6px; padding: 8px 12px; font-size: 13px;
}
QComboBox QAbstractItemView {
    background: #1a1a24; color: #e0e0ee; selection-background-color: #6366f1;
}
QCheckBox { color: #c0c0d0; font-size: 13px; spacing: 8px; }
QCheckBox::indicator {
    width: 18px; height: 18px; border-radius: 4px;
    border: 1px solid #2a2a35; background: #1a1a24;
}
QCheckBox::indicator:checked { background: #6366f1; border-color: #6366f1; }
QPushButton {
    background: #1e1e2a; color: #c0c0d0; border: 1px solid #2a2a35;
    border-radius: 8px; padding: 10px 24px; font-size: 13px;
}
QPushButton:hover { background: #2a2a38; border-color: #4a4a60; }
QPushButton#save {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6366f1,stop:1 #8b5cf6);
    color: white; border: none; font-weight: bold;
}
QPushButton#save:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #5558e6,stop:1 #7c4fe0);
}
"""


class SettingsDialog(QDialog):
    """设置对话框"""

    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SnapOCR - 设置")
        self.setMinimumSize(560, 520)
        self.resize(600, 560)
        self.setStyleSheet(DIALOG_STYLE)

        self.config = load_config()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # 标题
        title = QLabel("设置")
        title.setStyleSheet("color: #fff; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # 选项卡
        tabs = QTabWidget()
        tabs.addTab(self._create_general_tab(), "通用")
        tabs.addTab(self._create_ocr_tab(), "OCR")
        tabs.addTab(self._create_translate_tab(), "翻译")
        tabs.addTab(self._create_highlight_tab(), "高亮")
        tabs.addTab(self._create_about_tab(), "关于")
        layout.addWidget(tabs, 1)

        # 底部按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_reset = QPushButton("恢复默认")
        btn_reset.clicked.connect(self._reset_defaults)
        btn_row.addWidget(btn_reset)

        btn_save = QPushButton("保存")
        btn_save.setObjectName("save")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)

        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        layout.addLayout(btn_row)

    # ── 通用设置 ──

    def _create_general_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)

        # 快捷键
        grp = QGroupBox("快捷键")
        form = QFormLayout()
        form.setSpacing(10)

        self.edit_hk_screenshot = QLineEdit(self.config["hotkey_screenshot"])
        self.edit_hk_screenshot.setPlaceholderText("例: f4")
        form.addRow("截图识别:", self.edit_hk_screenshot)

        self.edit_hk_table = QLineEdit(self.config["hotkey_table"])
        self.edit_hk_table.setPlaceholderText("例: f5")
        form.addRow("表格识别:", self.edit_hk_table)

        self.edit_hk_highlight = QLineEdit(self.config["hotkey_highlight"])
        self.edit_hk_highlight.setPlaceholderText("例: f6")
        form.addRow("高亮标注:", self.edit_hk_highlight)

        grp.setLayout(form)
        layout.addWidget(grp)

        # 行为
        grp2 = QGroupBox("行为")
        vbox = QVBoxLayout()
        vbox.setSpacing(10)

        self.chk_hide_window = QCheckBox("截图时隐藏主窗口")
        self.chk_hide_window.setChecked(self.config["capture_hide_window"])
        vbox.addWidget(self.chk_hide_window)

        self.chk_auto_copy = QCheckBox("识别后自动复制文字到剪贴板")
        self.chk_auto_copy.setChecked(self.config["auto_copy_text"])
        vbox.addWidget(self.chk_auto_copy)

        self.chk_auto_ocr = QCheckBox("截图后自动识别")
        self.chk_auto_ocr.setChecked(self.config["auto_ocr_on_capture"])
        vbox.addWidget(self.chk_auto_ocr)

        self.chk_tray = QCheckBox("显示系统托盘图标")
        self.chk_tray.setChecked(self.config["show_tray_icon"])
        vbox.addWidget(self.chk_tray)

        self.chk_minimize = QCheckBox("关闭窗口时最小化到托盘")
        self.chk_minimize.setChecked(self.config["minimize_to_tray"])
        vbox.addWidget(self.chk_minimize)

        grp2.setLayout(vbox)
        layout.addWidget(grp2)

        layout.addStretch()
        return w

    # ── OCR 设置 ──

    def _create_ocr_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)

        grp = QGroupBox("OCR 引擎")
        form = QFormLayout()
        form.setSpacing(10)

        self.combo_lang = QComboBox()
        langs = [
            ("中文", "ch"), ("英文", "en"), ("日语", "japan"),
            ("韩语", "korean"), ("拉丁语系", "latin"),
        ]
        for name, code in langs:
            self.combo_lang.addItem(name, code)
        idx = self.combo_lang.findData(self.config["ocr_language"])
        if idx >= 0:
            self.combo_lang.setCurrentIndex(idx)
        form.addRow("识别语言:", self.combo_lang)

        grp.setLayout(form)
        layout.addWidget(grp)

        # 说明
        note = QLabel(
            "OCR 引擎使用 RapidOCR (PaddleOCR ONNX)，完全本地运行，无需网络。\n"
            "中文模型同时支持中英文混合识别。"
        )
        note.setStyleSheet("color: #55556a; font-size: 12px; padding: 12px;")
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addStretch()
        return w

    # ── 翻译设置 ──

    def _create_translate_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)

        grp = QGroupBox("Ollama 翻译")
        form = QFormLayout()
        form.setSpacing(10)

        self.combo_target = QComboBox()
        targets = [
            ("English", "en"), ("中文", "zh"), ("日本語", "ja"),
            ("한국어", "ko"), ("Français", "fr"), ("Deutsch", "de"),
        ]
        for name, code in targets:
            self.combo_target.addItem(name, code)
        idx = self.combo_target.findData(self.config["translate_target"])
        if idx >= 0:
            self.combo_target.setCurrentIndex(idx)
        form.addRow("默认翻译目标:", self.combo_target)

        self.edit_model = QLineEdit(self.config["ollama_model"])
        self.edit_model.setPlaceholderText("例: gemma4:latest")
        form.addRow("Ollama 模型:", self.edit_model)

        self.edit_url = QLineEdit(self.config["ollama_url"])
        self.edit_url.setPlaceholderText("http://localhost:11434")
        form.addRow("Ollama 地址:", self.edit_url)

        grp.setLayout(form)
        layout.addWidget(grp)

        note = QLabel(
            "翻译功能需要本地运行 Ollama。\n"
            "如未安装 Ollama，翻译功能将不可用，其他功能不受影响。\n"
            "下载 Ollama: https://ollama.com"
        )
        note.setStyleSheet("color: #55556a; font-size: 12px; padding: 12px;")
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addStretch()
        return w

    # ── 高亮设置 ──

    def _create_highlight_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)

        grp = QGroupBox("高亮标注")
        form = QFormLayout()
        form.setSpacing(10)

        self.spin_opacity = QSpinBox()
        self.spin_opacity.setRange(0, 255)
        self.spin_opacity.setValue(self.config["highlight_dim_opacity"])
        self.spin_opacity.setSuffix("  (0=全透明, 255=全黑)")
        form.addRow("变暗程度:", self.spin_opacity)

        # 边框颜色选择
        color_row = QHBoxLayout()
        self._border_color = self.config["highlight_border_color"]
        self.btn_color = QPushButton()
        self.btn_color.setFixedSize(80, 32)
        self._update_color_btn()
        self.btn_color.clicked.connect(self._pick_color)
        color_row.addWidget(self.btn_color)
        self.lbl_color = QLabel(self._border_color)
        color_row.addWidget(self.lbl_color)
        color_row.addStretch()
        form.addRow("边框颜色:", color_row)

        self.spin_border = QSpinBox()
        self.spin_border.setRange(1, 10)
        self.spin_border.setValue(self.config["highlight_border_width"])
        self.spin_border.setSuffix(" px")
        form.addRow("边框宽度:", self.spin_border)

        grp.setLayout(form)
        layout.addWidget(grp)

        layout.addStretch()
        return w

    def _update_color_btn(self):
        self.btn_color.setStyleSheet(
            f"background: {self._border_color}; border: 1px solid #2a2a35; border-radius: 6px;"
        )

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._border_color), self, "选择边框颜色")
        if color.isValid():
            self._border_color = color.name()
            self._update_color_btn()
            self.lbl_color.setText(self._border_color)

    # ── 关于 ──

    def _create_about_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("SnapOCR")
        title.setStyleSheet("color: #fff; font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        ver = QLabel("v1.0.0")
        ver.setStyleSheet("color: #6366f1; font-size: 14px;")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ver)

        desc = QLabel(
            "免费截图OCR工具\n\n"
            "截图即识别，完全免费，无需登录，无需API密钥，本地离线可用。\n\n"
            "功能：截图识别 / 表格识别 / 翻译 / 高亮标注\n\n"
            "OCR 引擎: RapidOCR (PaddleOCR ONNX)\n"
            "翻译: Ollama 本地大模型\n"
            "界面: PyQt6\n\n"
            "GitHub: github.com/d344218338/SnapOCR"
        )
        desc.setStyleSheet("color: #8080a0; font-size: 13px; line-height: 1.6;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addStretch()
        return w

    # ── 保存 / 重置 ──

    def _collect_config(self) -> dict:
        return {
            "hotkey_screenshot": self.edit_hk_screenshot.text().strip() or "f4",
            "hotkey_table": self.edit_hk_table.text().strip() or "f5",
            "hotkey_highlight": self.edit_hk_highlight.text().strip() or "f6",
            "ocr_language": self.combo_lang.currentData(),
            "auto_copy_text": self.chk_auto_copy.isChecked(),
            "auto_ocr_on_capture": self.chk_auto_ocr.isChecked(),
            "translate_target": self.combo_target.currentData(),
            "ollama_model": self.edit_model.text().strip() or "gemma4:latest",
            "ollama_url": self.edit_url.text().strip() or "http://localhost:11434",
            "capture_hide_window": self.chk_hide_window.isChecked(),
            "capture_sound": self.config.get("capture_sound", False),
            "highlight_dim_opacity": self.spin_opacity.value(),
            "highlight_border_color": self._border_color,
            "highlight_border_width": self.spin_border.value(),
            "show_tray_icon": self.chk_tray.isChecked(),
            "minimize_to_tray": self.chk_minimize.isChecked(),
            "auto_start": self.config.get("auto_start", False),
        }

    def _save(self):
        self.config = self._collect_config()
        save_config(self.config)
        self.settings_changed.emit(self.config)
        self.accept()

    def _reset_defaults(self):
        self.config = DEFAULT_CONFIG.copy()
        # 刷新所有控件
        self.edit_hk_screenshot.setText(self.config["hotkey_screenshot"])
        self.edit_hk_table.setText(self.config["hotkey_table"])
        self.edit_hk_highlight.setText(self.config["hotkey_highlight"])
        idx = self.combo_lang.findData(self.config["ocr_language"])
        if idx >= 0:
            self.combo_lang.setCurrentIndex(idx)
        self.chk_auto_copy.setChecked(self.config["auto_copy_text"])
        self.chk_auto_ocr.setChecked(self.config["auto_ocr_on_capture"])
        self.chk_hide_window.setChecked(self.config["capture_hide_window"])
        self.chk_tray.setChecked(self.config["show_tray_icon"])
        self.chk_minimize.setChecked(self.config["minimize_to_tray"])
        idx = self.combo_target.findData(self.config["translate_target"])
        if idx >= 0:
            self.combo_target.setCurrentIndex(idx)
        self.edit_model.setText(self.config["ollama_model"])
        self.edit_url.setText(self.config["ollama_url"])
        self.spin_opacity.setValue(self.config["highlight_dim_opacity"])
        self._border_color = self.config["highlight_border_color"]
        self._update_color_btn()
        self.lbl_color.setText(self._border_color)
        self.spin_border.setValue(self.config["highlight_border_width"])

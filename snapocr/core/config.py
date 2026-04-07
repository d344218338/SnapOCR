"""配置管理"""
import json
import os
from pathlib import Path

APP_NAME = "SnapOCR"
APP_DIR = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
APP_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = APP_DIR / "config.json"

DEFAULT_CONFIG = {
    # 快捷键
    "hotkey_screenshot": "f4",
    "hotkey_table": "f5",
    "hotkey_highlight": "f6",
    # OCR
    "ocr_language": "ch",          # ch, en, japan, korean, latin
    "auto_copy_text": True,        # 识别后自动复制文字到剪贴板
    "auto_ocr_on_capture": True,   # 截图后自动识别
    # 翻译
    "translate_target": "en",
    "ollama_model": "gemma4:latest",
    "ollama_url": "http://localhost:11434",
    # 截图
    "capture_hide_window": True,   # 截图时隐藏主窗口
    "capture_sound": False,        # 截图音效
    # 高亮
    "highlight_dim_opacity": 150,  # 变暗程度 0-255
    "highlight_border_color": "#6366f1",
    "highlight_border_width": 3,
    # 界面
    "show_tray_icon": True,
    "minimize_to_tray": True,      # 关闭窗口时最小化到托盘
    "auto_start": False,           # 开机自启
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            return {**DEFAULT_CONFIG, **saved}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

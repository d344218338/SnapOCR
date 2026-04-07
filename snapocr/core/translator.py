"""翻译模块 - Ollama 本地翻译"""
import json
import urllib.request


class Translator:
    """通过 Ollama 翻译文本"""

    LANG_NAMES = {
        "zh": "中文", "en": "English", "ja": "日本語", "ko": "한국어",
        "fr": "Français", "de": "Deutsch", "es": "Español",
        "ru": "Русский", "pt": "Português",
    }

    def __init__(self, model: str = "gemma4:latest", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def translate(self, text: str, target_lang: str = "en") -> str:
        target_name = self.LANG_NAMES.get(target_lang, target_lang)

        messages = [
            {"role": "system", "content": f"将文本翻译为{target_name}。只输出翻译结果，不加解释，不用markdown。"},
            {"role": "user", "content": text},
        ]

        data = json.dumps({
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.3, "num_predict": max(len(text) * 3, 200)},
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                parts = []
                for line in resp:
                    chunk = json.loads(line)
                    if "message" in chunk:
                        parts.append(chunk["message"].get("content", ""))
                return "".join(parts).strip()
        except Exception as e:
            return f"[翻译失败: {e}]"

"""OCR 引擎 - 多后端支持"""
import io
import numpy as np
from PIL import Image


class OCREngine:
    """OCR 识别引擎 - 本地 RapidOCR 为主"""

    def __init__(self, lang: str = "ch"):
        self._engine = None
        self._lang = lang

    def _ensure_engine(self):
        if self._engine is None:
            from rapidocr_onnxruntime import RapidOCR
            self._engine = RapidOCR()

    def recognize(self, image) -> list[dict]:
        """
        识别图片中的文字。
        image: PIL.Image, numpy array, 或文件路径
        返回: [{"text": "...", "box": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]], "score": 0.99}, ...]
        """
        self._ensure_engine()

        if isinstance(image, str):
            img = np.array(Image.open(image))
        elif isinstance(image, Image.Image):
            img = np.array(image)
        elif isinstance(image, bytes):
            img = np.array(Image.open(io.BytesIO(image)))
        else:
            img = image

        result, elapse = self._engine(img)

        if not result:
            return []

        items = []
        for box, text, score in result:
            items.append({
                "text": text,
                "box": box,
                "score": score,
            })
        return items

    def recognize_text(self, image) -> str:
        """识别并返回纯文本"""
        items = self.recognize(image)
        return "\n".join(item["text"] for item in items)

    def recognize_table(self, image) -> str:
        """识别表格并返回 markdown 格式"""
        items = self.recognize(image)
        if not items:
            return ""

        # 按 y 坐标分行
        rows = self._group_into_rows(items)

        if len(rows) <= 1:
            return "\n".join(item["text"] for item in items)

        # 按 x 坐标分列
        cols = self._detect_columns(items)
        if cols <= 1:
            return "\n".join(r[0]["text"] if r else "" for r in rows)

        # 构建 markdown 表格
        table_rows = []
        for row_items in rows:
            cells = self._assign_to_columns(row_items, cols)
            table_rows.append("| " + " | ".join(cells) + " |")

        if len(table_rows) >= 2:
            header = table_rows[0]
            sep = "| " + " | ".join(["---"] * cols) + " |"
            body = "\n".join(table_rows[1:])
            return f"{header}\n{sep}\n{body}"

        return "\n".join(table_rows)

    def _group_into_rows(self, items: list[dict], threshold=15) -> list[list[dict]]:
        """按 y 坐标将文字分组到同一行"""
        if not items:
            return []

        sorted_items = sorted(items, key=lambda x: min(p[1] for p in x["box"]))
        rows = []
        current_row = [sorted_items[0]]
        current_y = min(p[1] for p in sorted_items[0]["box"])

        for item in sorted_items[1:]:
            y = min(p[1] for p in item["box"])
            if abs(y - current_y) < threshold:
                current_row.append(item)
            else:
                rows.append(sorted(current_row, key=lambda x: min(p[0] for p in x["box"])))
                current_row = [item]
                current_y = y

        if current_row:
            rows.append(sorted(current_row, key=lambda x: min(p[0] for p in x["box"])))

        return rows

    def _detect_columns(self, items: list[dict]) -> int:
        """检测列数"""
        rows = self._group_into_rows(items)
        if not rows:
            return 1
        col_counts = [len(row) for row in rows]
        from collections import Counter
        most_common = Counter(col_counts).most_common(1)
        return most_common[0][0] if most_common else 1

    def _assign_to_columns(self, row_items: list[dict], num_cols: int) -> list[str]:
        """将一行中的文字分配到对应列"""
        if not row_items:
            return [""] * num_cols

        sorted_items = sorted(row_items, key=lambda x: min(p[0] for p in x["box"]))

        if len(sorted_items) >= num_cols:
            cells = [item["text"] for item in sorted_items[:num_cols]]
            for item in sorted_items[num_cols:]:
                cells[-1] += " " + item["text"]
        else:
            cells = [item["text"] for item in sorted_items]
            cells.extend([""] * (num_cols - len(cells)))

        return cells

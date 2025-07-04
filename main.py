import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel
)
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPalette, QColor, QCursor, QPainter, QPen

def google_translate(text):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": "zh-CN",
        "dt": "t",
        "q": text,
    }
    resp = requests.get(url, params=params)
    resp.encoding = 'utf-8'
    try:
        arr = resp.json()
        return arr[0][0][0]
    except Exception:
        return "翻译失败"

class SubtitleOverlay(QWidget):
    MARGIN = 6  # 边框拉伸敏感区宽度

    def __init__(self):
        super().__init__()
        self.setWindowTitle("字幕遮挡工具")
        self.resize(500, 100)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.FramelessWindowHint)

        # 不透明黑色背景
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.Window, QColor(0, 0, 0))
        self.setPalette(pal)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)

        # 输入框，直接填写占位提示
        self.input = QLineEdit()
        self.input.setPlaceholderText(
            "字幕遮挡区域（窗口可拖动、可拉伸置于视频字幕上方、点击ESC退出、点击Enter送出代翻译内容）"
        )
        layout.addWidget(self.input)

        # 按回车自动翻译
        self.input.returnPressed.connect(self.translate)

        self.translate_button = QPushButton("Google翻译")
        self.translate_button.clicked.connect(self.translate)
        layout.addWidget(self.translate_button)

        self.output = QLabel("")
        self.output.setStyleSheet("color: lightgreen; font-weight: bold;")
        layout.addWidget(self.output)

        # 拖拽/拉伸相关
        self._drag_pos = None
        self._resize_dir = None

    def paintEvent(self, event):
        super().paintEvent(event)
        # 画2像素外灰内白边框
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        # 外灰
        pen1 = QPen(QColor(180, 180, 180), 2)
        pen1.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen1)
        painter.drawRect(self.rect().adjusted(1, 1, -2, -2))
        # 内白
        pen2 = QPen(QColor(255, 255, 255), 1)
        pen2.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen2)
        painter.drawRect(self.rect().adjusted(3, 3, -4, -4))

    def translate(self):
        txt = self.input.text().strip()
        if not txt:
            self.output.setText("请输入需要翻译的内容")
            return
        self.output.setText("翻译中...")
        QApplication.processEvents()
        try:
            trans = google_translate(txt)
            self.output.setText(trans)
        except Exception:
            self.output.setText("翻译失败")

    # === 无痕窗体的移动与拉伸 ===
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            self._resize_dir = self._get_resize_dir(pos)
            if not self._resize_dir:
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        if self._resize_dir:
            self._do_resize(event.globalPos())
        elif self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
        else:
            self._update_cursor(pos)
        event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._resize_dir = None
        self._update_cursor(event.pos())
        super().mouseReleaseEvent(event)

    def _get_resize_dir(self, pos):
        rect = self.rect()
        x, y, w, h = pos.x(), pos.y(), rect.width(), rect.height()
        margins = self.MARGIN

        left = x <= margins
        right = x >= w - margins
        top = y <= margins
        bottom = y >= h - margins
        # 四个角
        if left and top:
            return "top_left"
        if right and top:
            return "top_right"
        if left and bottom:
            return "bottom_left"
        if right and bottom:
            return "bottom_right"
        # 四条边
        if top:
            return "top"
        if left:
            return "left"
        if right:
            return "right"
        if bottom:
            return "bottom"
        return None

    def _do_resize(self, global_pos):
        rect = self.geometry()
        min_width, min_height = 300, 80
        if self._resize_dir == "left":
            diff = global_pos.x() - rect.left()
            new_w = rect.width() - diff
            if new_w >= min_width:
                rect.setLeft(rect.left() + diff)
        elif self._resize_dir == "right":
            diff = global_pos.x() - rect.right()
            new_w = rect.width() + diff
            if new_w >= min_width:
                rect.setRight(rect.right() + diff)
        elif self._resize_dir == "top":
            diff = global_pos.y() - rect.top()
            new_h = rect.height() - diff
            if new_h >= min_height:
                rect.setTop(rect.top() + diff)
        elif self._resize_dir == "bottom":
            diff = global_pos.y() - rect.bottom()
            new_h = rect.height() + diff
            if new_h >= min_height:
                rect.setBottom(rect.bottom() + diff)
        elif self._resize_dir == "top_left":
            diff_x = global_pos.x() - rect.left()
            diff_y = global_pos.y() - rect.top()
            new_w = rect.width() - diff_x
            new_h = rect.height() - diff_y
            if new_w >= min_width:
                rect.setLeft(rect.left() + diff_x)
            if new_h >= min_height:
                rect.setTop(rect.top() + diff_y)
        elif self._resize_dir == "top_right":
            diff_x = global_pos.x() - rect.right()
            diff_y = global_pos.y() - rect.top()
            new_w = rect.width() + diff_x
            new_h = rect.height() - diff_y
            if new_w >= min_width:
                rect.setRight(rect.right() + diff_x)
            if new_h >= min_height:
                rect.setTop(rect.top() + diff_y)
        elif self._resize_dir == "bottom_left":
            diff_x = global_pos.x() - rect.left()
            diff_y = global_pos.y() - rect.bottom()
            new_w = rect.width() - diff_x
            new_h = rect.height() + diff_y
            if new_w >= min_width:
                rect.setLeft(rect.left() + diff_x)
            if new_h >= min_height:
                rect.setBottom(rect.bottom() + diff_y)
        elif self._resize_dir == "bottom_right":
            diff_x = global_pos.x() - rect.right()
            diff_y = global_pos.y() - rect.bottom()
            new_w = rect.width() + diff_x
            new_h = rect.height() + diff_y
            if new_w >= min_width:
                rect.setRight(rect.right() + diff_x)
            if new_h >= min_height:
                rect.setBottom(rect.bottom() + diff_y)
        self.setGeometry(rect)

    def _update_cursor(self, pos):
        cursor = Qt.ArrowCursor
        dir_ = self._get_resize_dir(pos)
        if dir_ in ["left", "right"]:
            cursor = Qt.SizeHorCursor
        elif dir_ in ["top", "bottom"]:
            cursor = Qt.SizeVerCursor
        elif dir_ in ["top_left", "bottom_right"]:
            cursor = Qt.SizeFDiagCursor
        elif dir_ in ["top_right", "bottom_left"]:
            cursor = Qt.SizeBDiagCursor
        self.setCursor(cursor)

    # 允许ESC键关闭窗口
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = SubtitleOverlay()
    win.show()
    sys.exit(app.exec_())